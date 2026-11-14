from typing import Never

import pytest
from hypothesis import given
from hypothesis import strategies as st
from twisted.internet.defer import CancelledError, Deferred
from twisted.internet.task import Clock
from twisted.python.failure import Failure

from minerva.qan import (
    Cancellation,
    InvalidQANFrame,
    KnownError,
    KnownErrorAnswer,
    Notification,
    OkayAnswer,
    QANFrame,
    QANHelper,
    Question,
    QuestionFailed,
    UnknownError,
    UnknownErrorAnswer,
    qan_frame_to_string,
    string_to_qan_frame,
)
from tests.helpers import ListLog, failure_result_of, success_result_of


def unused(*args: object) -> Never:
    raise AssertionError(f"unexpected call with {args!r}")


class TestQANFrames:
    def test_equality(self) -> None:
        assert OkayAnswer("blah", 10) == OkayAnswer("blah", 10)
        assert OkayAnswer("blah", 11) != OkayAnswer("blah", 10)
        assert OkayAnswer("blahx", 10) != OkayAnswer("blah", 10)

    def test_different_types_unequal(self) -> None:
        assert OkayAnswer("blah", 10) != Question("blah", 10)
        assert OkayAnswer("blah", 10) != KnownErrorAnswer("blah", 10)
        assert Question("blah", 10) != KnownErrorAnswer("blah", 10)

    @pytest.mark.parametrize(
        ("frame", "encoded"),
        [
            (Notification("blah"), "blah#"),
            (Question("blah", 0), "blah|0Q"),
            (Question("blah", 100), "blah|100Q"),
            (OkayAnswer("blah", 100), "blah|100K"),
            (KnownErrorAnswer("blah", 100), "blah|100E"),
            (UnknownErrorAnswer("blah", 100), "blah|100U"),
            (Cancellation(100), "100C"),
        ],
    )
    def test_encode_decode(self, frame: QANFrame, encoded: str) -> None:
        assert qan_frame_to_string(frame) == encoded
        assert string_to_qan_frame(encoded) == frame

    @pytest.mark.parametrize("bad", [None, True, b"blah", 3, 3.0, (), [], {}, object()])
    def test_encode_non_str_body(self, bad: object) -> None:
        with pytest.raises(TypeError):
            qan_frame_to_string(Notification(bad))  # ty: ignore[invalid-argument-type]

    @pytest.mark.parametrize(
        "s", ["", "whatX", "blah|10X", "1x0C", "C", "blah|1x0Q", "Q", "blah10Q", "-1C"]
    )
    def test_decode_invalid(self, s: str) -> None:
        with pytest.raises(InvalidQANFrame):
            string_to_qan_frame(s)

    @given(
        st.one_of(
            st.builds(Question, st.text(), st.integers(0, 2**53)),
            st.builds(OkayAnswer, st.text(), st.integers(0, 2**53)),
            st.builds(KnownErrorAnswer, st.text(), st.integers(0, 2**53)),
            st.builds(UnknownErrorAnswer, st.text(), st.integers(0, 2**53)),
            st.builds(Cancellation, st.integers(0, 2**53)),
            st.builds(Notification, st.text()),
        )
    )
    def test_roundtrip(self, frame: QANFrame) -> None:
        """
        Bodies may contain anything, including "|" and type characters.
        """
        assert string_to_qan_frame(qan_frame_to_string(frame)) == frame

    @given(st.text())
    def test_decoding_only_raises_invalid_qan_frame(self, s: str) -> None:
        try:
            frame = string_to_qan_frame(s)
        except InvalidQANFrame:
            return
        assert qan_frame_to_string(frame) == s


class TestQANHelper:
    def test_repr(self) -> None:
        h = QANHelper(unused, unused, lambda _: None, unused)
        assert repr(h) == (
            "<QANHelper asked 0 questions, waiting for 0 peer answers "
            "and 0 local answers>"
        )
        h.ask("what?")
        assert repr(h) == (
            "<QANHelper asked 1 questions, waiting for 1 peer answers "
            "and 0 local answers>"
        )

    def test_ask(self) -> None:
        sent: ListLog[QANFrame] = ListLog()
        fatal_errors: ListLog[str] = ListLog()
        h = QANHelper(unused, unused, sent.append, fatal_errors.append)

        d1 = h.ask("what?")
        assert sent.get_new() == [Question("what?", 1)]
        assert not d1.called

        # An answer with a wrong qid is a fatal error.
        h.handle_qan_frame(OkayAnswer("answer with wrong qid", 100))
        assert fatal_errors.get_new() == ["Received an answer with invalid qid: 100"]

        h.handle_qan_frame(OkayAnswer("no.", 1))
        assert success_result_of(d1) == "no."

        d2 = h.ask("I want a KnownError response to this one")
        h.handle_qan_frame(KnownErrorAnswer("KnownErrorAnswer as asked", 2))
        assert failure_result_of(d2, KnownError).body == "KnownErrorAnswer as asked"

        d3 = h.ask("I want an UnknownError response to this one")
        h.handle_qan_frame(UnknownErrorAnswer("UnknownErrorAnswer as asked", 3))
        assert failure_result_of(d3, UnknownError).body == "UnknownErrorAnswer as asked"

    def test_notify(self) -> None:
        sent: list[QANFrame] = []
        h = QANHelper(unused, unused, sent.append, unused)
        h.notify("you've got mail")
        assert sent == [Notification("you've got mail")]

    def test_notification_received(self) -> None:
        received: list[tuple[str, bool]] = []
        h = QANHelper(lambda *args: received.append(args), unused, unused, unused)
        h.handle_qan_frame(Notification("poke"))
        h.handle_qan_frame(Notification("and again"))
        assert received == [("poke", False), ("and again", False)]

    def test_question_received(self) -> None:
        received: list[tuple[str, bool]] = []

        def body_received(body: str, is_question: bool) -> str:
            received.append((body, is_question))
            return "chilly"

        sent: list[QANFrame] = []
        h = QANHelper(body_received, unused, sent.append, unused)
        h.handle_qan_frame(Question("the weather?", 1))
        h.handle_qan_frame(Question("how about now?", 2))
        assert received == [("the weather?", True), ("how about now?", True)]
        assert sent == [OkayAnswer("chilly", 1), OkayAnswer("chilly", 2)]

    def test_question_received_async(self) -> None:
        answers: list[Deferred[str]] = [Deferred(), Deferred(), Deferred()]
        d1, d2, d3 = answers
        sent: list[QANFrame] = []
        h = QANHelper(
            lambda body, is_question: answers.pop(0), unused, sent.append, unused
        )
        h.handle_qan_frame(Question("the weather?", 1))
        h.handle_qan_frame(Question("how about now?", 2))
        h.handle_qan_frame(Question("and now?", 3))
        assert sent == []

        d2.callback("rainy")
        d1.callback("hurricane")
        d3.errback(KnownError("weather station is broken"))
        assert sent == [
            OkayAnswer("rainy", 2),
            OkayAnswer("hurricane", 1),
            KnownErrorAnswer("weather station is broken", 3),
        ]

    def test_question_answered_by_coroutine(self) -> None:
        """
        `body_received` may be an `async def`.
        """
        clock = Clock()

        async def body_received(body: str, is_question: bool) -> str:
            d: Deferred[None] = Deferred()
            clock.callLater(1.0, d.callback, None)
            await d
            if body == "fail":
                raise KnownError("as requested")
            return body.upper()

        sent: list[QANFrame] = []
        h = QANHelper(body_received, unused, sent.append, unused)
        h.handle_qan_frame(Question("shout", 1))
        h.handle_qan_frame(Question("fail", 2))
        assert sent == []
        clock.advance(1.0)
        assert sent == [OkayAnswer("SHOUT", 1), KnownErrorAnswer("as requested", 2)]

    def test_notification_handled_by_coroutine(self) -> None:
        clock = Clock()
        received: list[str] = []

        async def body_received(body: str, is_question: bool) -> None:
            d: Deferred[None] = Deferred()
            clock.callLater(1.0, d.callback, None)
            await d
            received.append(body)

        h = QANHelper(body_received, unused, unused, unused)
        h.handle_qan_frame(Notification("poke"))
        clock.advance(1.0)
        assert received == ["poke"]

    def test_answer_not_a_str(self) -> None:
        """
        If the answer isn't a `str`, the error is logged and the peer gets an
        UnknownErrorAnswer, rather than no answer at all.
        """
        logged: list[tuple[str, Failure]] = []
        sent: list[QANFrame] = []
        h = QANHelper(
            lambda body, is_question: None,
            lambda *a: logged.append(a),
            sent.append,
            unused,
        )
        h.handle_qan_frame(Question("forgot to return?", 1))
        [(message, failure)] = logged
        assert message == "The answer to peer's Question #1 is not a str"
        assert failure.check(TypeError)
        assert sent == [UnknownErrorAnswer("Uncaught exception", 1)]

    def test_question_received_duplicate_qid(self) -> None:
        received: list[str] = []

        def body_received(body: str, is_question: bool) -> Deferred[str]:
            received.append(body)
            return Deferred()

        fatal_errors: list[str] = []
        h = QANHelper(body_received, unused, unused, fatal_errors.append)
        h.handle_qan_frame(Question("what?", 1))
        h.handle_qan_frame(Question("where?", 1))
        assert received == ["what?"]
        assert fatal_errors == ["Received Question with duplicate qid: 1"]

    def test_they_cancel(self) -> None:
        canceller_calls: list[str] = []

        def canceller_does_errback(d: Deferred[str]) -> None:
            canceller_calls.append("errback")
            d.errback(KnownError("okay, you'll never know"))

        def canceller_does_callback(d: Deferred[str]) -> None:
            canceller_calls.append("callback")
            d.callback("maybe a little warm")

        answers: list[Deferred[str]] = [
            Deferred(),
            Deferred(canceller_does_errback),
            Deferred(),
            Deferred(canceller_does_callback),
        ]
        _, _, d3, _ = answers
        sent: ListLog[QANFrame] = ListLog()
        h = QANHelper(
            lambda body, is_question: answers.pop(0), unused, sent.append, unused
        )
        for qid in (1, 2, 3, 4):
            h.handle_qan_frame(Question(f"question {qid}", qid))
        assert sent.get_new() == []
        assert canceller_calls == []

        h.handle_qan_frame(Cancellation(2))
        assert canceller_calls == ["errback"]
        assert sent.get_new() == [KnownErrorAnswer("okay, you'll never know", 2)]

        h.handle_qan_frame(Cancellation(4))
        assert canceller_calls == ["errback", "callback"]
        assert sent.get_new() == [OkayAnswer("maybe a little warm", 4)]

        # Question #1 has no canceller.
        h.handle_qan_frame(Cancellation(1))
        assert sent.get_new() == [UnknownErrorAnswer("CancelledError", 1)]

        d3.errback(KnownError("weather station is broken"))
        assert sent.get_new() == [KnownErrorAnswer("weather station is broken", 3)]

    def test_question_causes_exception(self) -> None:
        """
        If answering a Question raises an exception, it is logged, and the
        peer gets an uninformative UnknownErrorAnswer.
        """
        logged: list[tuple[str, Failure]] = []

        def body_received(body: str, is_question: bool) -> Never:
            raise ValueError("body_received did something wrong")

        sent: list[QANFrame] = []
        h = QANHelper(
            body_received, lambda *args: logged.append(args), sent.append, unused
        )
        h.handle_qan_frame(Question("How much wood would a wood chuck chuck?", 1))

        [(message, failure)] = logged
        assert message == "Peer's Question #1 caused uncaught exception"
        assert failure.check(ValueError)
        assert sent == [UnknownErrorAnswer("Uncaught exception", 1)]

    def test_notification_causes_exception(self) -> None:
        """
        If handling a Notification raises an exception, it is logged, and
        nothing is sent to the peer.
        """
        logged: list[tuple[str, Failure]] = []

        def body_received(body: str, is_question: bool) -> Never:
            raise ValueError("body_received did something wrong")

        sent: list[QANFrame] = []
        h = QANHelper(
            body_received, lambda *args: logged.append(args), sent.append, unused
        )
        h.handle_qan_frame(Notification("You've got more mail"))

        [(message, failure)] = logged
        assert message == "Peer's Notification caused uncaught exception"
        assert failure.check(ValueError)
        assert sent == []

    def test_they_cancel_nonexistent_question(self) -> None:
        h = QANHelper(unused, unused, unused, unused)
        # Cancelling a nonexistent Question is not an error.
        h.handle_qan_frame(Cancellation(1))
        h.handle_qan_frame(Cancellation(1))
        h.handle_qan_frame(Cancellation(2))

    def test_we_cancel(self) -> None:
        sent: ListLog[QANFrame] = ListLog()
        h = QANHelper(unused, unused, sent.append, unused)
        d = h.ask("going to the theater?")
        assert sent.get_new() == [Question("going to the theater?", 1)]

        d.cancel()
        assert sent.get_new() == [Cancellation(1)]
        failure_result_of(d, CancelledError)

        # The peer always sends an answer, which QANHelper must ignore.
        h.handle_qan_frame(OkayAnswer("nope", 1))

    def test_fail_all(self) -> None:
        sent: ListLog[QANFrame] = ListLog()
        h = QANHelper(unused, unused, sent.append, unused)
        d1 = h.ask("going to the theater?")
        d2 = h.ask("mu?")
        assert sent.get_new() == [
            Question("going to the theater?", 1),
            Question("mu?", 2),
        ]

        h.fail_all("just because")
        assert str(failure_result_of(d1, QuestionFailed)) == "just because"
        assert str(failure_result_of(d2, QuestionFailed)) == "just because"

        # The peer can still answer the failed Questions.
        h.handle_qan_frame(OkayAnswer("no", 1))
        h.handle_qan_frame(KnownErrorAnswer("what?", 2))

    def test_fail_all_when_an_errback_cancels_another_question(self) -> None:
        """
        `fail_all` doesn't errback a question a second time, if the errback of
        an earlier question cancelled it meanwhile.
        """
        h = QANHelper(unused, unused, lambda _: None, unused)
        d1 = h.ask("one")
        d2 = h.ask("two")
        d1.addErrback(lambda _: d2.cancel())
        h.fail_all("gone")
        failure_result_of(d2, CancelledError)

    def test_cancel_peer_questions_survives_a_raising_canceller(self) -> None:
        """
        A canceller that raises is logged, and the other answers are still
        cancelled.
        """

        def bad_canceller(d: Deferred[str]) -> None:
            raise ZeroDivisionError

        answers: list[Deferred[str]] = [Deferred(bad_canceller), Deferred()]
        errors: ListLog[tuple[str, Failure]] = ListLog()
        h = QANHelper(
            lambda body, is_question: answers.pop(0),
            lambda message, failure: errors.append((message, failure)),
            lambda _: None,
            unused,
        )
        h.handle_qan_frame(Question("first", 1))
        h.handle_qan_frame(Question("second", 2))
        h.cancel_peer_questions()

        [(message, failure)] = errors.get_new()
        assert message == "Cancelling the answer to peer's Question #1 raised"
        assert failure.check(ZeroDivisionError)
        # Only the answer to the first question is still pending.
        assert "and 1 local answers" in repr(h)

    def test_fail_all_after_cancel_and_twice(self) -> None:
        """
        `fail_all` skips questions that were already given up on.  (The
        Python 2 version called `.errback` on `None` here.)
        """
        h = QANHelper(unused, unused, lambda _: None, unused)
        d1 = h.ask("one")
        d2 = h.ask("two")
        d1.cancel()
        h.fail_all("first")
        h.fail_all("second")
        failure_result_of(d1, CancelledError)
        assert str(failure_result_of(d2, QuestionFailed)) == "first"
