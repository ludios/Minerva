"""
Tests for `minerva.protocols`: `SubprotocolFactory` and `QANProtocolWrapper`.
"""

import logging
from typing import Any

import pytest
from twisted.internet.defer import CancelledError, Deferred
from twisted.internet.task import Clock

from minerva.protocols import QANProtocolWrapper, SubprotocolFactory
from minerva.qan import (
    KnownError,
    KnownErrorAnswer,
    Notification,
    OkayAnswer,
    QANHelper,
    Question,
    QuestionFailed,
    UnknownErrorAnswer,
    qan_frame_to_string,
    string_to_qan_frame,
)
from minerva.stream import ServerStream
from tests.helpers import ListLog, failure_result_of
from tests.mocks import DummySocketLikeTransport, MockStringFactory


def start_stream(
    clock: Clock, factory: Any
) -> tuple[ServerStream, DummySocketLikeTransport]:
    stream = ServerStream(clock, "a stream id of unusual length", factory)
    transport = DummySocketLikeTransport()
    stream.transport_online(transport, True, None)
    return stream, transport


def sent(stream: ServerStream) -> list[str]:
    return [s for _, s in stream.queue.iter_items()]


@pytest.fixture
def clock() -> Clock:
    return Clock()


class TestSubprotocolFactory:
    @pytest.fixture
    def echo_factory(self) -> MockStringFactory:
        return MockStringFactory()

    @pytest.fixture
    def started(
        self, clock: Clock, echo_factory: MockStringFactory
    ) -> tuple[ServerStream, DummySocketLikeTransport]:
        return start_stream(clock, SubprotocolFactory({"echo": echo_factory}))

    def test_subprotocol(
        self,
        started: tuple[ServerStream, DummySocketLikeTransport],
        echo_factory: MockStringFactory,
    ) -> None:
        stream, transport = started
        stream.strings_received(transport, [(0, "subprotocol:echo")])
        assert echo_factory.instance.get_new() == [["stream_started", stream]]

        stream.strings_received(transport, [(1, "hello"), (2, "subprotocol:echo")])
        assert echo_factory.instance.get_new() == [
            ["string_received", "hello"],
            ["string_received", "subprotocol:echo"],
        ]

        stream.reset("bye")
        assert echo_factory.instance.get_new() == [["stream_reset", "bye", True]]

    @pytest.mark.parametrize(
        ("first_string", "reason"),
        [
            ("hello", "no subprotocol; send a subprotocol:... string first"),
            ("subprotocol:nope", "unknown subprotocol"),
        ],
    )
    def test_reset_without_known_subprotocol(
        self,
        started: tuple[ServerStream, DummySocketLikeTransport],
        first_string: str,
        reason: str,
    ) -> None:
        stream, transport = started
        stream.strings_received(transport, [(0, first_string), (1, "subprotocol:echo")])
        assert stream.disconnected
        assert transport.get_new()[-1] == ["write_reset", reason, True]


class RecordingQANProtocol:
    """
    A `QANProtocol` that records what it gets, and answers questions with
    whatever `answer` returns.
    """

    def __init__(self, answer: Any = lambda body: body.upper()) -> None:
        self.log: ListLog[list[Any]] = ListLog()
        self.answer = answer
        self.qan_helper: QANHelper | None = None

    def stream_started(self, stream: ServerStream, qan_helper: QANHelper) -> None:
        self.log.append(["stream_started", stream])
        self.qan_helper = qan_helper

    def stream_reset(self, reason_string: str, application_level: bool) -> None:
        self.log.append(["stream_reset", reason_string, application_level])

    def body_received(self, body: str, is_question: bool) -> Any:
        self.log.append(["body_received", body, is_question])
        return self.answer(body) if is_question else None


class QANFactory:
    def __init__(
        self, protocol: RecordingQANProtocol, validate_bodies: bool = True
    ) -> None:
        self.protocol = protocol
        self._validate_bodies = validate_bodies

    def build_protocol(self) -> QANProtocolWrapper:
        return QANProtocolWrapper(self.protocol, validate_bodies=self._validate_bodies)


class TestQANProtocolWrapper:
    def test_questions_and_notifications(self, clock: Clock) -> None:
        protocol = RecordingQANProtocol()
        stream, transport = start_stream(clock, QANFactory(protocol))
        assert protocol.log.get_new() == [["stream_started", stream]]

        stream.strings_received(
            transport,
            [
                (0, qan_frame_to_string(Notification("psst"))),
                (1, qan_frame_to_string(Question("what?", 1))),
            ],
        )
        assert protocol.log.get_new() == [
            ["body_received", "psst", False],
            ["body_received", "what?", True],
        ]
        assert list(map(string_to_qan_frame, sent(stream))) == [OkayAnswer("WHAT?", 1)]

    def test_ask_and_reset(self, clock: Clock) -> None:
        protocol = RecordingQANProtocol()
        stream, transport = start_stream(clock, QANFactory(protocol))
        assert protocol.qan_helper is not None

        answered = protocol.qan_helper.ask("are you there?")
        unanswered = protocol.qan_helper.ask("hello?")
        assert list(map(string_to_qan_frame, sent(stream))) == [
            Question("are you there?", 1),
            Question("hello?", 2),
        ]
        stream.strings_received(
            transport, [(0, qan_frame_to_string(OkayAnswer("yes", 1)))]
        )
        assert answered.result == "yes"

        # A reset fails the unanswered questions, and tells the protocol.
        stream.reset("bye")
        exception = failure_result_of(unanswered, QuestionFailed)
        assert str(exception) == "Stream reset application_level=True, reason: bye"
        assert protocol.log.get_new()[-1] == ["stream_reset", "bye", True]

    def test_cannot_ask_or_notify_after_reset(self, clock: Clock) -> None:
        """
        After the stream reset, `ask` and `notify` raise, like
        `ServerStream.send_string` does.  (`ask` must not return a Deferred
        that can never fire.)
        """
        protocol = RecordingQANProtocol()
        stream, _transport = start_stream(clock, QANFactory(protocol))
        assert protocol.qan_helper is not None
        stream.reset("bye")

        with pytest.raises(RuntimeError, match="disconnected"):
            protocol.qan_helper.ask("anyone?")
        assert "waiting for 0 peer answers" in repr(protocol.qan_helper)
        with pytest.raises(RuntimeError, match="disconnected"):
            protocol.qan_helper.notify("too late")

    def test_bad_qan_frame(self, clock: Clock) -> None:
        stream, transport = start_stream(clock, QANFactory(RecordingQANProtocol()))
        stream.strings_received(transport, [(0, "not QAN")])
        assert stream.disconnected
        assert transport.get_new()[-1] == [
            "write_reset",
            "Bad QAN frame.  Did peer send a non-QAN string?",
            True,
        ]

    def test_fatal_error_resets(self, clock: Clock) -> None:
        stream, transport = start_stream(clock, QANFactory(RecordingQANProtocol()))
        stream.strings_received(
            transport, [(0, qan_frame_to_string(OkayAnswer("?", 9)))]
        )
        assert stream.disconnected
        assert transport.get_new()[-1] == [
            "write_reset",
            "QANHelper said: Received an answer with invalid qid: 9",
            True,
        ]

    def test_answer_that_is_not_a_restricted_string(
        self, clock: Clock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """
        An answer that can't be sent is logged, with its traceback.
        """
        protocol = RecordingQANProtocol(answer=lambda body: "tab\t")
        stream, transport = start_stream(clock, QANFactory(protocol))
        stream.strings_received(transport, [(0, qan_frame_to_string(Question("?", 1)))])
        [record] = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert (
            record.message == "Bug in QANHelper._send_okay_answer or _send_error_answer"
        )
        assert record.exc_info
        assert record.exc_info[0] is ValueError

    def test_without_body_validation(self, clock: Clock) -> None:
        protocol = RecordingQANProtocol(answer=lambda body: "tab\t")
        stream, transport = start_stream(
            clock, QANFactory(protocol, validate_bodies=False)
        )
        stream.strings_received(transport, [(0, qan_frame_to_string(Question("?", 1)))])
        assert sent(stream) == ["tab\t|1K"]

    def test_uncaught_exception_is_logged(
        self, clock: Clock, caplog: pytest.LogCaptureFixture
    ) -> None:
        def answer(body: str) -> str:
            raise ZeroDivisionError

        stream, transport = start_stream(
            clock, QANFactory(RecordingQANProtocol(answer))
        )
        stream.strings_received(transport, [(0, qan_frame_to_string(Question("?", 1)))])
        assert list(map(string_to_qan_frame, sent(stream))) == [
            UnknownErrorAnswer("Uncaught exception", 1)
        ]
        [record] = caplog.records
        assert record.message == "Peer's Question #1 caused uncaught exception"
        assert record.exc_info
        assert record.exc_info[0] is ZeroDivisionError

    def test_known_error_from_a_deferred(self, clock: Clock) -> None:
        d: Deferred[str] = Deferred()
        stream, transport = start_stream(
            clock, QANFactory(RecordingQANProtocol(lambda _: d))
        )
        stream.strings_received(transport, [(0, qan_frame_to_string(Question("?", 1)))])
        assert sent(stream) == []
        d.errback(KnownError("nope"))
        assert list(map(string_to_qan_frame, sent(stream))) == [
            KnownErrorAnswer("nope", 1)
        ]


class TestQANReset:
    def test_pending_answers_cancelled(
        self, clock: Clock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """
        When the stream resets, answers still being worked out are cancelled,
        and nothing is logged as a bug.
        """
        cancelled: list[bool] = []
        d: Deferred[str] = Deferred(lambda _: cancelled.append(True))
        protocol = RecordingQANProtocol(answer=lambda body: d)
        stream, transport = start_stream(clock, QANFactory(protocol))
        stream.strings_received(transport, [(0, qan_frame_to_string(Question("?", 1)))])
        stream.reset("bye")
        assert cancelled == [True]
        assert [r for r in caplog.records if r.levelno >= logging.ERROR] == []

    def test_async_answer_cancelled(
        self, clock: Clock, caplog: pytest.LogCaptureFixture
    ) -> None:
        cancelled: list[bool] = []

        async def slow_answer(body: str) -> str:
            d: Deferred[None] = Deferred()
            clock.callLater(10, d.callback, None)
            try:
                await d
            except CancelledError:
                cancelled.append(True)
                raise
            return "too late"

        protocol = RecordingQANProtocol(answer=slow_answer)
        stream, transport = start_stream(clock, QANFactory(protocol))
        stream.strings_received(transport, [(0, qan_frame_to_string(Question("?", 1)))])
        stream.reset("bye")
        clock.advance(10)
        assert cancelled == [True]
        assert [r for r in caplog.records if r.levelno >= logging.ERROR] == []
