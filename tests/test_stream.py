"""
Tests for `ServerStream` (with dummy transports) and `StreamTracker`.
"""

import logging
from typing import Any

import pytest
from twisted.internet.defer import Deferred
from twisted.internet.task import Clock

from minerva.interfaces import ServerTransportLike
from minerva.stream import (
    NoSuchStream,
    ServerStream,
    StreamAlreadyExists,
    StreamTracker,
)
from minerva.transport import TransportInfo
from minerva.window import SACK
from tests.helpers import success_result_of
from tests.mocks import (
    DummySocketLikeTransport,
    MockProducer,
    MockStringFactory,
    MockStringProtocol,
)


def logged_exceptions(
    caplog: pytest.LogCaptureFixture, exc_type: type[BaseException]
) -> list[logging.LogRecord]:
    return [
        r
        for r in caplog.records
        if r.exc_info
        and r.exc_info[0] is not None
        and issubclass(r.exc_info[0], exc_type)
    ]


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def factory() -> MockStringFactory:
    return MockStringFactory()


@pytest.fixture
def stream(clock: Clock, factory: MockStringFactory) -> ServerStream:
    return ServerStream(clock, "some fake id", factory)


@pytest.fixture
def t1() -> DummySocketLikeTransport:
    return DummySocketLikeTransport()


def test_dummy_transport_conforms() -> None:
    # A static check, for the type checker.
    _: ServerTransportLike = DummySocketLikeTransport()


def test_repr(stream: ServerStream) -> None:
    r = repr(stream)
    assert r.startswith("<ServerStream ")
    assert "stream_id='some fake id'" in r
    assert "disconnected=False" in r
    assert "queued=0" in r


def test_notify_finish(stream: ServerStream, t1: DummySocketLikeTransport) -> None:
    # A transport must attach, so that a protocol is built: `reset` can only
    # be called by "application code".
    stream.transport_online(t1, False, None)
    d = stream.notify_finish()
    assert not d.called
    stream.reset("because we want to see if the notify_finish Deferreds get called")
    assert success_result_of(d) is None
    # After the stream finished, notify_finish fires immediately.
    assert success_result_of(stream.notify_finish()) is None


def test_stream_started_called_when_first_transport_attaches(
    stream: ServerStream, factory: MockStringFactory, t1: DummySocketLikeTransport
) -> None:
    """
    The protocol is built, and its `stream_started` called, only when the
    first transport attaches.
    """
    assert factory.instances == []
    stream.transport_online(t1, False, None)
    assert factory.instance.get_new() == [["stream_started", stream]]


def test_strings_received(
    stream: ServerStream, factory: MockStringFactory, t1: DummySocketLikeTransport
) -> None:
    """
    The protocol gets the strings, in order.
    """
    stream.transport_online(t1, False, None)
    stream.strings_received(t1, [(1, "string1")])
    assert factory.instance.get_new() == [["stream_started", stream]]

    stream.strings_received(t1, [(0, "string0")])
    assert factory.instance.get_new() == [
        ["string_received", "string0"],
        ["string_received", "string1"],
    ]


def test_string_received_raises(
    clock: Clock, t1: DummySocketLikeTransport, caplog: pytest.LogCaptureFixture
) -> None:
    """
    If `string_received` raises, the exception is logged, and the other
    strings are still delivered.
    """
    factory = MockStringFactory(raise_from=("string_received",))
    stream = ServerStream(clock, "some fake id", factory)
    stream.transport_online(t1, False, None)

    stream.strings_received(t1, [(0, "string0"), (1, "string1")])
    assert len(logged_exceptions(caplog, ZeroDivisionError)) == 2
    assert factory.instance.get_new()[1:] == [
        ["string_received", "string0"],
        ["string_received", "string1"],
    ]


def test_no_strings_delivered_after_protocol_resets(
    clock: Clock, t1: DummySocketLikeTransport
) -> None:
    factory = MockStringFactory(call_from=("string_received",), call_what=("reset",))
    stream = ServerStream(clock, "some fake id", factory)
    stream.transport_online(t1, False, None)

    stream.strings_received(t1, [(0, "string0"), (1, "string1")])
    assert factory.instance.get_new()[1:] == [
        ["string_received", "string0"],
        ["stream_reset", "reset forced by mock protocol", True],
    ]


def test_stream_started_raises(
    clock: Clock, t1: DummySocketLikeTransport, caplog: pytest.LogCaptureFixture
) -> None:
    """
    If `stream_started` raises, the exception is logged, and the stream is
    reset.
    """
    factory = MockStringFactory(raise_from=("stream_started",))
    stream = ServerStream(clock, "some fake id", factory)
    stream.transport_online(t1, False, None)

    assert len(logged_exceptions(caplog, ZeroDivisionError)) == 1
    assert factory.instance.log == [
        ["stream_started", stream],
        ["stream_reset", "stream_started raised uncaught exception", False],
    ]


def test_stream_started_resets_and_raises(
    clock: Clock, t1: DummySocketLikeTransport, caplog: pytest.LogCaptureFixture
) -> None:
    """
    If `stream_started` resets the stream and then raises, the exception is
    logged, and the original reset stands.
    """
    factory = MockStringFactory(
        call_from=("stream_started",),
        call_what=("reset",),
        raise_from=("stream_started",),
    )
    stream = ServerStream(clock, "some fake id", factory)
    stream.transport_online(t1, False, None)

    assert len(logged_exceptions(caplog, ZeroDivisionError)) == 1
    assert factory.instance.log == [
        ["stream_started", stream],
        ["stream_reset", "reset forced by mock protocol", True],
    ]


def test_stream_reset_raises(
    stream: ServerStream,
    factory: MockStringFactory,
    t1: DummySocketLikeTransport,
    caplog: pytest.LogCaptureFixture,
) -> None:
    stream.transport_online(t1, False, None)
    factory.instance._raise_from = ("stream_reset",)
    stream.reset("reason")
    assert len(logged_exceptions(caplog, ZeroDivisionError)) == 1
    assert stream.disconnected


def test_too_many_undelivered_strings(
    stream: ServerStream, t1: DummySocketLikeTransport
) -> None:
    """
    If too many strings are stuck in the receive window, the transport that
    delivered the last straw is killed.  Only 50 strings are kept.
    """
    stream.transport_online(t1, False, None)
    # String #0 never arrives, so none of these can be delivered.
    stream.strings_received(t1, [(n, "string") for n in range(1, 202)])
    assert t1.get_new() == [["caused_rwin_overflow"]]
    assert stream._incoming.get_undeliverable_count() == 50


@pytest.mark.parametrize(
    ("pairs", "expected_kept"),
    [
        ([(1, "x" * (1024 * 1024 + 1))], 0),
        (
            [(1, "x" * (400 * 1024)), (2, "x" * (400 * 1024)), (3, "x" * (400 * 1024))],
            2,
        ),
    ],
)
def test_too_many_undelivered_bytes(
    stream: ServerStream,
    t1: DummySocketLikeTransport,
    pairs: list[tuple[int, str]],
    expected_kept: int,
) -> None:
    """
    If the strings stuck in the receive window take up too much memory, the
    transport that delivered the last straw is killed.  Only 1 MiB is kept.
    """
    stream.transport_online(t1, False, None)
    stream.strings_received(t1, pairs)
    assert t1.get_new() == [["caused_rwin_overflow"]]
    assert stream._incoming.get_undeliverable_count() == expected_kept


@pytest.mark.parametrize("succeeds_transport", [None, 20])
def test_strings_go_to_the_primary_transport(
    clock: Clock, stream: ServerStream, succeeds_transport: int | None
) -> None:
    """
    S2C strings are sent over the primary transport.  When a new primary
    transport attaches, the old one is closed gently, and strings are sent over
    the new one.  (A `succeeds_transport` that isn't the current primary's
    transport number is the same as `None`.)
    """
    t1 = DummySocketLikeTransport(transport_number=30)
    stream.send_string("string0")
    stream.send_string("string1")
    stream.transport_online(t1, True, None)
    assert t1.get_new() == [["write_strings", stream.queue, 0]]

    t2 = DummySocketLikeTransport()
    stream.send_string("string2")
    stream.send_string("string3")
    clock.advance(0.001)
    stream.transport_online(t2, True, succeeds_transport)

    # string2 and string3 went to t1, because t2 wasn't primary yet.
    assert t1.get_new() == [["write_strings", stream.queue, 0], ["close_gently"]]
    assert t2.get_new() == [["write_strings", stream.queue, 0]]

    stream.transport_offline(t1)
    stream.transport_offline(t2)


def test_succeeding_transport_skips_already_sent_strings(
    clock: Clock, stream: ServerStream
) -> None:
    """
    A new primary transport can claim to succeed the current one, and then
    (at first) does not get the strings already sent over the old one.

    Minerva temporarily "pretends" that those strings were SACKed, until it
    gets a real SACK.
    """
    t1 = DummySocketLikeTransport(transport_number=30)
    for n in range(5):
        stream.send_string(f"string{n}")
    stream.transport_online(t1, True, None)
    assert t1.get_new() == [["write_strings", stream.queue, 0]]

    t2 = DummySocketLikeTransport(transport_number=31)
    stream.transport_online(t2, True, 30)
    assert t1.get_new() == [["close_gently"]]
    # write_strings is called even though there is nothing to write yet.
    assert t2.get_new() == [["write_strings", stream.queue, 5]]

    stream.send_string("string5")
    stream.send_string("string6")
    clock.advance(0.001)
    assert t2.get_new() == [["write_strings", stream.queue, 5]]

    # Oh no... the client actually lost string3 and string4, and its SACK
    # says so.  Now t2 is asked to write all unSACKed strings.
    stream.sack_received(SACK(2, ()))
    assert len(stream.queue) == 4  # string3 to string6
    assert t2.get_new() == [["write_strings", stream.queue, 0]]

    stream.transport_offline(t1)
    stream.transport_offline(t2)


@pytest.mark.parametrize("connect_irrelevant_transport", [True, False])
def test_succeeds_transport_without_primary_transport(
    stream: ServerStream, connect_irrelevant_transport: bool
) -> None:
    """
    `succeeds_transport` is ignored if there is no primary transport.
    """
    if connect_irrelevant_transport:
        stream.transport_online(
            DummySocketLikeTransport(transport_number=9999), False, None
        )
    t1 = DummySocketLikeTransport()
    stream.send_string("string0")
    stream.send_string("string1")
    stream.transport_online(t1, True, 9999)
    assert t1.get_new() == [["write_strings", stream.queue, 0]]


def test_get_sack(stream: ServerStream, t1: DummySocketLikeTransport) -> None:
    stream.transport_online(t1, False, None)
    assert stream.get_sack() == SACK(-1, ())
    stream.strings_received(t1, [(0, "string")])
    assert stream.get_sack() == SACK(0, ())
    stream.strings_received(t1, [(4, "string")])
    assert stream.get_sack() == SACK(0, (4,))
    stream.strings_received(t1, [(5, "string")])
    assert stream.get_sack() == SACK(0, (4, 5))


def test_transport_online_offline(
    stream: ServerStream, t1: DummySocketLikeTransport
) -> None:
    stream.transport_online(t1, False, None)
    stream.transport_offline(t1)


def test_transport_offline_unknown_transport(
    stream: ServerStream, t1: DummySocketLikeTransport
) -> None:
    with pytest.raises(RuntimeError):
        stream.transport_offline(t1)


class _TransportListener(MockStringProtocol):
    def transport_created(self, transport_info: TransportInfo) -> None:
        self.log.append(["transport_created", transport_info.transport_number])

    def transport_destroyed(self, transport_info: TransportInfo) -> None:
        self.log.append(["transport_destroyed", transport_info.transport_number])


class _TransportListenerFactory(MockStringFactory):
    def build_protocol(self) -> _TransportListener:
        return _TransportListener(self, **self._protocol_kwargs)


class _Proxy:
    """
    Forwards every attribute that it lacks to `target`, through `__getattr__`.
    """

    def __init__(self, target: object) -> None:
        self._target = target

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)


class _ProxiedTransportListenerFactory(_TransportListenerFactory):
    def build_protocol(self) -> Any:
        return _Proxy(super().build_protocol())


@pytest.mark.parametrize(
    "factory_class", [_TransportListenerFactory, _ProxiedTransportListenerFactory]
)
def test_transport_created_and_destroyed(
    clock: Clock, factory_class: type[_TransportListenerFactory]
) -> None:
    factory = factory_class()
    stream = ServerStream(clock, "some fake id", factory)
    t1 = DummySocketLikeTransport(transport_number=1)
    t2 = DummySocketLikeTransport(transport_number=2)
    stream.transport_online(t1, False, None)
    stream.transport_online(t2, True, None)
    stream.transport_offline(t1)
    assert factory.instance.get_new() == [
        ["stream_started", stream],
        ["transport_created", 1],
        ["transport_created", 2],
        ["transport_destroyed", 1],
    ]
    # Not called for transports that go offline after the reset.
    stream.reset("bye")
    stream.transport_offline(t2)
    assert factory.instance.get_new() == [["stream_reset", "bye", True]]


class TestReset:
    def test_reset_calls_all_transports(
        self, stream: ServerStream, t1: DummySocketLikeTransport
    ) -> None:
        """
        `reset` makes all transports write a reset frame.
        """
        t2 = DummySocketLikeTransport()
        stream.transport_online(t1, False, None)
        stream.transport_online(t2, False, None)

        assert not stream.disconnected
        stream.reset("the reason")
        assert stream.disconnected
        assert t1.get_new() == [["write_reset", "the reason", True]]
        assert t2.get_new() == [["write_reset", "the reason", True]]

    def test_internal_reset_calls_all_transports(
        self, clock: Clock, stream: ServerStream, t1: DummySocketLikeTransport
    ) -> None:
        """
        An internal reset (here: timing out) writes a non-application-level
        reset frame to all transports.
        """
        t2 = DummySocketLikeTransport()
        stream.transport_online(t1, False, None)
        stream.transport_online(t2, False, None)

        stream.timed_out()
        assert stream.disconnected
        assert t1.get_new() == [["write_reset", "no activity from peer", False]]
        assert t2.get_new() == [["write_reset", "no activity from peer", False]]

    @pytest.mark.parametrize("bad", ["tab\t", "\N{SNOWMAN}", "x" * 256])
    def test_reset_validates_reason(
        self, stream: ServerStream, t1: DummySocketLikeTransport, bad: str
    ) -> None:
        stream.transport_online(t1, False, None)
        with pytest.raises(ValueError):
            stream.reset(bad)
        assert not stream.disconnected

    @pytest.mark.parametrize("by_peer", [False, True])
    def test_cannot_reset_or_send_string_after_reset(
        self, stream: ServerStream, t1: DummySocketLikeTransport, by_peer: bool
    ) -> None:
        stream.transport_online(t1, False, None)
        if by_peer:
            stream.reset_from_peer("reason", True)
        else:
            stream.reset("reason")
        for _ in range(2):
            with pytest.raises(RuntimeError):
                stream.reset("reason")
            with pytest.raises(RuntimeError):
                stream.send_string("somestring")

    @pytest.mark.parametrize("application_level", [True, False])
    def test_reset_from_peer(
        self,
        stream: ServerStream,
        factory: MockStringFactory,
        t1: DummySocketLikeTransport,
        application_level: bool,
    ) -> None:
        """
        `reset_from_peer` (normally called by a transport that received a reset
        frame) calls `stream_reset` on the protocol, and closes all transports
        gently.
        """
        t2 = DummySocketLikeTransport()
        stream.transport_online(t1, False, None)
        stream.transport_online(t2, False, None)

        stream.reset_from_peer("the reason", application_level)
        assert stream.disconnected
        assert factory.instance.get_new() == [
            ["stream_started", stream],
            ["stream_reset", "the reason", application_level],
        ]
        assert t1.get_new() == [["close_gently"]]
        assert t2.get_new() == [["close_gently"]]


class TestSendString:
    def test_validation(self, stream: ServerStream) -> None:
        """
        `send_string` raises `ValueError` or `TypeError` for anything but a
        restricted string.
        """
        stream.send_string("okay")
        stream.send_string("")
        stream.send_string(" ~")  # The boundaries

        for bad in ("bad\t", "bad\n", "bad\x7f", "\N{SNOWMAN}"):
            with pytest.raises(ValueError):
                stream.send_string(bad)
        for bad in (b"bad", 3, None):
            with pytest.raises(TypeError):
                stream.send_string(bad)  # ty: ignore[invalid-argument-type]

    def test_validation_off(self, stream: ServerStream) -> None:
        stream.send_string("okay\t", validate=False)

    def test_strings_sent_soon_and_together(
        self, clock: Clock, stream: ServerStream, t1: DummySocketLikeTransport
    ) -> None:
        stream.transport_online(t1, True, None)
        stream.send_string("a")
        stream.send_string("b")
        assert t1.get_new() == []
        clock.advance(0.001)
        assert t1.get_new() == [["write_strings", stream.queue, 0]]


class TestProducers:
    def test_register_unregister_without_transports(self, stream: ServerStream) -> None:
        producer = MockProducer()
        # Unregistering is a no-op if no producer is registered, just like
        # twisted.internet.abstract.FileDescriptor.
        stream.unregisterProducer()

        stream.registerProducer(producer, streaming=True)
        with pytest.raises(RuntimeError):
            stream.registerProducer(producer, streaming=True)
        # ...even if it's nothing like a producer.
        with pytest.raises(RuntimeError):
            stream.registerProducer(None, streaming=False)  # ty: ignore[invalid-argument-type]

        stream.unregisterProducer()
        # Unregistering worked, so registering again works.
        stream.registerProducer(producer, streaming=False)

    @pytest.mark.parametrize("streaming", [True, False])
    def test_register_unregister_with_primary_transport(
        self, stream: ServerStream, t1: DummySocketLikeTransport, streaming: bool
    ) -> None:
        stream.transport_online(t1, True, None)
        # Without a producer, pausing and resuming are still legal.
        stream.pauseProducing()
        stream.resumeProducing()

        producer = MockProducer()
        stream.registerProducer(producer, streaming=streaming)
        # Pausing and resuming go straight to the producer, even a pull
        # producer; we trust Twisted not to make invalid calls.
        stream.pauseProducing()
        stream.pauseProducing()
        stream.resumeProducing()
        stream.resumeProducing()
        assert producer.get_new() == [
            "pauseProducing",
            "pauseProducing",
            "resumeProducing",
            "resumeProducing",
        ]
        stream.unregisterProducer()
        # It's idempotent.
        stream.unregisterProducer()

    def test_paused_stream_pauses_new_push_producer(
        self, stream: ServerStream, t1: DummySocketLikeTransport
    ) -> None:
        # Without a primary transport, every push producer would be paused.
        stream.transport_online(t1, True, None)
        stream.pauseProducing()

        producer1 = MockProducer()
        stream.registerProducer(producer1, streaming=True)
        assert producer1.get_new() == ["pauseProducing"]

        # ...even a completely new one.
        stream.unregisterProducer()
        producer2 = MockProducer()
        stream.registerProducer(producer2, streaming=True)
        assert producer2.get_new() == ["pauseProducing"]

        # ...until the stream is resumed.
        stream.resumeProducing()
        stream.unregisterProducer()
        producer3 = MockProducer()
        stream.registerProducer(producer3, streaming=True)
        assert producer3.get_new() == []

    def test_paused_stream_does_not_pause_new_pull_producer(
        self, stream: ServerStream, t1: DummySocketLikeTransport
    ) -> None:
        stream.transport_online(t1, True, None)
        stream.pauseProducing()
        producer = MockProducer()
        stream.registerProducer(producer, streaming=False)
        assert producer.get_new() == []

    def test_lack_of_primary_transport_pauses_push_producer(
        self, stream: ServerStream, t1: DummySocketLikeTransport
    ) -> None:
        producer = MockProducer()
        stream.registerProducer(producer, streaming=True)
        assert producer.get_new() == ["pauseProducing"]

        stream.transport_online(t1, True, None)
        assert producer.get_new() == ["resumeProducing"]

        stream.transport_offline(t1)
        assert producer.get_new() == ["pauseProducing"]

    def test_lack_of_primary_transport_after_one_was_attached(
        self, stream: ServerStream, t1: DummySocketLikeTransport
    ) -> None:
        stream.transport_online(t1, True, None)
        stream.pauseProducing()  # pretend that t1 called this
        stream.transport_offline(t1)

        push_producer = MockProducer()
        stream.registerProducer(push_producer, streaming=True)
        assert push_producer.get_new() == ["pauseProducing"]

        stream.unregisterProducer()
        pull_producer = MockProducer()
        stream.registerProducer(pull_producer, streaming=False)
        assert pull_producer.get_new() == []

    def test_new_primary_transport_does_not_pause_producer(
        self, stream: ServerStream, t1: DummySocketLikeTransport
    ) -> None:
        stream.transport_online(t1, True, None)
        producer = MockProducer()
        stream.registerProducer(producer, streaming=True)
        stream.transport_online(DummySocketLikeTransport(), True, None)
        assert producer.get_new() == []

    def test_new_primary_transport_resumes_if_necessary(
        self, stream: ServerStream, t1: DummySocketLikeTransport
    ) -> None:
        stream.transport_online(t1, True, None)
        producer = MockProducer()
        stream.registerProducer(producer, streaming=True)
        stream.pauseProducing()  # pretend that t1 called this
        assert producer.get_new() == ["pauseProducing"]

        stream.transport_online(DummySocketLikeTransport(), True, None)
        assert producer.get_new() == ["resumeProducing"]

    def test_new_primary_transport_leaves_good_state(
        self, stream: ServerStream, t1: DummySocketLikeTransport
    ) -> None:
        """
        No redundant `resumeProducing` calls when yet another transport
        attaches.
        """
        stream.transport_online(t1, True, None)
        producer = MockProducer()
        stream.registerProducer(producer, streaming=True)
        assert producer.get_new() == []
        stream.pauseProducing()  # pretend that t1 called this
        assert producer.get_new() == ["pauseProducing"]

        t2 = DummySocketLikeTransport()
        stream.transport_online(t2, True, None)
        assert t1.get_new() == [
            ["registerProducer", stream, True],
            ["unregisterProducer"],
            ["close_gently"],
        ]
        assert t2.get_new() == [["registerProducer", stream, True]]
        assert producer.get_new() == ["resumeProducing"]

        t3 = DummySocketLikeTransport()
        stream.transport_online(t3, True, None)
        assert t2.get_new() == [["unregisterProducer"], ["close_gently"]]
        assert t3.get_new() == [["registerProducer", stream, True]]
        assert producer.get_new() == []

    def test_lack_of_transports_ignores_pull_producer(
        self, stream: ServerStream, t1: DummySocketLikeTransport
    ) -> None:
        producer = MockProducer()
        stream.registerProducer(producer, streaming=False)
        stream.transport_online(t1, True, None)
        stream.transport_offline(t1)
        assert producer.get_new() == []

    def test_only_primary_transport_going_offline_pauses(
        self, stream: ServerStream, t1: DummySocketLikeTransport
    ) -> None:
        stream.transport_online(t1, True, None)
        producer = MockProducer()
        stream.registerProducer(producer, streaming=True)

        t2 = DummySocketLikeTransport()  # not primary
        stream.transport_online(t2, False, None)
        stream.transport_offline(t2)
        assert producer.get_new() == []

    def test_register_unregister_then_new_primary(
        self, stream: ServerStream, t1: DummySocketLikeTransport
    ) -> None:
        """
        Regression test for forgetting to check for a `None` producer.
        """
        stream.registerProducer(MockProducer(), streaming=True)
        stream.unregisterProducer()
        stream.transport_online(t1, True, None)

    @pytest.mark.parametrize("streaming", [True, False])
    def test_producer_registered_on_primary_transport(
        self, stream: ServerStream, t1: DummySocketLikeTransport, streaming: bool
    ) -> None:
        producer = MockProducer()
        stream.registerProducer(producer, streaming=streaming)
        # The stream had a producer before the transport attached.
        stream.transport_online(t1, True, None)
        assert t1.get_new() == [["registerProducer", stream, streaming]]

        stream.unregisterProducer()
        assert t1.get_new() == [["unregisterProducer"]]

        stream.registerProducer(producer, streaming=streaming)
        assert t1.get_new() == [["registerProducer", stream, streaming]]

    @pytest.mark.parametrize("streaming", [True, False])
    def test_producer_moves_to_new_primary_transport(
        self, stream: ServerStream, t1: DummySocketLikeTransport, streaming: bool
    ) -> None:
        stream.registerProducer(MockProducer(), streaming=streaming)
        stream.transport_online(t1, True, None)
        assert t1.get_new() == [["registerProducer", stream, streaming]]

        t2 = DummySocketLikeTransport()
        stream.transport_online(t2, True, None)
        assert t1.get_new() == [["unregisterProducer"], ["close_gently"]]
        assert t2.get_new() == [["registerProducer", stream, streaming]]

    def test_transport_offline_effect_on_transports(
        self, stream: ServerStream, t1: DummySocketLikeTransport
    ) -> None:
        stream.transport_online(t1, True, None)
        stream.registerProducer(MockProducer(), streaming=True)
        stream.transport_offline(t1)
        stream.unregisterProducer()
        stream.registerProducer(MockProducer(), streaming=True)
        assert t1.get_new() == [
            ["registerProducer", stream, True],
            ["unregisterProducer"],
        ]

        t2 = DummySocketLikeTransport()
        stream.transport_online(t2, True, None)
        assert t2.get_new() == [["registerProducer", stream, True]]


class TestStreamTracker:
    def test_build_stream(self, clock: Clock, factory: MockStringFactory) -> None:
        tracker = StreamTracker(clock, factory)
        stream = tracker.build_stream("some fake id")
        assert type(stream) is ServerStream
        assert tracker.get_stream("some fake id") is stream

    def test_cannot_build_stream_with_same_id(
        self, clock: Clock, factory: MockStringFactory
    ) -> None:
        tracker = StreamTracker(clock, factory)
        tracker.build_stream("some fake id")
        with pytest.raises(StreamAlreadyExists):
            tracker.build_stream("some fake id")

    def test_no_such_stream(self, clock: Clock, factory: MockStringFactory) -> None:
        with pytest.raises(NoSuchStream):
            StreamTracker(clock, factory).get_stream("some fake id")

    def test_forgets_finished_streams(
        self, clock: Clock, factory: MockStringFactory, t1: DummySocketLikeTransport
    ) -> None:
        tracker = StreamTracker(clock, factory)
        stream = tracker.build_stream("some fake id")
        stream.transport_online(t1, False, None)
        stream.reset("bye")
        with pytest.raises(NoSuchStream):
            tracker.get_stream("some fake id")
        # So a new stream with the same ID can be built.
        tracker.build_stream("some fake id")

    def test_disconnects_inactive_streams(
        self, clock: Clock, factory: MockStringFactory
    ) -> None:
        """
        Every 60 seconds, streams without transports that received nothing for
        `max_idle_time` seconds are reset.  (Several at once, which once
        mutated a dict while iterating it.)
        """
        tracker = StreamTracker(clock, factory)
        idle = [tracker.build_stream(f"idle stream {n}") for n in range(3)]
        busy = tracker.build_stream("busy stream")
        busy.transport_online(DummySocketLikeTransport(), False, None)

        finished: list[Deferred[None]] = [s.notify_finish() for s in idle]
        clock.advance(120)
        assert all(d.called for d in finished)
        assert not busy.disconnected
        assert tracker.get_stream("busy stream") is busy
        for n in range(3):
            with pytest.raises(NoSuchStream):
                tracker.get_stream(f"idle stream {n}")


class _RaisingTransportListener(_TransportListener):
    def transport_created(self, transport_info: TransportInfo) -> None:
        super().transport_created(transport_info)
        raise ZeroDivisionError

    def transport_destroyed(self, transport_info: TransportInfo) -> None:
        super().transport_destroyed(transport_info)
        raise ZeroDivisionError


def test_transport_listeners_raise(
    clock: Clock, caplog: pytest.LogCaptureFixture
) -> None:
    """
    Exceptions from `transport_created` and `transport_destroyed` are logged,
    and the transport still becomes primary (or goes offline).
    """

    class Factory(MockStringFactory):
        def build_protocol(self) -> _RaisingTransportListener:
            return _RaisingTransportListener(self)

    stream = ServerStream(clock, "some fake id", Factory())
    t1 = DummySocketLikeTransport()
    stream.send_string("s")
    stream.transport_online(t1, True, None)
    assert t1.get_new() == [["write_strings", stream.queue, 0]]
    stream.transport_offline(t1)
    assert len(logged_exceptions(caplog, ZeroDivisionError)) == 2
    assert stream._primary_transport is None


class _LookupRecordingProtocol(MockStringProtocol):
    """
    Has no optional methods, and records (or raises from) the lookup of every
    attribute that it lacks.
    """

    lookup_raises = False

    def __getattr__(self, name: str) -> Any:
        self.log.append(["lookup", name])
        if self.lookup_raises:
            raise ZeroDivisionError
        raise AttributeError(name)


class _LookupRecordingFactory(MockStringFactory):
    def build_protocol(self) -> _LookupRecordingProtocol:
        return _LookupRecordingProtocol(self)


def test_transport_destroyed_not_looked_up_during_reset(clock: Clock) -> None:
    """
    While the stream resets, its transports detach, and the protocol is not
    even asked for its `transport_destroyed`.
    """
    factory = _LookupRecordingFactory()
    stream = ServerStream(clock, "some fake id", factory)
    stream.transport_online(DummySocketLikeTransport(stream=stream), True, None)
    assert factory.instance.get_new() == [
        ["stream_started", stream],
        ["lookup", "transport_created"],
    ]
    stream.reset("bye")
    assert stream._transports == set()
    assert factory.instance.get_new() == [["stream_reset", "bye", True]]


def test_looking_up_transport_listener_raises(
    clock: Clock, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    An exception from looking up `transport_created` or `transport_destroyed`
    on the protocol is logged, like an exception from calling it.
    """
    monkeypatch.setattr(_LookupRecordingProtocol, "lookup_raises", True)
    stream = ServerStream(clock, "some fake id", _LookupRecordingFactory())
    t1 = DummySocketLikeTransport()
    stream.send_string("s")
    stream.transport_online(t1, True, None)
    assert t1.get_new() == [["write_strings", stream.queue, 0]]
    stream.transport_offline(t1)
    assert len(logged_exceptions(caplog, ZeroDivisionError)) == 2
    assert stream._primary_transport is None


def test_calls_after_reset_are_ignored(
    stream: ServerStream, factory: MockStringFactory, t1: DummySocketLikeTransport
) -> None:
    stream.transport_online(t1, True, None)
    stream.reset("bye")
    t1.get_new()
    factory.instance.get_new()

    stream.strings_received(t1, [(0, "late")])
    stream.reset_from_peer("late", True)
    assert factory.instance.get_new() == []
    assert t1.get_new() == []


def test_transport_attaching_to_reset_stream_gets_reset(
    stream: ServerStream, t1: DummySocketLikeTransport
) -> None:
    """
    A transport that attaches after the stream reset (it was being set up
    meanwhile) is told about the reset, rather than left attached and silent.
    """
    stream.transport_online(t1, True, None)
    stream.reset("bye")
    t2 = DummySocketLikeTransport()
    stream.transport_online(t2, True, None)
    assert t2.get_new() == [["write_reset", "bye", True]]


@pytest.mark.parametrize("bad", [b"bye", None, 3])
def test_reset_rejects_non_str(
    stream: ServerStream, t1: DummySocketLikeTransport, bad: object
) -> None:
    stream.transport_online(t1, False, None)
    with pytest.raises(TypeError):
        stream.reset(bad)  # ty: ignore[invalid-argument-type]


def test_build_protocol_raises(
    clock: Clock, t1: DummySocketLikeTransport, caplog: pytest.LogCaptureFixture
) -> None:
    """
    If the factory can't build a protocol, the stream is reset, and the
    transport is told to close (so it won't linger).
    """

    class BrokenFactory(MockStringFactory):
        def build_protocol(self) -> MockStringProtocol:
            raise ZeroDivisionError

    stream = ServerStream(clock, "some fake id", BrokenFactory())
    stream.transport_online(t1, True, None)
    assert stream.disconnected
    assert t1.get_new() == [
        ["write_reset", "stream_started raised uncaught exception", False]
    ]
    assert len(logged_exceptions(caplog, ZeroDivisionError)) == 1


class TestPrimarySwitchWithRealisticTransports:
    """
    These transports go offline as soon as they're closed, like the real ones.
    """

    @pytest.mark.parametrize("paused", [False, True])
    def test_push_producer_not_left_paused(
        self, stream: ServerStream, paused: bool
    ) -> None:
        t1 = DummySocketLikeTransport(stream=stream)
        stream.transport_online(t1, True, None)
        producer = MockProducer()
        stream.registerProducer(producer, streaming=True)
        if paused:
            stream.pauseProducing()  # pretend that t1 called this
            assert producer.get_new() == ["pauseProducing"]

        t2 = DummySocketLikeTransport(stream=stream)
        stream.transport_online(t2, True, None)
        assert stream._primary_transport is t2
        assert t1.get_new()[-1] == ["close_gently"]
        # The producer ends up resumed (or was never paused).
        assert producer.get_new() == (["resumeProducing"] if paused else [])

    def test_reset_in_transport_destroyed(self, clock: Clock) -> None:
        """
        A protocol may reset the stream when the old primary transport goes
        away during a switch.
        """

        class Resetter(_TransportListener):
            def transport_destroyed(self, transport_info: TransportInfo) -> None:
                assert self.stream is not None
                self.stream.reset("old transport gone")

        class Factory(MockStringFactory):
            def build_protocol(self) -> Resetter:
                return Resetter(self)

        stream = ServerStream(clock, "some fake id", Factory())
        t1 = DummySocketLikeTransport(stream=stream)
        stream.transport_online(t1, True, None)
        stream.send_string("pending")
        t2 = DummySocketLikeTransport(stream=stream)
        stream.transport_online(t2, True, None)
        assert stream.disconnected
        assert t2.get_new() == [["write_reset", "old transport gone", True]]


def test_stream_tracker_stop(clock: Clock, factory: MockStringFactory) -> None:
    tracker = StreamTracker(clock, factory)
    assert clock.getDelayedCalls() != []
    tracker.stop()
    assert clock.getDelayedCalls() == []
    tracker.stop()  # idempotent
