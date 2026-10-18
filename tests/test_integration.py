"""
Integration tests for `ServerTransportFactory`, `ServerTransport`,
`StreamTracker`, and `ServerStream`, over the int32 (Flash socket) transport.
"""

from collections.abc import Callable
from typing import Any

import pytest
from twisted.internet.task import Clock

from minerva.frames import (
    Frame,
    ResetFrame,
    SackFrame,
    SeqNumFrame,
    StreamCreatedFrame,
    StreamStatusFrame,
    StringFrame,
    YouCloseItFrame,
)
from minerva.stream import ServerStream, StreamTracker
from minerva.transport import ServerTransportFactory
from minerva.window import SACK
from tests.helpers import make_hello
from tests.mocks import MockProducer, MockStringFactory, SocketPeer

STREAM_ID = "x" * 26


def closed(sack: SACK, seen: SACK) -> list[Any]:
    """
    The frames a socket transport writes when it is closed gently.
    """
    return [SackFrame(sack), StreamStatusFrame(seen), YouCloseItFrame()]


class Server:
    """
    A real stream tracker, and a way to connect transports to it.
    """

    def __init__(self, clock: Clock, factory: MockStringFactory) -> None:
        self.clock = clock
        self.factory = factory
        self.tracker = StreamTracker(clock, factory, inactive_check_interval=None)
        self._transport_factory = ServerTransportFactory(clock, self.tracker)

    def connect(self, *frames: Frame) -> SocketPeer:
        peer = SocketPeer.connect(self._transport_factory)
        if frames:
            peer.send(*frames)
        return peer

    @property
    def stream(self) -> ServerStream:
        return self.tracker.get_stream(STREAM_ID)


@pytest.fixture
def make_server() -> Callable[..., Server]:
    return lambda **protocol_kwargs: Server(
        Clock(), MockStringFactory(**protocol_kwargs)
    )


@pytest.fixture
def server(make_server: Callable[..., Server]) -> Server:
    return make_server()


def test_string_sending_and_new_transports(server: Server) -> None:
    t0 = server.connect(make_hello(wants_strings=True))
    assert t0.get_new() == [StreamCreatedFrame()]
    stream = server.stream
    proto = server.factory.instance

    # Send two strings with a gap; we get a SACK, and the protocol gets the
    # deliverable string.
    t0.send(StringFrame("string0"), SeqNumFrame(2), StringFrame("string2"))
    assert t0.get_new() == [SackFrame(SACK(0, (2,)))]
    assert proto.get_new() == [
        ["stream_started", stream],
        ["string_received", "string0"],
    ]

    # Fill the gap; the protocol gets strings 1, 2, and 3.
    t0.send(
        SeqNumFrame(1), StringFrame("string1"), SeqNumFrame(3), StringFrame("string3")
    )
    assert t0.get_new() == [SackFrame(SACK(3))]
    assert proto.get_new() == [["string_received", f"string{n}"] for n in (1, 2, 3)]

    # Send two S2C strings.
    stream.send_string("s2cstring0")
    stream.send_string("s2cstring1")
    server.clock.advance(0.001)
    assert t0.get_new() == [
        SeqNumFrame(0),
        StringFrame("s2cstring0"),
        StringFrame("s2cstring1"),
    ]

    # Don't SACK them.  A new transport gets them again, and t0 is closed.
    t1 = server.connect(
        make_hello(
            request_new_stream=False,
            wants_strings=True,
            last_sack_seen_by_client=SACK(3),
        )
    )
    assert t1.get_new() == [
        SeqNumFrame(0),
        StringFrame("s2cstring0"),
        StringFrame("s2cstring1"),
    ]
    assert t0.get_new() == closed(SACK(3), seen=SACK(-1))

    # Finally SACK them; the next transport doesn't get them, and t1 is
    # closed.
    t1.send(SackFrame(SACK(1)))
    t2 = server.connect(
        make_hello(
            request_new_stream=False,
            wants_strings=True,
            last_sack_seen_by_client=SACK(3),
        )
    )
    assert t2.get_new() == []
    assert t1.get_new() == closed(SACK(3), seen=SACK(1))

    # A reset over t2 closes t2, and the protocol hears about it.
    t2.send(ResetFrame("testing", True))
    assert t2.get_new() == closed(SACK(3), seen=SACK(1))
    assert proto.get_new() == [["stream_reset", "testing", True]]
    assert t0.get_new() == []
    assert t1.get_new() == []


def test_succeeding_transport_gets_only_new_strings(server: Server) -> None:
    t0 = server.connect(make_hello(wants_strings=True))
    assert t0.get_new() == [StreamCreatedFrame()]
    stream = server.stream

    stream.send_string("s2cstring0")
    stream.send_string("s2cstring1")
    server.clock.advance(0.001)
    assert t0.get_new() == [
        SeqNumFrame(0),
        StringFrame("s2cstring0"),
        StringFrame("s2cstring1"),
    ]

    # A transport that succeeds transport #0 doesn't get the strings sent
    # over #0 (thanks to "pretend acked"), and #0 is closed.
    t1 = server.connect(
        make_hello(
            request_new_stream=False,
            transport_number=1,
            wants_strings=True,
            succeeds_transport=0,
        )
    )
    assert t1.get_new() == []
    assert t0.get_new() == closed(SACK(-1), seen=SACK(-1))

    stream.send_string("s2cstring2")
    server.clock.advance(0.001)
    assert t1.get_new() == [SeqNumFrame(2), StringFrame("s2cstring2")]


def test_sacked_strings_not_sent_again(server: Server) -> None:
    t0 = server.connect(make_hello(wants_strings=True))
    assert t0.get_new() == [StreamCreatedFrame()]
    for n in range(12):
        server.stream.send_string(str(n))
    server.clock.advance(0.001)
    assert len(t0.get_new()) == 1 + 12  # a SeqNumFrame and 12 StringFrames
    t0.send(SackFrame(SACK(-1, (1, 3, 5, 9))))

    t1 = server.connect(
        make_hello(request_new_stream=False, transport_number=1, wants_strings=True)
    )
    assert t1.get_new() == [
        SeqNumFrame(0),
        StringFrame("0"),
        SeqNumFrame(2),
        StringFrame("2"),
        SeqNumFrame(4),
        StringFrame("4"),
        SeqNumFrame(6),
        StringFrame("6"),
        StringFrame("7"),
        StringFrame("8"),
        SeqNumFrame(10),
        StringFrame("10"),
        StringFrame("11"),
    ]


def test_ignores_already_received_strings(server: Server) -> None:
    t0 = server.connect(make_hello(wants_strings=True))
    assert t0.get_new() == [StreamCreatedFrame()]

    t0.send(SeqNumFrame(0), StringFrame("string0"))
    assert t0.get_new() == [SackFrame(SACK(0))]
    # 0 was already received, 1 was not.
    t0.send(SeqNumFrame(0), StringFrame("string0"), StringFrame("string1"))
    assert t0.get_new() == [SackFrame(SACK(1))]
    # 0 and 1 were already received, 2 was not.
    t0.send(
        SeqNumFrame(0),
        StringFrame("string0"),
        StringFrame("string1"),
        StringFrame("string2"),
    )
    assert t0.get_new() == [SackFrame(SACK(2))]

    assert server.factory.instance.get_new() == [
        ["stream_started", server.stream],
        ["string_received", "string0"],
        ["string_received", "string1"],
        ["string_received", "string2"],
    ]


@pytest.mark.parametrize("client_loses_sack", [True, False])
def test_last_sack_seen_by_client(server: Server, client_loses_sack: bool) -> None:
    """
    If the hello frame's `last_sack_seen_by_client` is out of date, the
    current SACK is written to the client.
    """
    t0 = server.connect(make_hello(wants_strings=True))
    assert t0.get_new() == [StreamCreatedFrame()]
    t0.send(StringFrame("string0"))
    # If client_loses_sack, imagine that the client never gets this one.
    assert t0.get_new() == [SackFrame(SACK(0))]

    t1 = server.connect(
        make_hello(
            request_new_stream=False,
            transport_number=1,
            wants_strings=True,
            succeeds_transport=0,
            last_sack_seen_by_client=SACK(-1 if client_loses_sack else 0),
        )
    )
    assert t1.get_new() == ([SackFrame(SACK(0))] if client_loses_sack else [])


def test_reset_as_first_frame(server: Server) -> None:
    """
    A reset right after the hello frame works, and the frames after the reset
    frame are ignored.
    """
    t0 = server.connect(make_hello())
    assert t0.get_new() == [StreamCreatedFrame()]
    stream = server.stream
    t0.send(ResetFrame("reason", True), ResetFrame("x", False), b"?")
    assert t0.get_new() == closed(SACK(-1), seen=SACK(-1))
    assert server.factory.instance.get_new() == [
        ["stream_started", stream],
        ["stream_reset", "reason", True],
    ]


def test_strings_then_reset_writes_sack(server: Server) -> None:
    """
    Strings sent along with a reset frame are SACKed before the transport
    closes.
    """
    t0 = server.connect(
        make_hello(wants_strings=True),
        StringFrame("string0"),
        StringFrame("string1"),
        ResetFrame("", True),
    )
    assert t0.get_new() == [
        StreamCreatedFrame(),
        SackFrame(SACK(1)),
        *closed(SACK(1), SACK(-1)),
    ]
    assert server.factory.instance.get_new()[1:] == [
        ["string_received", "string0"],
        ["string_received", "string1"],
        ["stream_reset", "", True],
    ]


def test_simultaneous_reset(server: Server) -> None:
    """
    Reset frames over two transports close both, and the protocol hears of
    just one.
    """
    t0 = server.connect(make_hello())
    assert t0.get_new() == [StreamCreatedFrame()]
    t1 = server.connect(make_hello())
    assert t1.get_new() == [StreamCreatedFrame()]
    stream = server.stream

    t0.send(ResetFrame("reason", True))
    t1.send(ResetFrame("reason", False))
    assert t0.get_new() == closed(SACK(-1), seen=SACK(-1))
    assert t1.get_new() == closed(SACK(-1), seen=SACK(-1))
    assert server.factory.instance.get_new() == [
        ["stream_started", stream],
        ["stream_reset", "reason", True],
    ]


# These "reentrant" tests check that calls back into the stream from the
# protocol, while Minerva is calling the protocol, work as usual.


@pytest.mark.parametrize("client_resets_immediately", [True, False])
def test_send_string_and_reset_in_stream_started(
    make_server: Callable[..., Server], client_resets_immediately: bool
) -> None:
    server = make_server(
        call_from=("stream_started",), call_what=("send_string", "reset")
    )
    frames: list[Frame] = [make_hello(wants_strings=True)]
    if client_resets_immediately:
        frames.append(ResetFrame("", True))
    t0 = server.connect(*frames)

    # The S2C strings are lost, which may be an implementation detail.
    assert t0.get_new() == [
        StreamCreatedFrame(),
        ResetFrame("reset forced by mock protocol", True),
        YouCloseItFrame(),
    ]
    assert server.factory.instance.get_new()[1:] == [
        ["stream_reset", "reset forced by mock protocol", True]
    ]


@pytest.mark.parametrize("client_resets_immediately", [True, False])
def test_send_string_in_stream_started(
    make_server: Callable[..., Server], client_resets_immediately: bool
) -> None:
    server = make_server(call_from=("stream_started",), call_what=("send_string",))
    frames: list[Frame] = [make_hello(wants_strings=True)]
    if client_resets_immediately:
        frames.append(ResetFrame("", True))
    t0 = server.connect(*frames)

    expected: list[Any] = [
        StreamCreatedFrame(),
        SeqNumFrame(0),
        StringFrame("s2cstring0"),
        StringFrame("s2cstring1"),
        StringFrame("s2cstring2"),
    ]
    if client_resets_immediately:
        expected += closed(SACK(-1), seen=SACK(-1))
    assert t0.get_new() == expected
    assert server.factory.instance.get_new()[1:] == (
        [["stream_reset", "", True]] if client_resets_immediately else []
    )


@pytest.mark.parametrize("client_resets_immediately", [True, False])
def test_send_string_and_reset_in_string_received(
    make_server: Callable[..., Server], client_resets_immediately: bool
) -> None:
    """
    The S2C strings are lost, because `send_string` writes only after a
    small delay.  After the reset, the protocol gets no more strings.
    """
    server = make_server(
        call_from=("string_received",), call_what=("send_string", "reset")
    )
    frames: list[Frame] = [
        make_hello(wants_strings=True),
        StringFrame("string0"),
        StringFrame("string1"),
    ]
    if client_resets_immediately:
        frames.append(ResetFrame("", True))
    t0 = server.connect(*frames)

    assert t0.get_new() == [
        StreamCreatedFrame(),
        SackFrame(SACK(1)),
        ResetFrame("reset forced by mock protocol", True),
        YouCloseItFrame(),
    ]
    assert server.factory.instance.get_new()[1:] == [
        ["string_received", "string0"],
        ["stream_reset", "reset forced by mock protocol", True],
    ]


@pytest.mark.parametrize("client_resets_immediately", [True, False])
def test_send_string_in_string_received(
    make_server: Callable[..., Server], client_resets_immediately: bool
) -> None:
    server = make_server(call_from=("string_received",), call_what=("send_string",))
    frames: list[Frame] = [
        make_hello(wants_strings=True),
        StringFrame("string0"),
        StringFrame("string1"),
    ]
    if client_resets_immediately:
        frames.append(ResetFrame("", True))
    t0 = server.connect(*frames)
    server.clock.advance(0.001)

    expected: list[Any] = [StreamCreatedFrame(), SackFrame(SACK(1))]
    if client_resets_immediately:
        expected += closed(SACK(1), seen=SACK(-1))
    else:
        # The mock protocol sends 3 strings for each string it receives.
        expected += [
            SeqNumFrame(0),
            *[StringFrame(f"s2cstring{n}") for n in (0, 1, 2)] * 2,
        ]
    assert t0.get_new() == expected
    assert server.factory.instance.get_new()[1:] == [
        ["string_received", "string0"],
        ["string_received", "string1"],
        *([["stream_reset", "", True]] if client_resets_immediately else []),
    ]


@pytest.mark.parametrize("client_resets_immediately", [True, False])
def test_reset_in_string_received(
    make_server: Callable[..., Server], client_resets_immediately: bool
) -> None:
    """
    If a string makes the protocol reset the stream, the strings are SACKed
    before the transport closes, and a reset frame from the client is
    ignored.
    """
    server = make_server(call_from=("string_received",), call_what=("reset",))
    frames: list[Frame] = [
        make_hello(wants_strings=True),
        StringFrame("string0"),
        StringFrame("string1"),
        StringFrame("string2"),
    ]
    if client_resets_immediately:
        frames.append(ResetFrame("client's reason", True))
    t0 = server.connect(*frames)

    assert t0.get_new() == [
        StreamCreatedFrame(),
        SackFrame(SACK(2)),
        # Because it's a reset, there's no StreamStatusFrame.
        ResetFrame("reset forced by mock protocol", True),
        YouCloseItFrame(),
    ]
    assert server.factory.instance.get_new()[1:] == [
        ["string_received", "string0"],
        ["stream_reset", "reset forced by mock protocol", True],
    ]


def test_producer_survives_primary_switch(server: Server) -> None:
    """
    Through real transports: a push producer registered on the stream isn't
    left paused when a new primary transport succeeds the old one.
    """
    t0 = server.connect(make_hello(wants_strings=True))
    stream = server.stream
    producer = MockProducer()
    stream.registerProducer(producer, streaming=True)
    assert t0.tcp.producer is t0.transport

    t1 = server.connect(
        make_hello(
            transport_number=1,
            request_new_stream=False,
            wants_strings=True,
            succeeds_transport=0,
        )
    )
    assert producer.get_new() == []
    assert t1.tcp.producer is t1.transport
    assert t0.tcp.producer is None
