"""
Tests for `ServerTransport` in its TCP modes (policy file and int32), usually
with a `MockServerStream`; and for its producer logic and factory.
"""

from collections.abc import Callable
from typing import Any, cast

import pytest
from twisted.internet.address import IPv4Address
from twisted.internet.interfaces import (
    IAddress,
    IProtocol,
    IPullProducer,
    IPushProducer,
)
from twisted.internet.task import Clock
from twisted.python.failure import Failure
from zope.interface.verify import verifyObject

from minerva.decoders import Int32StringDecoder
from minerva.frames import (
    MAX_SAFE_INT,
    CommentFrame,
    KillReason,
    ResetFrame,
    SackFrame,
    SeqNumFrame,
    StreamCreatedFrame,
    StreamStatusFrame,
    StringFrame,
    TransportKillFrame,
    YouCloseItFrame,
    decode_frame_from_server,
    encode_hello_json,
)
from minerva.interfaces import ServerTransportLike
from minerva.stream import NoSuchStream, StreamTracker
from minerva.transport import ServerTransport, ServerTransportFactory, TransportInfo
from minerva.window import SACK, Queue
from tests.helpers import dice, make_hello
from tests.mocks import (
    DummyStreamTracker,
    FakeRequest,
    FakeTcpTransport,
    MockProducer,
    MockServerStream,
    MockStringFactory,
    SocketPeer,
)

STREAM_ID = "x" * 26


def kill(reason: KillReason) -> list[Any]:
    """
    The frames a socket transport writes when it is killed without a stream.
    """
    return [TransportKillFrame(reason), YouCloseItFrame()]


NOTHING = SACK(-1)


def kill_attached(
    reason: KillReason, sack: SACK = NOTHING, seen: SACK = NOTHING
) -> list[Any]:
    """
    The frames a socket transport writes when it is killed while attached.
    """
    return [
        SackFrame(sack),
        StreamStatusFrame(seen),
        TransportKillFrame(reason),
        YouCloseItFrame(),
    ]


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def tracker(clock: Clock) -> DummyStreamTracker:
    return DummyStreamTracker(clock, MockStringFactory())


@pytest.fixture
def connect(clock: Clock, tracker: DummyStreamTracker) -> Callable[[], SocketPeer]:
    factory = ServerTransportFactory(clock, tracker)
    return lambda: SocketPeer.connect(factory)


@pytest.fixture
def peer(connect: Callable[[], SocketPeer]) -> SocketPeer:
    return connect()


@pytest.fixture
def attached(peer: SocketPeer) -> SocketPeer:
    """
    A peer that sent a hello frame, creating a stream.
    """
    peer.send(make_hello())
    assert peer.get_new() == [StreamCreatedFrame()]
    return peer


def stream_of(tracker: DummyStreamTracker) -> MockServerStream:
    return tracker.get_stream(STREAM_ID)


def assert_ignores_more_data(peer: SocketPeer) -> None:
    """
    A terminating transport silently ignores the data it receives.
    """
    peer.send(b"?")
    assert peer.get_new() == []
    assert not peer.tcp.disconnecting


def test_implements(peer: SocketPeer) -> None:
    for interface in (IProtocol, IPushProducer, IPullProducer):
        assert verifyObject(interface, peer.transport)
    # A static check, for the type checker.
    _: ServerTransportLike = peer.transport


def test_repr(peer: SocketPeer) -> None:
    r = repr(peer.transport)
    assert "terminating=False" in r
    assert "stream=None" in r
    assert "paused=False" in r
    assert "our_seq_num=-1" in r


def test_transport_info_repr() -> None:
    info = TransportInfo(
        transport_number=3,
        is_primary=True,
        streaming_from_peer=False,
        streaming_to_peer=True,
        host=cast(IAddress, "not a real host"),
    )
    assert repr(info) == (
        "TransportInfo(transport_number=3, is_primary=True, streaming_from_peer=False, "
        "streaming_to_peer=True, host='not a real host', request_headers=None)"
    )


class TestModeSelection:
    @pytest.mark.parametrize("packet_size", [1, 2, 200, 511, 512])
    def test_unknown_mode_causes_rst(
        self, clock: Clock, tracker: DummyStreamTracker, packet_size: int
    ) -> None:
        """
        If the peer sends nonsense during mode detection, the transport aborts
        the connection (a TCP RST) without writing anything.
        """
        transport = ServerTransportFactory(clock, tracker).buildProtocol(None)
        tcp = FakeTcpTransport()
        transport.makeConnection(tcp)
        for piece in dice(b" " * 512, packet_size):
            assert not tcp.disconnecting
            transport.dataReceived(piece)
        assert tcp.value() == b""
        assert tcp.disconnecting
        assert tcp.aborted

    @pytest.mark.parametrize("packet_size", range(1, 20))
    def test_int32(
        self, clock: Clock, tracker: DummyStreamTracker, packet_size: int
    ) -> None:
        transport = ServerTransportFactory(clock, tracker).buildProtocol(None)
        tcp = FakeTcpTransport()
        transport.makeConnection(tcp)
        # This hello causes a stream_attach_failure, which shows that we're
        # getting frames correctly (unlike a frame corruption error would).
        hello = make_hello(stream_id="\x00" * 26, request_new_stream=False)
        for piece in dice(
            b"<int32/>\n" + Int32StringDecoder.encode(hello.encode()), packet_size
        ):
            transport.dataReceived(piece)
        frames = Int32StringDecoder(max_length=2**20).feed(tcp.value())
        assert list(map(decode_frame_from_server, frames)) == kill(
            KillReason.STREAM_ATTACH_FAILURE
        )

    @pytest.mark.parametrize("packet_size", range(1, 20))
    @pytest.mark.parametrize("garbage", [b"", b"BLAH, BLAH, BLAH"])
    def test_policy_file(
        self,
        clock: Clock,
        tracker: DummyStreamTracker,
        packet_size: int,
        garbage: bytes,
    ) -> None:
        """
        It's okay if the client sends garbage after the NULL (though no client
        has been observed to do this).
        """
        factory = ServerTransportFactory(
            clock, tracker, policy_string="<nonsense-policy/>"
        )
        transport = factory.buildProtocol(None)
        tcp = FakeTcpTransport()
        transport.makeConnection(tcp)
        for piece in dice(b"<policy-file-request/>\x00" + garbage, packet_size):
            transport.dataReceived(piece)
        assert tcp.value() == b"<nonsense-policy/>\x00"
        assert not tcp.disconnecting


class TestIsHttp:
    def test_unknown(self, clock: Clock, tracker: DummyStreamTracker) -> None:
        with pytest.raises(RuntimeError):
            ServerTransport(clock, tracker).is_http()

    def test_tcp(self, peer: SocketPeer) -> None:
        assert peer.transport.is_http() is False

    def test_http(self, clock: Clock, tracker: DummyStreamTracker) -> None:
        transport = ServerTransport(clock, tracker)
        transport.request_started(FakeRequest(b"yow \n"))
        assert transport.is_http() is True


class TestWriteStrings:
    @pytest.fixture
    def queue(self) -> Queue:
        q = Queue()
        q.extend(["string0", "string1", "string2", "string3", "string4"])
        return q

    def test_start_0(self, attached: SocketPeer, queue: Queue) -> None:
        attached.transport.write_strings(queue, start=0)
        assert attached.get_new() == [
            SeqNumFrame(0),
            *(StringFrame(f"string{n}") for n in range(5)),
        ]

    def test_start_1(self, attached: SocketPeer, queue: Queue) -> None:
        attached.transport.write_strings(queue, start=1)
        assert attached.get_new() == [
            SeqNumFrame(1),
            *(StringFrame(f"string{n}") for n in range(1, 5)),
        ]

    def test_sent_only_once(self, attached: SocketPeer) -> None:
        """
        A transport remembers which strings it wrote, so strings aren't sent
        twice even if they're still in the queue.
        """
        q = Queue()
        q.extend(["string0", "string1"])
        attached.transport.write_strings(q, start=0)
        attached.transport.write_strings(q, start=0)
        assert attached.get_new() == [
            SeqNumFrame(0),
            StringFrame("string0"),
            StringFrame("string1"),
        ]

        q.append("string2")
        attached.transport.write_strings(q, start=0)
        assert attached.get_new() == [StringFrame("string2")]

    @pytest.mark.parametrize("second_start", [0, 1])
    def test_connection_interleaving(
        self, attached: SocketPeer, queue: Queue, second_start: int
    ) -> None:
        """
        A transport that succeeded another one is first told to skip the
        strings sent over that one.  If the client then reveals that it lost
        some of them, the transport has to jump back.

        See also `test_succeeding_transport_skips_already_sent_strings`.
        """
        t = attached.transport
        t.write_strings(queue, start=3)
        t.write_strings(queue, start=3)  # pretty much a no-op
        t.write_strings(queue, start=second_start)
        t.write_strings(queue, start=second_start)  # pretty much a no-op
        assert attached.get_new() == [
            SeqNumFrame(3),
            StringFrame("string3"),
            StringFrame("string4"),
            SeqNumFrame(second_start),
            *(StringFrame(f"string{n}") for n in range(second_start, 5)),
        ]


class TestFrames:
    def test_pause_resume_before_stream_found(self, peer: SocketPeer) -> None:
        """
        Twisted may pause or resume us whenever it likes, even before we
        found the stream.
        """
        peer.transport.pauseProducing()
        peer.transport.resumeProducing()

    @pytest.mark.parametrize(
        "data",
        [
            # Prefixes that announce frames longer than 1 MiB
            b"1:xxxxxxxx",
            b"%d:" % (1024 * 1024 + 1,),
        ],
    )
    def test_frame_corruption(self, peer: SocketPeer, data: bytes) -> None:
        peer.transport.dataReceived(data)
        assert peer.get_new() == kill(KillReason.FRAME_CORRUPTION)
        assert_ignores_more_data(peer)

    def test_frame_corruption_takes_transport_offline(
        self, attached: SocketPeer, tracker: DummyStreamTracker
    ) -> None:
        stream = stream_of(tracker)
        assert stream.get_new() == [
            ["transport_online", attached.transport, False, None]
        ]

        attached.transport.dataReceived(b"1:xxxxxxxx")
        assert attached.get_new() == kill_attached(KillReason.FRAME_CORRUPTION)
        assert stream.get_new() == [["transport_offline", attached.transport]]

    def test_unknown_frame_type(self, attached: SocketPeer) -> None:
        attached.send(b"?")
        assert attached.get_new() == kill_attached(
            KillReason.INVALID_FRAME_TYPE_OR_ARGUMENTS
        )
        assert_ignores_more_data(attached)

    @pytest.mark.parametrize(
        "frame",
        [
            TransportKillFrame(KillReason.INVALID_FRAME_TYPE_OR_ARGUMENTS),
            CommentFrame(" " * 4096),
            YouCloseItFrame(),
            StreamCreatedFrame(),
            StreamStatusFrame(SACK(-1)),
        ],
    )
    def test_server_to_client_frame_from_client(
        self, attached: SocketPeer, frame: Any
    ) -> None:
        attached.send(frame)
        assert attached.get_new() == kill_attached(
            KillReason.INVALID_FRAME_TYPE_OR_ARGUMENTS
        )
        assert_ignores_more_data(attached)

    def test_first_frame_must_be_hello(self, peer: SocketPeer) -> None:
        peer.send(StringFrame("string0"))
        assert peer.get_new() == kill(KillReason.INVALID_FRAME_TYPE_OR_ARGUMENTS)

    def test_hello_sent_twice(self, attached: SocketPeer) -> None:
        attached.send(make_hello())
        assert attached.get_new() == kill_attached(
            KillReason.INVALID_FRAME_TYPE_OR_ARGUMENTS
        )

    def test_hello_sent_twice_at_once(self, peer: SocketPeer) -> None:
        peer.send(make_hello(), make_hello())
        assert peer.get_new() == [
            StreamCreatedFrame(),
            *kill_attached(KillReason.INVALID_FRAME_TYPE_OR_ARGUMENTS),
        ]

    @pytest.mark.parametrize("stream_id", ["\x00" * 20, "\x7f" * 20, "~" * 30])
    def test_valid_hello(self, peer: SocketPeer, stream_id: str) -> None:
        peer.send(make_hello(stream_id=stream_id))
        assert peer.get_new() == [StreamCreatedFrame()]

    @pytest.mark.parametrize("transport_number", [1, 1000, 12378912, 1283718237, 2**53])
    def test_any_transport_number(
        self, peer: SocketPeer, transport_number: int
    ) -> None:
        peer.send(make_hello(transport_number=transport_number))
        assert peer.get_new() == [StreamCreatedFrame()]

    @pytest.mark.parametrize("new", ["delete", 0, 0.0, -0.0, False])
    def test_no_such_stream(self, peer: SocketPeer, new: object) -> None:
        """
        A hello frame for a stream the server doesn't know (that doesn't ask
        for a new stream) gets a `stream_attach_failure`.
        """
        hello = make_hello().to_json_dict()
        if new == "delete":
            del hello["new"]
        else:
            hello["new"] = new
        peer.send(encode_hello_json(hello))
        assert peer.get_new() == kill(KillReason.STREAM_ATTACH_FAILURE)
        assert_ignores_more_data(peer)

    def test_new_stream_more_than_once_ok(
        self, connect: Callable[[], SocketPeer], tracker: DummyStreamTracker
    ) -> None:
        """
        A hello frame with `request_new_stream` for an existing stream is
        treated as if it didn't have `request_new_stream`, because the
        response to the first one might have been lost.
        """
        for _ in range(2):
            peer = connect()
            peer.send(make_hello())
            assert peer.get_new() == [StreamCreatedFrame()]
            assert tracker.count_streams() == 1

    def test_invalid_hello(self, peer: SocketPeer, tracker: DummyStreamTracker) -> None:
        peer.send(encode_hello_json({}))
        assert peer.get_new() == kill(KillReason.INVALID_FRAME_TYPE_OR_ARGUMENTS)
        with pytest.raises(NoSuchStream):
            tracker.get_stream(STREAM_ID)
        assert_ignores_more_data(peer)

    def test_no_delay_enabled(self, peer: SocketPeer) -> None:
        """
        TCP_NODELAY is enabled for TCP transports.
        """
        assert peer.tcp.no_delay_enabled is True

    def test_close_gently(self, attached: SocketPeer) -> None:
        attached.transport.close_gently()
        assert attached.get_new() == [
            SackFrame(SACK(-1)),
            StreamStatusFrame(SACK(-1)),
            YouCloseItFrame(),
        ]
        assert_ignores_more_data(attached)

    def test_caused_rwin_overflow(self, peer: SocketPeer) -> None:
        peer.transport.caused_rwin_overflow()
        assert peer.get_new() == kill(KillReason.RWIN_OVERFLOW)
        assert_ignores_more_data(peer)

    @pytest.mark.parametrize("application_level", [True, False])
    def test_write_reset(self, peer: SocketPeer, application_level: bool) -> None:
        peer.transport.write_reset("the reason", application_level=application_level)
        assert peer.get_new() == [
            ResetFrame("the reason", application_level),
            YouCloseItFrame(),
        ]
        assert_ignores_more_data(peer)

    def test_connection_lost_takes_transport_offline(
        self, attached: SocketPeer, tracker: DummyStreamTracker
    ) -> None:
        stream = stream_of(tracker)
        assert stream.get_new() == [
            ["transport_online", attached.transport, False, None]
        ]
        attached.transport.connectionLost(Failure(ValueError("a made-up error")))
        assert attached.get_new() == []
        assert stream.get_new() == [["transport_offline", attached.transport]]

    @pytest.mark.parametrize("succeeds_transport", [None, 0, 3])
    def test_wanting_strings(
        self,
        peer: SocketPeer,
        tracker: DummyStreamTracker,
        succeeds_transport: int | None,
    ) -> None:
        """
        A hello frame with "eeds" makes the transport ask for strings.
        """
        peer.send(make_hello(wants_strings=True, succeeds_transport=succeeds_transport))
        assert peer.get_new() == [StreamCreatedFrame()]
        assert stream_of(tracker).get_new() == [
            ["transport_online", peer.transport, True, succeeds_transport]
        ]

    def test_strings_delivered_to_stream_and_acked(
        self, attached: SocketPeer, tracker: DummyStreamTracker
    ) -> None:
        stream = stream_of(tracker)
        assert stream.get_new() == [
            ["transport_online", attached.transport, False, None]
        ]

        attached.send(StringFrame("string0"))
        assert stream.get_new() == [
            ["strings_received", attached.transport, [(0, "string0")]]
        ]
        assert attached.get_new() == [SackFrame(SACK(0))]

        attached.send(SeqNumFrame(2), StringFrame("string2"))
        assert stream.get_new() == [
            ["strings_received", attached.transport, [(2, "string2")]]
        ]
        assert attached.get_new() == [SackFrame(SACK(0, (2,)))]

    def test_duplicate_seq_nums_keep_their_order(
        self, attached: SocketPeer, tracker: DummyStreamTracker
    ) -> None:
        stream = stream_of(tracker)
        stream.get_new()
        attached.send(
            SeqNumFrame(0), StringFrame("b"), SeqNumFrame(0), StringFrame("a")
        )
        assert stream.get_new() == [
            ["strings_received", attached.transport, [(0, "b"), (0, "a")]]
        ]

    @pytest.mark.parametrize(
        "bad_string", [b"\x00 ", b"\xff ", b"\n ", b"\x1f ", b"\x7f ", b"hello\tworld "]
    )
    def test_string_with_illegal_bytes(
        self, attached: SocketPeer, bad_string: bytes
    ) -> None:
        attached.send(bad_string)
        assert attached.get_new() == kill_attached(
            KillReason.INVALID_FRAME_TYPE_OR_ARGUMENTS
        )

    @pytest.mark.parametrize("bad_frame", [b"?", b"\x00 ", SackFrame(SACK(5))])
    def test_strings_before_a_bad_frame_are_delivered(
        self, attached: SocketPeer, tracker: DummyStreamTracker, bad_frame: Any
    ) -> None:
        """
        Strings that arrive together with (but before) a frame that kills the
        transport are delivered and SACKed first.  (This crashed in the Python
        2 version.)
        """
        stream = stream_of(tracker)
        stream.get_new()
        attached.send(StringFrame("string0"), StringFrame("string1"), bad_frame)
        kill_reason = (
            KillReason.ACKED_UNSENT_STRINGS
            if isinstance(bad_frame, SackFrame)
            else KillReason.INVALID_FRAME_TYPE_OR_ARGUMENTS
        )
        seen = SACK(5) if isinstance(bad_frame, SackFrame) else SACK(-1)
        # The first SackFrame is for the delivered strings; the rest are the
        # usual termination frames.
        assert attached.get_new() == [
            SackFrame(SACK(1)),
            *kill_attached(kill_reason, sack=SACK(1), seen=seen),
        ]
        assert stream.get_new()[-2:] == [
            ["strings_received", attached.transport, [(0, "string0"), (1, "string1")]],
            ["transport_offline", attached.transport],
        ]

    def test_sack_frame(
        self, attached: SocketPeer, tracker: DummyStreamTracker
    ) -> None:
        stream = stream_of(tracker)
        stream.queue.extend(["string0", "string1", "string2"])
        attached.send(SackFrame(SACK(0)))
        attached.send(SackFrame(SACK(0, (2,))))
        assert attached.get_new() == []
        assert stream.get_new() == [
            ["transport_online", attached.transport, False, None],
            ["sack_received", SACK(0)],
            ["sack_received", SACK(0, (2,))],
        ]

    def test_sacked_unsent_strings(
        self, attached: SocketPeer, tracker: DummyStreamTracker
    ) -> None:
        """
        A SackFrame that acknowledges strings that were never sent kills the
        transport with `acked_unsent_strings`.
        """
        stream = stream_of(tracker)
        stream.queue.append("string0")
        attached.send(SackFrame(SACK(1)))
        assert attached.get_new() == kill_attached(
            KillReason.ACKED_UNSENT_STRINGS, seen=SACK(1)
        )
        assert stream.get_new() == [
            ["transport_online", attached.transport, False, None],
            ["sack_received", SACK(1)],
            ["transport_offline", attached.transport],
        ]

    def test_sack_in_hello_frame(
        self, peer: SocketPeer, tracker: DummyStreamTracker
    ) -> None:
        stream = tracker.build_stream(STREAM_ID)
        stream.queue.append("string0")
        peer.send(make_hello(sack=SACK(0)))
        assert peer.get_new() == [StreamCreatedFrame()]
        # Note that sack_received comes before transport_online.
        assert stream.get_new() == [
            ["sack_received", SACK(0)],
            ["transport_online", peer.transport, False, None],
        ]

    def test_sacked_unsent_strings_in_hello_frame(
        self, peer: SocketPeer, tracker: DummyStreamTracker
    ) -> None:
        """
        A hello frame whose SACK acknowledges strings that were never sent
        kills the transport, and the stream never hears of the transport.
        """
        stream = tracker.build_stream(STREAM_ID)
        stream.queue.append("string0")
        peer.send(make_hello(sack=SACK(1)))
        # The curious lack of a StreamStatusFrame is an implementation detail.
        assert peer.get_new() == [
            StreamCreatedFrame(),
            *kill(KillReason.ACKED_UNSENT_STRINGS),
        ]
        assert stream.get_new() == [["sack_received", SACK(1)]]

    @pytest.mark.parametrize("application_level", [True, False])
    @pytest.mark.parametrize("reason", ["the reason", ""])
    def test_reset(
        self,
        attached: SocketPeer,
        tracker: DummyStreamTracker,
        application_level: bool,
        reason: str,
    ) -> None:
        stream = stream_of(tracker)
        attached.send(ResetFrame(reason, application_level))
        assert stream.get_new() == [
            ["transport_online", attached.transport, False, None],
            ["reset_from_peer", reason, application_level],
            ["transport_offline", attached.transport],
        ]


class TestHeartbeats:
    @pytest.fixture
    def connect_real(self, clock: Clock) -> Callable[[], SocketPeer]:
        self.tracker = StreamTracker(
            clock, MockStringFactory(), inactive_check_interval=None
        )
        factory = ServerTransportFactory(clock, self.tracker)
        return lambda: SocketPeer.connect(factory)

    def test_heartbeats_sent(self, clock: Clock, peer: SocketPeer) -> None:
        peer.send(make_hello(max_inactivity=2))
        # The first heartbeat is sent right away.
        assert peer.get_new() == [StreamCreatedFrame(), CommentFrame("beat")]
        clock.advance(1)
        assert peer.get_new() == []
        clock.advance(1)
        assert peer.get_new() == [CommentFrame("beat")]
        clock.advance(2)
        assert peer.get_new() == [CommentFrame("beat")]

    def test_heartbeat_timer_reset_by_writes(
        self, clock: Clock, connect_real: Callable[[], SocketPeer]
    ) -> None:
        peer = connect_real()
        peer.send(make_hello(wants_strings=True, max_inactivity=2))
        assert peer.get_new() == [StreamCreatedFrame(), CommentFrame("beat")]

        clock.advance(1)
        self.tracker.get_stream(STREAM_ID).send_string("s2c0")
        clock.advance(0.001)
        assert peer.get_new() == [SeqNumFrame(0), StringFrame("s2c0")]
        clock.advance(1)
        assert peer.get_new() == []
        clock.advance(1)
        # 2 seconds since the last write, so it's time for a heartbeat.
        assert peer.get_new() == [CommentFrame("beat")]

    def test_no_heartbeats_after_closing(
        self, clock: Clock, connect_real: Callable[[], SocketPeer]
    ) -> None:
        peer = connect_real()
        peer.send(make_hello(max_inactivity=2))
        assert peer.get_new() == [StreamCreatedFrame(), CommentFrame("beat")]
        clock.advance(1)
        peer.transport.close_gently()
        assert peer.get_new() == [
            SackFrame(SACK(-1)),
            StreamStatusFrame(SACK(-1)),
            YouCloseItFrame(),
        ]
        clock.advance(2)
        assert peer.get_new() == []
        assert clock.getDelayedCalls() == []


class TestProducers:
    @pytest.fixture
    def transport_and_tcp(
        self, clock: Clock
    ) -> tuple[ServerTransport, FakeTcpTransport]:
        tracker = StreamTracker(clock, MockStringFactory())
        transport = ServerTransportFactory(clock, tracker).buildProtocol(None)
        tcp = FakeTcpTransport()
        transport.makeConnection(tcp)
        return transport, tcp

    @pytest.mark.parametrize("streaming", [True, False])
    def test_register(
        self,
        transport_and_tcp: tuple[ServerTransport, FakeTcpTransport],
        streaming: bool,
    ) -> None:
        transport, tcp = transport_and_tcp
        # Without a producer, pausing and resuming are still legal.
        transport.pauseProducing()
        transport.resumeProducing()

        producer = MockProducer()
        transport.registerProducer(producer, streaming=streaming)
        # The Minerva transport is registered, not the producer itself.
        assert tcp.producer is transport
        assert tcp.streaming is streaming

        # Pausing and resuming go straight to the producer, even a pull
        # producer.
        transport.pauseProducing()
        transport.pauseProducing()
        transport.resumeProducing()
        transport.resumeProducing()
        assert producer.get_new() == [
            "pauseProducing",
            "pauseProducing",
            "resumeProducing",
            "resumeProducing",
        ]
        transport.unregisterProducer()
        # It's idempotent.
        transport.unregisterProducer()
        assert tcp.producer is None

    def test_stop_producing_ignored(
        self, transport_and_tcp: tuple[ServerTransport, FakeTcpTransport]
    ) -> None:
        transport, _ = transport_and_tcp

        def state() -> tuple[object, ...]:
            return (transport._paused, transport._producer, transport._stream)

        before = state()
        transport.stopProducing()
        assert state() == before

        producer = MockProducer()
        transport.registerProducer(producer, streaming=True)
        before = state()
        transport.stopProducing()
        assert state() == before
        assert producer.get_new() == []

    @pytest.mark.parametrize(
        ("streaming", "expected"), [(True, ["pauseProducing"]), (False, [])]
    )
    def test_paused_transport_pauses_new_push_producer(
        self,
        transport_and_tcp: tuple[ServerTransport, FakeTcpTransport],
        streaming: bool,
        expected: list[str],
    ) -> None:
        """
        Twisted can pause us any time, and a producer that registers later
        needs to know.  (Pull producers can't be paused.)
        """
        transport, _ = transport_and_tcp
        transport.pauseProducing()
        producer = MockProducer()
        transport.registerProducer(producer, streaming=streaming)
        assert producer.get_new() == expected

    def test_cannot_register_twice(
        self, transport_and_tcp: tuple[ServerTransport, FakeTcpTransport]
    ) -> None:
        transport, _ = transport_and_tcp
        producer = MockProducer()
        transport.registerProducer(producer, streaming=True)
        for another in (producer, MockProducer()):
            with pytest.raises(RuntimeError):
                transport.registerProducer(another, streaming=True)


class TestServerTransportFactory:
    def test_policy_string(self, clock: Clock, tracker: DummyStreamTracker) -> None:
        factory = ServerTransportFactory(clock, tracker)
        factory.set_policy_string("okay")
        factory.set_policy_string(None)

    def test_policy_string_must_be_str(
        self, clock: Clock, tracker: DummyStreamTracker
    ) -> None:
        factory = ServerTransportFactory(clock, tracker)
        with pytest.raises(TypeError):
            factory.set_policy_string(b"hi")  # ty: ignore[invalid-argument-type]

    @pytest.mark.parametrize("policy", ["hello\x00", "\x00"])
    def test_policy_string_cannot_contain_null(
        self, clock: Clock, tracker: DummyStreamTracker, policy: str
    ) -> None:
        factory = ServerTransportFactory(clock, tracker)
        with pytest.raises(ValueError):
            factory.set_policy_string(policy)

    def test_build_protocol(self, clock: Clock, tracker: DummyStreamTracker) -> None:
        factory = ServerTransportFactory(clock, tracker)
        transport = factory.buildProtocol(IPv4Address("TCP", "127.0.0.1", 0))  # ty: ignore[invalid-argument-type]
        assert isinstance(transport, ServerTransport)
        assert transport.factory is factory


@pytest.mark.parametrize("wants_strings", [True, False])
def test_get_info(connect: Callable[[], SocketPeer], wants_strings: bool) -> None:
    peer = connect()
    peer.send(make_hello(transport_number=7, wants_strings=wants_strings))
    info = peer.transport.get_info()
    assert info.transport_number == 7
    assert info.is_primary is wants_strings
    assert info.streaming_from_peer is True
    assert info.streaming_to_peer is True
    assert info.request_headers is None
    assert info.host == peer.tcp.getHost()


@pytest.mark.parametrize(
    ("method", "frame"),
    [
        ("strings_received", StringFrame("string0")),
        ("sack_received", SackFrame(SACK(-1))),
        ("reset_from_peer", ResetFrame("bye", True)),
    ],
)
def test_detaches_even_if_the_stream_raises(
    attached: SocketPeer, tracker: DummyStreamTracker, method: str, frame: Any
) -> None:
    """
    If a call into the stream raises (a bug), Twisted drops the connection,
    and the transport still goes offline.
    """
    stream = stream_of(tracker)

    def broken(*args: object) -> None:
        raise ZeroDivisionError

    setattr(stream, method, broken)
    with pytest.raises(ZeroDivisionError):
        attached.send(frame)
    attached.transport.connectionLost(Failure(ZeroDivisionError()))
    assert stream.get_new()[-1] == ["transport_offline", attached.transport]


def test_peer_seq_num_cannot_exceed_max_safe_int(
    attached: SocketPeer, tracker: DummyStreamTracker
) -> None:
    attached.send(
        SeqNumFrame(MAX_SAFE_INT), StringFrame("last"), StringFrame("too far")
    )
    frames = attached.get_new()
    assert frames[-2:] == [
        TransportKillFrame(KillReason.INVALID_FRAME_TYPE_OR_ARGUMENTS),
        YouCloseItFrame(),
    ]
    assert [
        "strings_received",
        attached.transport,
        [(MAX_SAFE_INT, "last")],
    ] in stream_of(tracker).log
