"""
QAN (question, answer, notification) lets you ask the peer a question and
receive an answer or error-answer, or just notify it of something.

You can think of it as the "simplest wire-level implementation of Deferreds",
which is what AMP calls itself, but QAN goes even further: there is no command
dispatching, and the bodies of questions and answers (restricted strings,
when used over Minerva) are up to you.

QAN does not require Minerva; you can use it over any bidirectional framed
stream.
"""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any, cast

from twisted.internet.defer import CancelledError, Deferred, maybeDeferred
from twisted.python.failure import Failure

from minerva.objcheck import str_to_non_neg_limit


@dataclass(frozen=True, slots=True)
class Question:
    body: str
    qid: int


@dataclass(frozen=True, slots=True)
class OkayAnswer:
    body: str
    qid: int


@dataclass(frozen=True, slots=True)
class KnownErrorAnswer:
    body: str
    qid: int


@dataclass(frozen=True, slots=True)
class UnknownErrorAnswer:
    body: str
    qid: int


@dataclass(frozen=True, slots=True)
class Cancellation:
    qid: int


@dataclass(frozen=True, slots=True)
class Notification:
    body: str


type Answer = OkayAnswer | KnownErrorAnswer | UnknownErrorAnswer
type QANFrame = Question | Answer | Cancellation | Notification


class InvalidQANFrame(Exception):
    pass


def qan_frame_to_string(frame: QANFrame) -> str:
    """
    Encode a QAN frame (whose body, if any, must be a `str`).
    """
    match frame:
        case Cancellation(qid):
            return f"{qid}C"
        case Notification(body):
            return f"{_check_body(body)}#"
        case Question(body, qid):
            return f"{_check_body(body)}|{qid}Q"
        case OkayAnswer(body, qid):
            return f"{_check_body(body)}|{qid}K"
        case KnownErrorAnswer(body, qid):
            return f"{_check_body(body)}|{qid}E"
        case UnknownErrorAnswer(body, qid):
            return f"{_check_body(body)}|{qid}U"


def _check_body(body: object) -> str:
    if not isinstance(body, str):
        raise TypeError(f"QAN frame body must be a str, was {body!r}")
    return body


_TYPES_WITH_BODY_AND_QID: dict[str, type[Question | Answer]] = {
    "Q": Question,
    "K": OkayAnswer,
    "E": KnownErrorAnswer,
    "U": UnknownErrorAnswer,
}


def string_to_qan_frame(s: str) -> QANFrame:
    """
    Decode a QAN frame encoded by `qan_frame_to_string`.  Raises
    `InvalidQANFrame` if it is malformed.
    """
    code, rest = s[-1:], s[:-1]
    match code:
        case "":
            raise InvalidQANFrame("0-length frame")
        case "#":
            return Notification(rest)
        case "C":
            return Cancellation(_parse_qid(rest))
        case _ if code in _TYPES_WITH_BODY_AND_QID:
            body, sep, qid = rest.rpartition("|")
            if not sep:
                raise InvalidQANFrame("Expected pipe char in frame")
            return _TYPES_WITH_BODY_AND_QID[code](body, _parse_qid(qid))
        case _:
            raise InvalidQANFrame(f"Invalid QAN frame type {code!r}")


def _parse_qid(s: str) -> int:
    try:
        return str_to_non_neg_limit(s, 2**53)
    except ValueError:
        raise InvalidQANFrame("bad qid") from None


class KnownError(Exception):
    """
    Raise (or errback with) this in `body_received` to send the peer an
    error-answer with body `body`.  An `ask` Deferred errbacks with this when
    the peer sends an error-answer.
    """

    def __init__(self, body: str) -> None:
        super().__init__(body)
        self.body = body


class UnknownError(Exception):
    """
    An `ask` Deferred errbacks with this when the peer had an uncaught
    exception while answering.
    """

    def __init__(self, body: str) -> None:
        super().__init__(body)
        self.body = body


class QuestionFailed(Exception):
    """
    An `ask` Deferred errbacks with this after `QANHelper.fail_all`.
    """


# The answer to a question, or `None` for a notification.
type BodyReceivedResult = str | None
type BodyReceived = Callable[
    [str, bool],
    # `Deferred[Any]`, because Deferred is invariant: a `Deferred[str]` is not
    # a `Deferred[str | None]`.
    BodyReceivedResult
    | Deferred[Any]
    | Coroutine[Deferred[Any], Any, BodyReceivedResult],
]


class QANHelper:
    """
    Keeps track of the questions asked by us and by the peer.
    """

    def __init__(
        self,
        body_received: BodyReceived,
        log_error: Callable[[str, Failure], None],
        send_qan_frame: Callable[[QANFrame], None],
        fatal_error: Callable[[str], None],
    ) -> None:
        """
        Args:
            body_received: Called with `(body, is_question)` when the peer
                sends a Question or Notification.  For a question, the return
                value (which may also be a Deferred or a coroutine) is the
                answer.
            log_error: Called with `(message, failure)` when `body_received`
                raises for a Notification or a non-`KnownError` for a
                Question, or for other non-fatal internal errors.
            send_qan_frame: Sends a QAN frame to the peer.
            fatal_error: Called with a reason (a restricted string) when we
                can no longer handle QAN frames.  After that, stop calling
                `handle_qan_frame`.
        """
        self._body_received = body_received
        self._log_error = log_error
        self._send_qan_frame = send_qan_frame
        self._fatal_error = fatal_error

        self._qid_counter = 0
        # qid -> Deferred, or None if we already gave up on the question
        # (cancelled it, or `fail_all`ed) but still expect an answer.
        self._our_questions: dict[int, Deferred[str] | None] = {}
        self._their_questions: dict[int, Deferred[BodyReceivedResult]] = {}

    def __repr__(self) -> str:
        return (
            f"<{type(self).__name__} asked {self._qid_counter} questions, "
            f"waiting for {len(self._our_questions)} peer answers "
            f"and {len(self._their_questions)} local answers>"
        )

    def _send_okay_answer(self, body: BodyReceivedResult, qid: int) -> None:
        del self._their_questions[qid]
        if not isinstance(body, str):
            self._log_error(
                f"The answer to peer's Question #{qid} is not a str",
                Failure(TypeError(f"{body!r} is not a str")),
            )
            self._send_qan_frame(UnknownErrorAnswer("Uncaught exception", qid))
            return
        self._send_qan_frame(OkayAnswer(body, qid))

    def _send_error_answer(self, failure: Failure, qid: int) -> None:
        del self._their_questions[qid]
        match failure.value:
            case KnownError(body=body):
                self._send_qan_frame(KnownErrorAnswer(body, qid))
            case CancelledError():
                self._send_qan_frame(UnknownErrorAnswer("CancelledError", qid))
            case _:
                self._log_error(
                    f"Peer's Question #{qid} caused uncaught exception", failure
                )
                # We intentionally don't reveal anything about the exception.
                self._send_qan_frame(UnknownErrorAnswer("Uncaught exception", qid))

    def handle_qan_frame(self, frame: QANFrame) -> None:
        match frame:
            case OkayAnswer() | KnownErrorAnswer() | UnknownErrorAnswer():
                self._handle_answer(frame)

            case Notification(body):
                # maybeDeferred runs (or schedules) an `async def` handler too.
                maybeDeferred(self._body_received, body, False).addErrback(
                    lambda failure: self._log_error(
                        "Peer's Notification caused uncaught exception", failure
                    )
                )

            case Question(body, qid):
                if qid in self._their_questions:
                    self._fatal_error(f"Received Question with duplicate qid: {qid}")
                    return
                # maybeDeferred unwraps a returned Deferred or coroutine, but its
                # signature can't express that for a union return type.
                d = cast(
                    "Deferred[BodyReceivedResult]",
                    maybeDeferred(self._body_received, body, True),
                )
                self._their_questions[qid] = d
                d.addCallbacks(
                    self._send_okay_answer,
                    self._send_error_answer,
                    callbackArgs=(qid,),
                    errbackArgs=(qid,),
                )
                d.addErrback(
                    lambda failure: self._log_error(
                        "Bug in QANHelper._send_okay_answer or _send_error_answer",
                        failure,
                    )
                )

            case Cancellation(qid):
                # Cancellations for nonexistent questions are ignored.  We don't
                # remove the question here: a cancelled Deferred still runs its
                # callback or errback chain, which sends the (final) answer.
                if (d := self._their_questions.get(qid)) is not None:
                    d.cancel()

    def _handle_answer(self, answer: Answer) -> None:
        try:
            d = self._our_questions.pop(answer.qid)
        except KeyError:
            self._fatal_error(f"Received an answer with invalid qid: {answer.qid}")
            return
        if d is None:
            return  # The answer to a question we cancelled or `fail_all`ed

        match answer:
            case OkayAnswer(body):
                d.callback(body)
            case KnownErrorAnswer(body):
                d.errback(KnownError(body))
            case UnknownErrorAnswer(body):
                d.errback(UnknownError(body))

    def _send_cancel(self, qid: int) -> None:
        self._our_questions[qid] = None
        # Even after cancelling, we expect an answer from the peer (at least
        # in the typical case where the stream does not reset).
        self._send_qan_frame(Cancellation(qid))
        # Because this canceller doesn't call .callback or .errback, the
        # Deferred errbacks with CancelledError.

    def ask(self, body: str) -> Deferred[str]:
        """
        Send a Question to the peer.

        Returns a Deferred that fires with the answer's body, or errbacks with
        `KnownError`, `UnknownError`, or `QuestionFailed`.  Cancelling it sends
        a Cancellation to the peer.

        If the question can't be sent, this raises what `send_qan_frame`
        raised.  (With `QANProtocolWrapper`, that is a `RuntimeError` after
        the stream reset.)  The same goes for `notify`.
        """
        qid = self._qid_counter + 1
        # This may raise if `body` is invalid.
        self._send_qan_frame(Question(body, qid))
        self._qid_counter = qid

        d: Deferred[str] = Deferred(lambda _: self._send_cancel(qid))
        self._our_questions[qid] = d
        return d

    def notify(self, body: str) -> None:
        """
        Send a Notification to the peer.
        """
        self._send_qan_frame(Notification(body))

    def cancel_peer_questions(self) -> None:
        """
        Cancel the Deferreds (or coroutines) answering the peer's questions,
        for example because the stream is gone.
        """
        for qid, d in list(self._their_questions.items()):
            try:
                d.cancel()
            except Exception:
                # The application's canceller raised.  Go on, so that the
                # other answers are cancelled too.
                self._log_error(
                    f"Cancelling the answer to peer's Question #{qid} raised",
                    Failure(),
                )

    def fail_all(self, reason: str) -> None:
        """
        Errback all of our pending questions with `QuestionFailed(reason)`.
        """
        # A list() copy, because some buggy errback might .ask() a question.
        for qid in list(self._our_questions):
            # Looked up only now, because the errback of an earlier question
            # may have cancelled this one.
            d = self._our_questions.get(qid)
            if d is not None:
                self._our_questions[qid] = None
                d.errback(QuestionFailed(reason))
