"""
Mocks, fakes, and dummies for Minerva's tests.
"""

from collections.abc import Callable
from dataclasses import dataclass
from io import BytesIO
from typing import Any, ClassVar, Self, cast

from twisted.internet.address import IPv4Address
from twisted.internet.defer import Deferred
from twisted.internet.interfaces import IAddress
from twisted.internet.testing import StringTransport
from twisted.web.test.requesthelper import DummyRequest

from minerva.decoders import Decoder, Int32StringDecoder
from minerva.frames import Frame, ServerFrame, decode_frame_from_server
from minerva.interfaces import PausableProducer, ServerStreamLike, ServerTransportLike
from minerva.stream import NoSuchStream, ServerStream, StreamAlreadyExists
from minerva.transport import ServerTransport, ServerTransportFactory, TransportInfo
from minerva.window import SACK, Incoming, Queue
from tests.helpers import ListLog

# --- Twisted-level fakes --------------------------------------------------------


class FakeTcpTransport(StringTransport):
    """
    A `StringTransport` with the TCP-specific methods, and producer
    registration that behaves more like the real thing.
    """

    def __init__(self) -> None:
        super().__init__()
        self.aborted = False
        self.no_delay_enabled: bool | None = None
        self.producer: Any = None
        self.streaming: bool | None = None

    def registerProducer(self, producer: Any, streaming: bool) -> None:
        if self.producer is not None:
            raise RuntimeError("Cannot register two producers")
        self.producer = producer
        self.streaming = streaming

    def unregisterProducer(self) -> None:
        # Like the real thing: don't raise if no producer is registered.
        self.producer = None

    def setTcpNoDelay(self, enabled: bool) -> None:
        self.no_delay_enabled = bool(enabled)

    def abortConnection(self) -> None:
        self.unregisterProducer()
        self.aborted = True
        self.disconnecting = True


class FakeRequest(DummyRequest):
    """
    A POST request with a `body`, that records `registerProducer` calls instead
    of pulling from the producer forever.
    """

    def __init__(self, body: bytes = b"") -> None:
        super().__init__([])
        self.method = b"POST"
        self.content = BytesIO(body)
        self.producers: ListLog[tuple[object, bool] | None] = ListLog()

    def registerProducer(self, prod: object, s: bool) -> None:
        self.producers.append((prod, s))

    def unregisterProducer(self) -> None:
        self.producers.append(None)

    def getHost(self) -> IAddress:
        return cast(IAddress, IPv4Address("TCP", "10.0.0.1", 80))

    def written_bytes(self) -> bytes:
        return b"".join(self.written)


class MockProducer:
    def __init__(self) -> None:
        self.log: ListLog[str] = ListLog()

    def get_new(self) -> list[str]:
        return self.log.get_new()

    def pauseProducing(self) -> None:
        self.log.append("pauseProducing")

    def resumeProducing(self) -> None:
        self.log.append("resumeProducing")

    def stopProducing(self) -> None:
        self.log.append("stopProducing")


class FrameDecodingTcpTransport(FakeTcpTransport):
    """
    A TCP transport that decodes what's written to it into Minerva frames.
    """

    def __init__(self, parser: Decoder) -> None:
        super().__init__()
        self.parser = parser
        self.frames: ListLog[ServerFrame] = ListLog()

    def get_new(self) -> list[ServerFrame]:
        return self.frames.get_new()

    def write(self, data: bytes) -> None:
        super().write(data)
        self.frames.extend(map(decode_frame_from_server, self.parser.feed(data)))


@dataclass
class SocketPeer:
    """
    A `ServerTransport` in int32 (Flash socket) mode, connected to a fake TCP
    peer that encodes and decodes frames.
    """

    transport: ServerTransport
    tcp: FrameDecodingTcpTransport

    @classmethod
    def connect(cls, factory: ServerTransportFactory) -> Self:
        tcp = FrameDecodingTcpTransport(Int32StringDecoder(max_length=2**20))
        transport = factory.buildProtocol(None)
        transport.makeConnection(tcp)
        transport.dataReceived(b"<int32/>\n")
        return cls(transport, tcp)

    def send(self, *frames: Frame | bytes) -> None:
        """
        Send frames (or raw frame bytes) to the transport, all at once.
        """
        self.transport.dataReceived(
            b"".join(
                Int32StringDecoder.encode(f if isinstance(f, bytes) else f.encode())
                for f in frames
            )
        )

    def get_new(self) -> list[ServerFrame]:
        """
        The frames the transport wrote since the last call.
        """
        return self.tcp.get_new()


# --- Stand-ins for Minerva's own components --------------------------------------


class MockServerStream:
    """
    Records the calls that a `ServerTransport` makes.
    """

    def __init__(self, clock: object, stream_id: str, protocol_factory: object) -> None:
        self.stream_id = stream_id
        self.log: ListLog[list[Any]] = ListLog()
        self.queue = Queue()
        self.last_sack_seen_by_server = SACK(-1, ())
        self.last_received = 0.0
        self.all_seen_transports: list[ServerTransportLike] = []
        self._incoming = Incoming()
        self._transports: set[ServerTransportLike] = set()
        self._notifications: list[Deferred[None]] = []

    def get_new(self) -> list[list[Any]]:
        return self.log.get_new()

    def send_string(self, string: str) -> None:
        self.log.append(["send_string", string])

    def reset(self, reason_string: str) -> None:
        self.log.append(["reset", reason_string])

    def reset_from_peer(self, reason_string: str, application_level: bool) -> None:
        self.log.append(["reset_from_peer", reason_string, application_level])
        for t in list(self._transports):
            t.close_gently()

    def strings_received(
        self, transport: ServerTransportLike, pairs: list[tuple[int, str]]
    ) -> None:
        self.log.append(["strings_received", transport, pairs])
        self._incoming.give(pairs)

    def sack_received(self, sack: SACK) -> bool:
        self.log.append(["sack_received", sack])
        self.last_sack_seen_by_server = sack
        return self.queue.handle_sack(sack)

    def transport_online(
        self,
        transport: ServerTransportLike,
        wants_strings: bool,
        succeeds_transport: int | None,
    ) -> None:
        self.all_seen_transports.append(transport)
        self.log.append(
            ["transport_online", transport, wants_strings, succeeds_transport]
        )
        assert transport not in self._transports
        self._transports.add(transport)

    def transport_offline(self, transport: ServerTransportLike) -> None:
        self.log.append(["transport_offline", transport])
        self._transports.remove(transport)

    def get_sack(self) -> SACK:
        return self._incoming.get_sack()

    def notify_finish(self) -> Deferred[None]:
        d: Deferred[None] = Deferred()
        self._notifications.append(d)
        return d


class DummyStreamTracker:
    """
    A stream tracker that builds `MockServerStream`s (or another class).
    """

    def __init__(
        self,
        clock: object,
        protocol_factory: object,
        stream_class: Callable[[Any, str, Any], ServerStreamLike] = MockServerStream,
    ) -> None:
        self._clock = clock
        self._protocol_factory = protocol_factory
        self._stream_class = stream_class
        self._streams: dict[str, Any] = {}

    def get_stream(self, stream_id: str) -> Any:
        try:
            return self._streams[stream_id]
        except KeyError:
            raise NoSuchStream(f"I don't know about {stream_id!r}") from None

    def build_stream(self, stream_id: str) -> Any:
        if stream_id in self._streams:
            raise StreamAlreadyExists(stream_id)
        stream = self._stream_class(self._clock, stream_id, self._protocol_factory)
        self._streams[stream_id] = stream
        return stream

    def count_streams(self) -> int:
        return len(self._streams)


class DummySocketLikeTransport:
    """
    A transport, as seen by a `ServerStream`, that records the calls it gets.
    """

    _next_transport_number: ClassVar[int] = 0

    def __init__(
        self, transport_number: int | None = None, stream: ServerStream | None = None
    ) -> None:
        """
        If `stream` is given, closing the transport takes it offline right
        away, as real transports do.
        """
        self.log: ListLog[list[Any]] = ListLog()
        if transport_number is None:
            transport_number = DummySocketLikeTransport._next_transport_number
            DummySocketLikeTransport._next_transport_number += 1
        self.transport_number = transport_number
        self.our_seq_num = -1
        self._stream = stream

    def get_new(self) -> list[list[Any]]:
        return self.log.get_new()

    def _close(self, entry: list[Any]) -> None:
        self.log.append(entry)
        if self._stream is not None:
            stream, self._stream = self._stream, None
            stream.transport_offline(self)

    def close_gently(self) -> None:
        self._close(["close_gently"])

    def caused_rwin_overflow(self) -> None:
        self._close(["caused_rwin_overflow"])

    def write_reset(self, reason_string: str, application_level: bool) -> None:
        self._close(["write_reset", reason_string, application_level])

    def write_strings(self, queue: Queue, start: int) -> None:
        self.log.append(["write_strings", queue, start])
        for seq_num, _ in queue.iter_items(start):
            self.our_seq_num = seq_num

    def registerProducer(self, producer: PausableProducer, streaming: bool) -> None:
        self.log.append(["registerProducer", producer, streaming])

    def unregisterProducer(self) -> None:
        self.log.append(["unregisterProducer"])

    def get_info(self) -> TransportInfo:
        return TransportInfo(
            transport_number=self.transport_number,
            is_primary=False,
            streaming_from_peer=True,
            streaming_to_peer=True,
            host=cast(IAddress, IPv4Address("TCP", "127.0.0.1", 0)),
        )


# --- String protocols -------------------------------------------------------------


class MockStringProtocol:
    """
    Records the calls it gets, and can be told to call `send_string` or
    `reset` on its stream, or raise, from some of them.
    """

    def __init__(
        self,
        factory: MockStringFactory,
        call_from: tuple[str, ...] = (),
        call_what: tuple[str, ...] = (),
        raise_from: tuple[str, ...] = (),
        raise_what: type[Exception] = ZeroDivisionError,
    ) -> None:
        self.factory = factory
        self.log: ListLog[list[Any]] = ListLog()
        self.stream: ServerStream | None = None
        self._call_from = call_from
        self._call_what = call_what
        self._raise_from = raise_from
        self._raise_what = raise_what

    def get_new(self) -> list[list[Any]]:
        return self.log.get_new()

    def _act(self, method: str) -> None:
        if method in self._call_from:
            assert self.stream is not None
            if "send_string" in self._call_what:
                for s in ("s2cstring0", "s2cstring1", "s2cstring2"):
                    self.stream.send_string(s)
            if "reset" in self._call_what:
                self.stream.reset("reset forced by mock protocol")
        if method in self._raise_from:
            raise self._raise_what()

    def stream_started(self, stream: ServerStream) -> None:
        self.factory.instances.append(self)
        self.log.append(["stream_started", stream])
        self.stream = stream
        self._act("stream_started")

    def stream_reset(self, reason_string: str, application_level: bool) -> None:
        self.log.append(["stream_reset", reason_string, application_level])
        self._act("stream_reset")

    def string_received(self, s: str) -> None:
        self.log.append(["string_received", s])
        self._act("string_received")


class MockStringFactory:
    """
    Builds `MockStringProtocol`s, passing `protocol_kwargs` along.
    """

    def __init__(self, **protocol_kwargs: Any) -> None:
        self.instances: list[MockStringProtocol] = []
        self._protocol_kwargs = protocol_kwargs

    def build_protocol(self) -> MockStringProtocol:
        return MockStringProtocol(self, **self._protocol_kwargs)

    @property
    def instance(self) -> MockStringProtocol:
        """
        The only protocol built so far (that started).
        """
        [instance] = self.instances
        return instance
