"""
`ServerStream`, the server side of a Minerva stream, and `StreamTracker`,
which creates streams and finds them by ID.
"""

import logging
from typing import cast

from twisted.internet.defer import Deferred, succeed
from twisted.internet.interfaces import IReactorTime
from twisted.internet.task import LoopingCall

from minerva.frames import is_restricted_string
from minerva.interfaces import (
    Clock,
    DelayedCall,
    PausableProducer,
    ServerTransportLike,
    StringFactory,
    StringProtocol,
)
from minerva.window import SACK, Incoming, Queue

logger = logging.getLogger(__name__)


class NoSuchStream(Exception):
    pass


class StreamAlreadyExists(Exception):
    pass


# Note: just like there's no factory for `twisted.internet.tcp.Server`s, there
# is no factory for customizing the construction of `ServerStream`s.
class ServerStream:
    """
    The server side of a Minerva stream, roughly analogous to a
    `twisted.internet.tcp.Connection`, except that it can span many TCP
    connections and HTTP requests ("transports").

    The (incomplete) producer/consumer support is designed to deal with TCP
    back-pressure, and with the lack of any transport to send strings over.
    It does not help with application-level pressure; applications that need
    high-volume streaming should implement their own flow control.
    """

    # Limits for strings that arrived but can't be delivered yet, because an
    # earlier string is missing.
    max_undelivered_strings = 50
    max_undelivered_bytes = 1 * 1024 * 1024

    def __init__(
        self, clock: Clock, stream_id: str, protocol_factory: StringFactory
    ) -> None:
        self._clock = clock
        self.stream_id = stream_id
        self._protocol_factory = protocol_factory

        self._protocol: StringProtocol | None = None
        self._transports: set[ServerTransportLike] = set()
        # The transport that we send strings over.
        self._primary_transport: ServerTransportLike | None = None
        # If not None, temporarily assume that strings up to and including
        # this sequence number were received, because they were sent over the
        # transport that the current primary transport succeeded.
        self._pretend_acked: int | None = None

        self._producer: PausableProducer | None = None
        self._streaming_producer = False
        self._primary_has_producer = False
        # Does the primary transport think it is paused?  False if there is no
        # primary transport.
        self._primary_paused = False

        self.disconnected = False
        # (reason_string, application_level), once the stream has reset.
        self._reset_reason: tuple[str, bool] | None = None
        # None once the stream has finished.
        self._notifications: list[Deferred[None]] | None = []
        self._send_soon_dc: DelayedCall | None = None

        self.queue = Queue()
        self._incoming = Incoming()
        self.last_sack_seen_by_server = SACK(-1, ())
        self.last_received = clock.seconds()
        # If there are no transports and nothing was received for this many
        # seconds, the stream is reset.  This needs to be somewhat forgiving,
        # to allow for bad connections; you can raise it from your protocol.
        self.max_idle_time = 120

    def __repr__(self) -> str:
        return (
            f"<{type(self).__name__} stream_id={self.stream_id!r}, "
            f"queued={len(self.queue)}, disconnected={self.disconnected}>"
        )

    # --- The application-facing API ---------------------------------------------

    def send_string(self, string: str, validate: bool = True) -> None:
        """
        Send `string`, which must contain only characters in the inclusive
        range `" "` - `"~"`, to the peer.

        Strings are queued and sent "very soon", so calling this many times in
        a row does not lead to redundant network activity.  (This matters for
        long-polling transports, which close right after sending.)

        Set `validate=False` to skip checking that `string` is a restricted
        `str` (raising `TypeError` or `ValueError`), for a slight speedup.
        """
        if validate:
            if not isinstance(string, str):
                raise TypeError(f"not a str: {string!r}")
            if not is_restricted_string(string):
                raise ValueError(
                    f"String {string!r} contains illegal characters.  Only "
                    "0x20 (SPACE) - 0x7E (~) is allowed.  Consider using JSON "
                    "or Base64 encoding."
                )
        if self.disconnected:
            raise RuntimeError(f"Cannot send_string on disconnected {self!r}")

        # We don't need to pause our producer if the queue is getting big here:
        # an active primary transport pauses it in response to TCP pressure,
        # and without a primary transport it's already paused.
        # TODO: implement flow control for a big queue, because clients can
        # exhaust our memory by never sending SACKs.
        self.queue.append(string)
        self._try_to_send_soon()

    def reset(self, reason_string: str) -> None:
        """
        Reset (disconnect) the stream.  Strings queued for sending will never
        be sent.  `reason_string` must be a restricted string of at most 255
        characters.

        A reset frame is written to every open transport, but because there
        might be none, the client may never see it.  In that case, the client
        will soon get a `stream_attach_failure` when it tries to attach to the
        nonexistent stream.
        """
        if not isinstance(reason_string, str):
            raise TypeError(f"reason_string must be a str, was {reason_string!r}")
        if not is_restricted_string(reason_string) or len(reason_string) > 255:
            raise ValueError(f"bad reason_string {reason_string!r}")
        if self.disconnected:
            raise RuntimeError(f"Cannot reset disconnected {self!r}")
        self._reset(reason_string, application_level=True)

    # This API resembles `twisted.web.server.Request.notifyFinish`.
    def notify_finish(self) -> Deferred[None]:
        """
        Return a Deferred that fires (with `None`) when this stream finishes.
        """
        if self._notifications is None:
            return succeed(None)
        d: Deferred[None] = Deferred()
        self._notifications.append(d)
        return d

    # This is a modified copy of `twisted.internet.interfaces.IConsumer`.
    # We have it because not all string protocols will be producers.
    def registerProducer(self, producer: PausableProducer, streaming: bool) -> None:
        """
        Register `producer`, which creates the strings for this stream.

        If `streaming`, `producer` is a push producer: it is paused when the
        primary transport is under TCP pressure or there is no primary
        transport, and resumed when that's over.  Otherwise, `producer` is a
        pull producer, whose `resumeProducing` is called when more strings can
        be sent.
        """
        if self._producer is not None:
            raise RuntimeError(
                f"Cannot register producer {producer!r}, because producer "
                f"{self._producer!r} was never unregistered."
            )
        self._producer = producer
        self._streaming_producer = streaming

        if streaming and (self._primary_paused or self._primary_transport is None):
            producer.pauseProducing()
        if self._primary_transport is not None:
            self._register_producer_on_primary()

    def unregisterProducer(self) -> None:
        """
        Stop consuming strings from the producer, without disconnecting.
        """
        self._producer = None
        if self._primary_transport is not None:
            self._unregister_producer_on_primary()

    # --- Called by Minerva's transports -----------------------------------------

    def pauseProducing(self) -> None:
        """
        Called only by the primary transport, in response to TCP pressure.
        """
        self._primary_paused = True
        if self._producer is not None:
            self._producer.pauseProducing()

    def resumeProducing(self) -> None:
        """
        Called only by the primary transport.
        """
        self._primary_paused = False
        if self._producer is not None:
            self._producer.resumeProducing()

    def reset_from_peer(self, reason_string: str, application_level: bool) -> None:
        """
        A transport received a reset frame from the peer.  (The transport
        still needs to call `transport_offline` afterwards.)
        """
        if self.disconnected:
            return
        self._cancel_send_soon()
        self.disconnected = True
        self._reset_reason = (reason_string, application_level)
        # A copy, because `_transports` shrinks as transports go offline.
        for t in list(self._transports):
            t.close_gently()
        self._finish_reset(reason_string, application_level)

    def timed_out(self) -> None:
        self._reset("no activity from peer", application_level=False)

    def strings_received(
        self, transport: ServerTransportLike, pairs: list[tuple[int, str]]
    ) -> None:
        """
        `transport` received the (already sorted) `(seq_num, string)` `pairs`.
        """
        assert transport in self._transports, self._transports
        if self.disconnected:
            return
        assert self._protocol is not None

        strings, hit_limit = self._incoming.give(
            pairs, self.max_undelivered_strings, self.max_undelivered_bytes
        )
        for s in strings:
            try:
                self._protocol.string_received(s)
            except Exception:
                logger.exception("string_received raised an uncaught exception")
            # Don't deliver strings to a protocol that reset the stream.
            if self.disconnected:
                return
        # We deliver the deliverable strings even if the receive window
        # overflowed, just in case the peer sent something useful.
        if hit_limit:
            transport.caused_rwin_overflow()

    def sack_received(self, sack: SACK) -> bool:
        """
        A transport received a SACK from the peer (in a SACK frame or a hello
        frame).  Returns `True` if it was a bad SACK.
        """
        # We just got a probably-up-to-date SACK from the client, so there's
        # no need to pretend any more.
        was_pretending = self._pretend_acked is not None
        self._pretend_acked = None
        self.last_sack_seen_by_server = sack

        if self.queue.handle_sack(sack):
            return True
        if was_pretending:
            # The SACK may reveal that the client lost strings that were sent
            # over the previous primary transport, so try to send them again.
            self._try_to_send()
        return False

    def transport_online(
        self,
        transport: ServerTransportLike,
        wants_strings: bool,
        succeeds_transport: int | None,
    ) -> None:
        """
        A transport attached.  This happens even for very short-lived HTTP
        transports that only upload strings.

        If `wants_strings`, the transport becomes the primary transport.  If
        it succeeds the current primary transport, temporarily assume that the
        strings already sent over that one were received.
        """
        self._transports.add(transport)
        if self.disconnected:
            # The stream died while this transport was attaching (for example,
            # while it processed the SACK in its hello frame).  Tell the
            # client, rather than leave the transport attached and silent.
            assert self._reset_reason is not None
            transport.write_reset(*self._reset_reason)
            return

        # This is done here rather than in `_new_primary`, because the client
        # should be able to upload strings without ever having a primary
        # transport.
        if self._protocol is None:
            try:
                self._protocol = self._protocol_factory.build_protocol()
                # This can do anything to us, including reset or send_string.
                self._protocol.stream_started(self)
            except Exception:
                logger.exception("Couldn't build or start the protocol")
                self._reset(
                    "stream_started raised uncaught exception", application_level=False
                )
                return
            if self.disconnected:
                return

        # `stream_started` is called before `transport_created`, even though
        # the transport caused the stream to start, because that's a nicer
        # abstraction, and it matches the client: there, `stream_started` is
        # called when you call `.start()`.
        # The optional methods are looked up with `getattr`, so that a protocol
        # may also supply them dynamically (a proxy with `__getattr__`, say).
        transport_created = getattr(self._protocol, "transport_created", None)
        if transport_created is not None:
            try:
                # This can do anything to us, including reset or send_string.
                transport_created(transport.get_info())
            except Exception:
                logger.exception("transport_created raised an uncaught exception")
            if self.disconnected:
                return

        if wants_strings:
            # TODO: do we really need the old primary transport to still be
            # attached?  Can't we just remember its transport number and
            # our_seq_num?  Then a transport could succeed it even if it
            # detached in the meantime.
            primary = self._primary_transport
            if (
                succeeds_transport is not None
                and primary is not None
                and succeeds_transport == primary.transport_number
                and primary.our_seq_num != -1
            ):
                self._pretend_acked = primary.our_seq_num
            self._new_primary(transport)
            self._try_to_send()

    def transport_offline(self, transport: ServerTransportLike) -> None:
        """
        A transport detached.
        """
        try:
            self._transports.remove(transport)
        except KeyError:
            raise RuntimeError(
                f"Cannot take {transport!r} offline; it wasn't registered"
            ) from None

        if transport is self._primary_transport:
            self._unregister_producer_on_primary()
            self._primary_transport = None
            # Not strictly necessary (without a primary transport, producers
            # are paused anyway), but it makes debugging easier.
            self._primary_paused = False
            if self._producer is not None and self._streaming_producer:
                self._producer.pauseProducing()

        transport_destroyed = getattr(self._protocol, "transport_destroyed", None)
        if not self.disconnected and transport_destroyed is not None:
            try:
                # This can do anything to us, including reset or send_string.
                transport_destroyed(transport.get_info())
            except Exception:
                logger.exception("transport_destroyed raised an uncaught exception")

    def get_sack(self) -> SACK:
        """
        Return the SACK for the strings we received.
        """
        return self._incoming.get_sack()

    # --- Internals --------------------------------------------------------------

    def _cancel_send_soon(self) -> None:
        if self._send_soon_dc is not None:
            if self._send_soon_dc.active():
                self._send_soon_dc.cancel()
            self._send_soon_dc = None

    def _try_to_send(self) -> None:
        self._cancel_send_soon()
        # The stream may have been reset underneath a call to the protocol.
        if self.disconnected:
            return
        if self.queue and self._primary_transport is not None:
            start = 0 if self._pretend_acked is None else self._pretend_acked + 1
            self._primary_transport.write_strings(self.queue, start)

    def _try_to_send_soon(self) -> None:
        if self._send_soon_dc is None:
            self._send_soon_dc = self._clock.callLater(0.001, self._try_to_send)

    def _reset(self, reason_string: str, application_level: bool) -> None:
        """
        Write a reset frame to every transport, and finish the stream.
        """
        if self.disconnected:
            return
        self._cancel_send_soon()
        self.disconnected = True
        self._reset_reason = (reason_string, application_level)
        # A copy, because `_transports` shrinks as transports go offline.
        for t in list(self._transports):
            t.write_reset(reason_string, application_level)
        self._finish_reset(reason_string, application_level)

    def _finish_reset(self, reason_string: str, application_level: bool) -> None:
        notifications, self._notifications = self._notifications, None
        assert notifications is not None, "the stream can finish only once"
        for d in notifications:
            d.callback(None)
        protocol, self._protocol = self._protocol, None
        if protocol is not None:
            try:
                protocol.stream_reset(reason_string, application_level)
            except Exception:
                logger.exception("stream_reset raised an uncaught exception")

    def _register_producer_on_primary(self) -> None:
        """
        Called when we have a new primary transport, or when a producer
        registers with us.
        """
        assert self._primary_transport is not None
        if not self._primary_has_producer:
            self._primary_transport.registerProducer(self, self._streaming_producer)
            self._primary_has_producer = True

    def _unregister_producer_on_primary(self) -> None:
        """
        Note that this doesn't change `_primary_paused`.
        """
        if self._primary_has_producer:
            assert self._primary_transport is not None
            self._primary_transport.unregisterProducer()
            self._primary_has_producer = False

    def _new_primary(self, transport: ServerTransportLike) -> None:
        old_primary = self._primary_transport
        if old_primary is not None:
            self._unregister_producer_on_primary()
            # If the old primary transport paused our producer, that no longer
            # matters, so resume it.
            if (
                self._primary_paused
                and self._producer is not None
                and self._streaming_producer
            ):
                self._producer.resumeProducing()
            self._primary_paused = False
        else:
            # Without a primary transport, our push producer was paused.
            if self._producer is not None and self._streaming_producer:
                self._producer.resumeProducing()
            assert not self._primary_paused

        self._primary_transport = transport
        if self._producer is not None:
            self._register_producer_on_primary()
        # Close the old primary only now: it goes offline right away, and
        # `transport_offline` must not mistake it for the primary transport
        # (which would pause our producer).
        if old_primary is not None:
            old_primary.close_gently()


class StreamTracker:
    """
    Creates `ServerStream`s and keeps track of them, so that transports can
    find the right one by the stream ID that the client sent.  It also resets
    streams that the client seems to have abandoned.
    """

    def __init__(
        self,
        clock: Clock,
        protocol_factory: StringFactory,
        inactive_check_interval: float | None = 60,
    ) -> None:
        """
        Every `inactive_check_interval` seconds, abandoned streams are reset.
        If `None`, call `disconnect_inactive` yourself.
        """
        self._clock = clock
        self._protocol_factory = protocol_factory
        self._streams: dict[str, ServerStream] = {}
        self._idle_killer: LoopingCall | None = None

        if inactive_check_interval is not None:
            self._idle_killer = LoopingCall(self.disconnect_inactive)
            # Our Clock protocol is the part of IReactorTime that LoopingCall uses.
            self._idle_killer.clock = cast(IReactorTime, clock)
            # `now=True` to exercise the code early.
            self._idle_killer.start(inactive_check_interval, now=True)

    def stop(self) -> None:
        """
        Stop resetting abandoned streams periodically.
        """
        if self._idle_killer is not None and self._idle_killer.running:
            self._idle_killer.stop()

    def get_stream(self, stream_id: str) -> ServerStream:
        try:
            return self._streams[stream_id]
        except KeyError:
            raise NoSuchStream(f"I don't know about {stream_id!r}") from None

    def build_stream(self, stream_id: str) -> ServerStream:
        if stream_id in self._streams:
            raise StreamAlreadyExists(
                f"cannot make stream with id {stream_id!r} because it already exists"
            )
        stream = ServerStream(self._clock, stream_id, self._protocol_factory)
        self._streams[stream_id] = stream
        stream.notify_finish().addBoth(lambda _: self._streams.pop(stream_id))
        return stream

    def disconnect_inactive(self) -> None:
        """
        Reset the streams that the client appears to have abandoned.  By
        default, this is called automatically every 60 seconds.
        """
        now = self._clock.seconds()
        # A copy, because `timed_out` makes us forget the stream.
        for stream in list(self._streams.values()):
            if (
                not stream._transports
                and stream.last_received + stream.max_idle_time <= now
            ):
                stream.timed_out()
