"""
The interfaces between Minerva's components, and between Minerva and your
application, as `typing.Protocol`s.

You implement `StringFactory` and `StringProtocol` (or `QANProtocol`, wrapped
in a `QANProtocolWrapper`).  Your protocol can optionally implement
`TransportCreatedListener` and/or `TransportDestroyedListener`.  Subclassing
these protocols is not required, but lets a type checker verify your
implementation.

The other protocols describe what Minerva's own components need from each
other; tests use them to substitute fakes.
"""

from collections.abc import Callable, Coroutine
from typing import Any, Protocol, runtime_checkable

# These are only used in annotations, and import this module themselves.
lazy from twisted.internet.defer import Deferred

lazy from minerva.qan import QANHelper
lazy from minerva.stream import ServerStream
lazy from minerva.transport import TransportInfo
lazy from minerva.window import SACK, Queue

# --- Implemented by your application --------------------------------------------


class StringProtocol(Protocol):
    """
    String-based communication that abstracts away the Comet logic and the
    transports; analogous to `twisted.internet.interfaces.IProtocol`.

    Note: when you reset a stream, some (or all) of the strings you recently
    sent may be lost.  If you need a clean close, use your own application-
    level strings to agree that it is safe to close, then reset.

    The simplest way to end abandoned streams is an application-level ping
    that your client sends every ~55 seconds; reset the stream if none has
    arrived for 2 minutes.
    """

    def stream_started(self, stream: ServerStream) -> None:
        """
        The `stream` for this protocol has started.  On the server, this
        happens when the client attaches its first transport.

        You'll want to keep a reference: `self.stream = stream`.
        """
        ...

    def stream_reset(self, reason_string: str, application_level: bool) -> None:
        """
        The stream has reset, because of `ServerStream.reset`, because of a
        reset frame from the peer, or because Minerva gave up on it.

        `reason_string` is a restricted string.  `application_level` is true if
        the reset was caused by an application (not Minerva internals).
        """
        ...

    def string_received(self, s: str) -> None:
        """
        A restricted string `s` arrived from the peer.
        """
        ...


class StringFactory(Protocol):
    def build_protocol(self) -> StringProtocol:
        """
        Called when a `ServerStream` has been established.  Unlike Twisted's
        `IProtocolFactory.buildProtocol`, you can't refuse it.
        """
        ...


@runtime_checkable
class TransportCreatedListener(Protocol):
    def transport_created(self, transport_info: TransportInfo) -> None:
        """
        A transport attached to the stream.  This is always called after
        `stream_started`, even for the transport that started the stream.
        """
        ...


@runtime_checkable
class TransportDestroyedListener(Protocol):
    def transport_destroyed(self, transport_info: TransportInfo) -> None:
        """
        A transport detached from the stream.  (Not called for transports
        that detach while the stream is resetting.)
        """
        ...


class QANProtocol(Protocol):
    """
    Communication with questions, answers, and notifications.  Wrap your
    implementation in a `minerva.QANProtocolWrapper`.
    """

    def stream_started(self, stream: ServerStream, qan_helper: QANHelper) -> None:
        """
        Like `StringProtocol.stream_started`.  Keep a reference to the
        `qan_helper` too, and use its `ask` and `notify` for all communication
        instead of calling `stream.send_string` yourself.
        """
        ...

    def stream_reset(self, reason_string: str, application_level: bool) -> None:
        """
        Like `StringProtocol.stream_reset`.
        """
        ...

    def body_received(
        self, body: str, is_question: bool
    ) -> str | Deferred[Any] | Coroutine[Deferred[Any], Any, str | None] | None:
        """
        The peer asked a question or sent a notification with restricted-string
        `body`.

        For a question, return the answer: a restricted `str`, or a `Deferred`
        or coroutine (e.g. make this an `async def`) that produces one.  For a
        notification, the return value is ignored.  Raise
        (or errback with) `minerva.qan.KnownError(body)` to send an
        error-answer with that body.  Any other exception sends an
        uninformative "unknown error" answer.
        """
        ...


# --- Minerva's internal interfaces ----------------------------------------------


class DelayedCall(Protocol):
    def active(self) -> bool: ...

    def cancel(self) -> None: ...


class Clock(Protocol):
    """
    The part of Twisted's `IReactorTime` that Minerva uses.  Both the reactor
    and `twisted.internet.task.Clock` provide it.
    """

    def seconds(self) -> float: ...

    def callLater(
        self,
        delay: float,
        callable: Callable[..., object],
        /,
        *args: object,
        **kw: object,
    ) -> DelayedCall: ...


class PausableProducer(Protocol):
    def pauseProducing(self) -> None: ...

    def resumeProducing(self) -> None: ...


class Producer(PausableProducer, Protocol):
    """
    A Twisted push or pull producer.
    """

    def stopProducing(self) -> None: ...


class ServerTransportLike(Protocol):
    """
    What a `ServerStream` needs from a transport.
    """

    @property
    def transport_number(self) -> int | None: ...

    @property
    def our_seq_num(self) -> int:
        """
        The sequence number of the last string written to the peer, or -1.
        """
        ...

    def write_strings(self, queue: Queue, start: int) -> None:
        """
        Write the strings in `queue` with sequence numbers `>= start`, skipping
        those this transport already wrote -- unless `start` is lower than it
        was in the previous call.
        """
        ...

    def close_gently(self) -> None:
        """
        Close this transport, because it is no longer useful (due to HTTP
        limitations), or because a new primary transport has attached.
        """
        ...

    def caused_rwin_overflow(self) -> None:
        """
        Close this transport, because it overflowed our receive window.  This
        is a strong hint that the client should attach a new transport and
        send deliverable strings.
        """
        ...

    def write_reset(self, reason_string: str, application_level: bool) -> None:
        """
        Write a reset frame (which the peer may or may not receive), then
        close.
        """
        ...

    def registerProducer(self, producer: PausableProducer, streaming: bool) -> None: ...

    def unregisterProducer(self) -> None: ...

    def get_info(self) -> TransportInfo: ...


class ServerStreamLike(Protocol):
    """
    What a `ServerTransport` needs from a stream.
    """

    last_received: float

    @property
    def last_sack_seen_by_server(self) -> SACK: ...

    def get_sack(self) -> SACK: ...

    def sack_received(self, sack: SACK) -> bool:
        """
        Returns `True` for a bad SACK.
        """
        ...

    def strings_received(
        self, transport: ServerTransportLike, pairs: list[tuple[int, str]]
    ) -> None: ...

    def reset_from_peer(self, reason_string: str, application_level: bool) -> None: ...

    def transport_online(
        self,
        transport: ServerTransportLike,
        wants_strings: bool,
        succeeds_transport: int | None,
    ) -> None: ...

    def transport_offline(self, transport: ServerTransportLike) -> None: ...


class StreamTrackerLike(Protocol):
    """
    What a `ServerTransport` needs from a stream tracker.
    """

    def get_stream(self, stream_id: str) -> ServerStreamLike:
        """
        Raises `minerva.stream.NoSuchStream`.
        """
        ...

    def build_stream(self, stream_id: str) -> ServerStreamLike:
        """
        Raises `minerva.stream.StreamAlreadyExists`.
        """
        ...
