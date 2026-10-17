"""
`ServerTransport`: one per HTTP request or TCP connection.  It speaks Minerva
frames to the peer, and attaches to a `ServerStream`.

A TCP connection (used by the client's Flash socket transport) first sends
either a Flash policy-file request, or `<int32/>\\n` followed by
length-prefixed frames.  An HTTP request has newline-delimited frames in its
POST body.
"""

import dataclasses
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto
from operator import itemgetter
from typing import IO, Protocol, cast, override

from twisted.internet.interfaces import IAddress, IPullProducer, IPushProducer
from twisted.internet.protocol import Factory, connectionDone
from twisted.internet.protocol import Protocol as TwistedProtocol
from twisted.python.failure import Failure
from twisted.web.http_headers import Headers
from zope.interface import implementer

from minerva.decoders import (
    Decoder,
    DelimitedStringDecoder,
    FrameTooLong,
    Int32StringDecoder,
)
from minerva.frames import (
    MAX_SAFE_INT,
    CommentFrame,
    Frame,
    HelloFrame,
    InvalidFrame,
    KillReason,
    ResetFrame,
    SackFrame,
    SeqNumFrame,
    StreamCreatedFrame,
    StreamStatusFrame,
    StringFrame,
    TransportKillFrame,
    YouCloseItFrame,
    decode_frame_from_client,
    is_restricted_string,
)
from minerva.interfaces import (
    Clock,
    DelayedCall,
    PausableProducer,
    ServerStreamLike,
    StreamTrackerLike,
)
from minerva.stream import NoSuchStream, StreamAlreadyExists
from minerva.window import SACK, Queue

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class TransportInfo:
    """
    Information about a transport, passed to your protocol's
    `transport_created` and `transport_destroyed`.
    """

    transport_number: int
    # Does the client want strings over this transport?
    is_primary: bool
    # Can the peer send us data more than once over this transport?
    streaming_from_peer: bool
    # Can we send the peer data more than once over this transport?
    streaming_to_peer: bool
    host: IAddress
    # For HTTP transports only.
    request_headers: Headers | None = dataclasses.field(default=None, hash=False)


class _TcpTransport(Protocol):
    """
    The part of `ITCPTransport` that we use.
    """

    def write(self, data: bytes) -> None: ...
    def setTcpNoDelay(self, enabled: bool) -> None: ...
    def abortConnection(self) -> None: ...
    def registerProducer(self, producer: object, streaming: bool) -> None: ...
    def unregisterProducer(self) -> None: ...
    def getHost(self) -> IAddress: ...


class _Request(Protocol):
    """
    The part of `twisted.web.server.Request` that we use.
    """

    @property
    def content(self) -> IO[bytes] | None: ...
    @property
    def finished(self) -> int | bool: ...
    @property
    def requestHeaders(self) -> Headers: ...
    @property
    def responseHeaders(self) -> Headers: ...

    def write(self, data: bytes) -> None: ...
    def finish(self) -> None: ...
    def registerProducer(self, producer: object, streaming: bool) -> None: ...
    def unregisterProducer(self) -> None: ...
    def getHost(self) -> IAddress: ...


class _Mode(Enum):
    # We don't know yet what the TCP peer wants to speak.
    UNKNOWN = auto()
    # Flash Player asked for a socket policy file.
    POLICY_FILE = auto()
    # Length-prefixed frames over TCP, for the Flash socket transport.
    INT32 = auto()
    HTTP = auto()


# Sent as the first frame over HTTP transports, to defeat JSON hijacking-style
# attacks that try to load the response as a script.
HTTP_RESPONSE_PREAMBLE = CommentFrame(";)]}")

_POLICY_FILE_REQUEST = b"<policy-file-request/>\x00"
_INT32_MODE_REQUEST = b"<int32/>\n"

# `_last_sack_seen_by_client` is this after we wrote any SACK to the client.
_DONT_WRITE_SACK = sentinel("_DONT_WRITE_SACK")


@implementer(IPushProducer, IPullProducer)
class ServerTransport(TwistedProtocol):
    """
    Private.  Use `ServerTransportFactory` or `WebPort`, which create these.

    Methods with camelCase names implement Twisted interfaces; the rest
    implement `ServerTransportLike` for `ServerStream`.
    """

    max_length = 1024 * 1024

    def __init__(
        self,
        clock: Clock,
        stream_tracker: StreamTrackerLike,
        policy_with_null: bytes = b"\x00",
    ) -> None:
        self._clock = clock
        self._stream_tracker = stream_tracker
        self._policy_with_null = policy_with_null

        self._mode = _Mode.UNKNOWN
        # Exactly one of these is set (once we know which it is).
        self._tcp: _TcpTransport | None = None
        self._request: _Request | None = None
        self._request_aborted = False
        self._wrote_http_preamble = False

        # Buffers data while we determine the mode.
        self._initial_buffer = b""
        self._parser: Decoder | None = None
        self._to_send = bytearray()

        # Not None if we are attached to a stream (i.e. have called
        # `transport_online`, or are calling it right now).
        self._stream: ServerStreamLike | None = None
        self._terminating = False
        # True while we're calling the stream, which can call us back.
        self._calling_stream = False
        self._sack_dirty = False
        self._received_counter = -1
        self._peer_seq_num = -1
        self.our_seq_num = -1
        self._last_start: int | None = None

        # These come from the hello frame.
        self.stream_id: str | None = None
        self.transport_number: int | None = None
        self._wants_strings = False
        self._last_sack_seen_by_client: SACK | _DONT_WRITE_SACK = _DONT_WRITE_SACK
        self._max_inactivity: int | None = None
        # False until we get a hello frame, so that a request from a client
        # that fails to send one doesn't get "stuck".
        self._streaming_response = False

        self._producer: PausableProducer | None = None
        self._paused = False

        self._max_open_dc: DelayedCall | None = None
        self._heartbeat_dc: DelayedCall | None = None

    def __repr__(self) -> str:
        return (
            f"<{type(self).__name__} at {id(self):#x} "
            f"terminating={self._terminating}, stream={self._stream!r}, "
            f"paused={self._paused}, our_seq_num={self.our_seq_num}>"
        )

    def is_attached(self) -> bool:
        """
        Is this transport attached to a `ServerStream`?  Always `False` after
        `ServerStream.transport_offline`.
        """
        return self._stream is not None

    # --- Writing ------------------------------------------------------------------

    def _write(self, data: bytes) -> None:
        if self._request is not None:
            self._request.write(data)
        else:
            assert self._tcp is not None
            self._tcp.write(data)

    def _encode_frame(self, frame: Frame) -> bytes:
        assert self._parser is not None
        return self._parser.encode(frame.encode())

    def _append_frame(self, frame: Frame) -> None:
        self._to_send += self._encode_frame(frame)

    def _maybe_write_to_peer(self) -> None:
        """
        Write the buffered frames to the peer, and terminate the transport if
        `_terminating`.
        """
        if self._calling_stream:
            return

        # If this isn't a streaming response, we have to terminate after
        # writing anything.
        if self._to_send and not self._streaming_response and not self._terminating:
            self._write_termination_frames()
            # Just in case we ever have a non-HTTP non-streaming response...
            if self._mode is not _Mode.HTTP:
                self._append_frame(YouCloseItFrame())
            self._terminating = True

        if self._to_send:
            to_send, self._to_send = bytes(self._to_send), bytearray()
            # Heartbeats are sent only when there's no other S2C activity.
            self._reset_heartbeat()

            if self._request is not None and not self._wrote_http_preamble:
                preamble = self._encode_frame(HTTP_RESPONSE_PREAMBLE)
                if self._terminating:
                    self._request.responseHeaders.setRawHeaders(
                        "content-length", [str(len(preamble) + len(to_send))]
                    )
                self._request.write(preamble)
                self._wrote_http_preamble = True
            self._write(to_send)

        if self._terminating:
            self._cancel_timers()
            # Tell the stream that this transport is offline.  (Whether we
            # still have a TCP connection to the peer is irrelevant.)
            if self._stream is not None:
                self._stream.transport_offline(self)
                self._stream = None
            if (
                self._request is not None
                and not self._request_aborted
                and not self._request.finished
            ):
                self._request.finish()
            # TODO: for TCP, close the connection ourselves in 5-10 seconds.

    def _cancel_timers(self) -> None:
        for dc in (self._max_open_dc, self._heartbeat_dc):
            if dc is not None and dc.active():
                dc.cancel()
        self._max_open_dc = self._heartbeat_dc = None

    def _write_termination_frames(self) -> None:
        if self._stream is not None:
            # Always write a SackFrame, to avoid a complicated scenario where
            # the client creates a useless primary transport that is closed
            # quickly:
            # 1) Client has a long-poll primary open; client app sends a string.
            # 2) Client creates a secondary transport; server reacts to string.
            # 3) Server sends a string over primary and closes primary.
            # 4) Client receives string/close over primary before receiving
            #    SackFrame/close over secondary.
            # 5) Client creates a new primary with a lastSackSeenByClient that
            #    does not include the SackFrame that server sent over secondary.
            # 6) Server thinks client needs a SackFrame because
            #    lastSackSeenByClient is older than expected.  Server writes
            #    SackFrame/close to the primary; client soon creates a new
            #    primary with an up-to-date lastSackSeenByClient.
            self._append_sack()
            self._append_frame(StreamStatusFrame(self._stream.last_sack_seen_by_server))

    def _close(self, kill_reason: KillReason | None = None) -> None:
        assert not self._terminating, self
        self._write_termination_frames()
        if kill_reason is not None:
            self._append_frame(TransportKillFrame(kill_reason))
        if self._mode is not _Mode.HTTP:
            self._append_frame(YouCloseItFrame())
        self._terminating = True
        self._maybe_write_to_peer()

    def _append_sack(self) -> None:
        assert self._stream is not None
        self._append_frame(SackFrame(self._stream.get_sack()))
        self._sack_dirty = False
        # We no longer need to write the "initial SACK" to the client.
        self._last_sack_seen_by_client = _DONT_WRITE_SACK

    # --- ServerTransportLike ------------------------------------------------------

    def close_gently(self) -> None:
        self._close()

    def caused_rwin_overflow(self) -> None:
        self._close(KillReason.RWIN_OVERFLOW)

    def write_reset(self, reason_string: str, application_level: bool) -> None:
        assert not self._terminating, self
        if self._sack_dirty:
            self._append_sack()
        # Because it's a reset, there's no need to send a StreamStatusFrame.
        self._append_frame(ResetFrame(reason_string, application_level))
        if self._mode is not _Mode.HTTP:
            self._append_frame(YouCloseItFrame())
        self._terminating = True
        self._maybe_write_to_peer()

    def write_strings(self, queue: Queue, start: int) -> None:
        # A terminating transport already went offline.
        assert not self._terminating, self
        # It's a bug to write strings before we received the hello frame.
        assert self._received_counter > -1, self._received_counter

        if self._sack_dirty:
            self._append_sack()

        # If `start` went down, the client lost strings that were sent over an
        # older transport; see test_write_strings_connection_interleaving.
        if self._last_start is None or start < self._last_start:
            self.our_seq_num = -1
            self._last_start = start

        # Even if there's a lot in the queue, write everything.
        for seq_num, string in queue.iter_items(max(start, self.our_seq_num + 1)):
            if self.our_seq_num == -1 or self.our_seq_num + 1 != seq_num:
                self._append_frame(SeqNumFrame(seq_num))
            self._append_frame(StringFrame(string))
            self.our_seq_num = seq_num
        self._maybe_write_to_peer()

    def get_info(self) -> TransportInfo:
        assert self.transport_number is not None
        return TransportInfo(
            transport_number=self.transport_number,
            is_primary=self._wants_strings,
            streaming_from_peer=self.is_streaming_from_peer(),
            streaming_to_peer=self.is_streaming_to_peer(),
            host=self.get_host(),
            request_headers=self._request.requestHeaders
            if self._request is not None
            else None,
        )

    def is_http(self) -> bool:
        """
        Raises `RuntimeError` if we don't know yet.
        """
        if self._request is None and self._tcp is None:
            raise RuntimeError("Don't yet know whether this is an HTTP transport")
        return self._request is not None

    def is_streaming_from_peer(self) -> bool:
        """
        Can the peer send us data more than once over this transport?
        """
        return not self.is_http()

    def is_streaming_to_peer(self) -> bool:
        """
        Can we send the peer data more than once over this transport?
        """
        return self._streaming_response

    def get_host(self) -> IAddress:
        writable = self._request or self._tcp
        assert writable is not None
        return writable.getHost()

    # --- Timers -------------------------------------------------------------------

    def _exceeded_max_open_time(self) -> None:
        self._max_open_dc = None
        if self.is_attached():
            self.close_gently()

    def _append_heartbeat(self) -> None:
        self._append_frame(CommentFrame("beat"))

    def _write_heartbeat(self) -> None:
        self._heartbeat_dc = None
        self._append_heartbeat()
        # Because there's now something to send, this resets the heartbeat.
        self._maybe_write_to_peer()

    def _reset_heartbeat(self) -> None:
        if self._heartbeat_dc is not None and self._heartbeat_dc.active():
            self._heartbeat_dc.cancel()
        self._heartbeat_dc = None
        # None before the hello frame; 0 if the client doesn't want heartbeats.
        if self._max_inactivity:
            self._heartbeat_dc = self._clock.callLater(
                self._max_inactivity, self._write_heartbeat
            )

    # --- Reading ------------------------------------------------------------------

    def _write_initial_frames(
        self, stream: ServerStreamLike, request_new_stream: bool
    ) -> None:
        assert not self._terminating, self
        if request_new_stream:
            # If we send a StreamCreatedFrame, it *must* be the first frame,
            # or the client might get into an inconsistent state if the
            # transport disconnects after an earlier frame.
            self._append_frame(StreamCreatedFrame())

        # Write the current SACK if the client has an out-of-date idea of it.
        # (We can't always send it, because long-polling transports must close
        # right after sending anything.)
        if self._last_sack_seen_by_client is not _DONT_WRITE_SACK:
            current_sack = stream.get_sack()
            if current_sack != self._last_sack_seen_by_client:
                self._append_frame(SackFrame(current_sack))

    def _handle_hello_frame(
        self, hello: HelloFrame, more_frames: Sequence[bytes]
    ) -> None:
        """
        Raises `NoSuchStream` if the stream doesn't exist (and the client
        didn't ask for a new one).
        """
        if self._mode is not _Mode.HTTP:
            # These options make sense only for HTTP; don't let clients use
            # them elsewhere.
            hello = dataclasses.replace(
                hello,
                streaming_response=True,
                max_receive_bytes=MAX_SAFE_INT,
                max_open_time=None,
            )

        self.stream_id = hello.stream_id
        self.transport_number = hello.transport_number
        self._streaming_response = hello.streaming_response
        self._max_inactivity = hello.max_inactivity
        self._last_sack_seen_by_client = hello.last_sack_seen_by_client
        self._wants_strings = hello.wants_strings
        # TODO: implement need_padding_bytes and max_receive_bytes.
        if hello.max_open_time is not None:
            self._max_open_dc = self._clock.callLater(
                hello.max_open_time, self._exceeded_max_open_time
            )

        # A hello with request_new_stream doesn't always create a new stream:
        # the response to the request that created it may have been lost.
        stream: ServerStreamLike
        if hello.request_new_stream:
            try:
                stream = self._stream_tracker.build_stream(hello.stream_id)
            except StreamAlreadyExists:
                stream = self._stream_tracker.get_stream(hello.stream_id)
        else:
            stream = self._stream_tracker.get_stream(hello.stream_id)

        self._write_initial_frames(stream, hello.request_new_stream)
        # Do this before `transport_online`: if the SACK is bad, the stream
        # never learns about this transport, and if this transport succeeds
        # another one, the SACK removes strings from the stream's queue while
        # keeping it in "pretend acked" mode.
        if hello.sack is not None and stream.sack_received(hello.sack):
            self._close(KillReason.ACKED_UNSENT_STRINGS)
            return

        self._stream = stream
        self._calling_stream = True
        stream.transport_online(
            self,
            hello.wants_strings,
            hello.succeeds_transport if hello.wants_strings else None,
        )
        self._calling_stream = False
        # A lot can happen underneath `transport_online`: it may have created a
        # protocol, which may even have reset the stream.
        if self._terminating:
            return

        self._frames_received(more_frames)
        if self._terminating:
            return

        if self._mode is _Mode.HTTP and not self._wants_strings:
            self.close_gently()
            return

        if self._max_inactivity:
            self._append_heartbeat()
        self._reset_heartbeat()
        self._maybe_write_to_peer()

    def _frames_received(self, frames: Sequence[bytes]) -> None:
        # Deliver the strings in a batch, to reduce the number of SACKs we
        # write.  This adds no latency.
        bunched_strings: list[tuple[int, str]] = []

        def deliver_strings() -> None:
            nonlocal bunched_strings
            if not bunched_strings:
                return
            assert self._stream is not None
            # Almost always already sorted, so this is fast with Timsort.
            bunched_strings.sort(key=itemgetter(0))
            strings, bunched_strings = bunched_strings, []

            # `_sack_dirty` makes us write fewer SackFrames, while making sure
            # that a SackFrame is written *before* any StringFrames that the
            # stream writes while we call it.
            assert not self._sack_dirty, self
            self._sack_dirty = True
            self._calling_stream = True
            try:
                self._stream.strings_received(self, strings)
            finally:
                self._calling_stream = False
            # Underneath that call, a lot can happen, including calls to our own
            # `write_reset` or `close_gently` or `write_strings`.
            if not self._terminating and self._sack_dirty:
                self._append_sack()

        def kill(reason: KillReason) -> None:
            # Deliver the strings that preceded the problem first.
            deliver_strings()
            if not self._terminating:
                self._close(reason)

        for i, raw_frame in enumerate(frames):
            if self._terminating:
                break
            self._received_counter += 1
            try:
                frame = decode_frame_from_client(raw_frame)
            except InvalidFrame:
                kill(KillReason.INVALID_FRAME_TYPE_OR_ARGUMENTS)
                break

            # The first frame must be a hello frame, and only the first.
            if self._received_counter == 0:
                if not isinstance(frame, HelloFrame):
                    kill(KillReason.INVALID_FRAME_TYPE_OR_ARGUMENTS)
                    break
                try:
                    # This processes the rest of the frames, too.
                    self._handle_hello_frame(frame, frames[i + 1 :])
                except NoSuchStream:
                    self._close(KillReason.STREAM_ATTACH_FAILURE)
                break

            assert self._stream is not None
            match frame:
                case StringFrame(string):
                    # In the future, we could support switching to strings
                    # with a wider character range mid-stream.
                    if not is_restricted_string(string):
                        kill(KillReason.INVALID_FRAME_TYPE_OR_ARGUMENTS)
                        break
                    self._peer_seq_num += 1
                    bunched_strings.append((self._peer_seq_num, string))

                case SackFrame(sack):
                    self._calling_stream = True
                    bad_sack = self._stream.sack_received(sack)
                    self._calling_stream = False
                    if bad_sack:
                        kill(KillReason.ACKED_UNSENT_STRINGS)
                        break

                case SeqNumFrame(seq_num):
                    self._peer_seq_num = seq_num - 1

                case ResetFrame(reason_string, application_level):
                    # Deliver the strings before processing the reset.  This
                    # is an implementation detail that may change.
                    deliver_strings()
                    if not self._terminating:
                        self._calling_stream = True
                        self._stream.reset_from_peer(reason_string, application_level)
                        self._calling_stream = False
                    # Frames after a reset frame are ignored.
                    break

                case HelloFrame():
                    # A second hello frame
                    kill(KillReason.INVALID_FRAME_TYPE_OR_ARGUMENTS)
                    break

        if not self._terminating:
            deliver_strings()
        self._maybe_write_to_peer()

    # --- Twisted's IProtocol ------------------------------------------------------

    @override
    def dataReceived(self, data: bytes) -> None:
        if self._terminating:
            # Ignore data received while terminating.
            return

        # Before we can speak "Minerva", we need to determine which mode the
        # TCP peer wants us to speak in.
        if self._mode is _Mode.UNKNOWN:
            assert self._tcp is not None
            self._initial_buffer += data
            if self._initial_buffer.startswith(_POLICY_FILE_REQUEST):
                self._mode = _Mode.POLICY_FILE
                self._initial_buffer = b""
                self._tcp.write(self._policy_with_null)
                self._terminating = True
                # No need to close the connection: "The server must send a null
                # byte to terminate a policy file and may then close the
                # connection; if the server does not close the connection, the
                # Flash Player will do so upon receiving the terminating null
                # byte."  TODO: close it in 5-10 seconds if the client doesn't.
                return
            elif self._initial_buffer.startswith(_INT32_MODE_REQUEST):
                self._mode = _Mode.INT32
                data = self._initial_buffer[len(_INT32_MODE_REQUEST) :]
                self._initial_buffer = b""
                self._parser = Int32StringDecoder(max_length=self.max_length)
                # TODO: implement <int32-zlib/>, but beware of zlib bombs.
            elif len(self._initial_buffer) >= 512:
                # We need far less than 512 bytes, but stay on the safe side.
                # We can't send any frames, so just RST the peer; it doesn't
                # look like a well-behaved client anyway.
                self._terminating = True
                self._tcp.abortConnection()
                return
            else:
                return

        assert self._parser is not None
        try:
            frames = self._parser.feed(data)
        except FrameTooLong:
            self._close(KillReason.FRAME_CORRUPTION)
        else:
            self._frames_received(frames)

        if self._stream is not None:
            self._stream.last_received = self._clock.seconds()
        self._maybe_write_to_peer()

    @override
    def connectionMade(self) -> None:
        # The (untyped) `self.transport` is a TCP transport.
        self._tcp = cast(_TcpTransport, self.transport)
        # We don't do this for HTTP transports, because that requires digging
        # into private state, and can affect non-Minerva requests on the same
        # HTTP connection.  Applications that demand low latency should set
        # TCP_NODELAY on all of their HTTP connections.
        self._tcp.setTcpNoDelay(True)
        logger.info("Connection made for %r", self)

    @override
    def connectionLost(self, reason: Failure = connectionDone) -> None:
        logger.info("Connection lost for %r: %s", self, reason.getErrorMessage())
        if self._stream is not None:
            # Give the client some time to attach a new transport; otherwise
            # `disconnect_inactive` would reset streams that just happened to
            # have no transports at that instant.
            self._stream.last_received = self._clock.seconds()
        # It might already be terminating, but often not.
        self._terminating = True
        self._maybe_write_to_peer()

    # --- HTTP ---------------------------------------------------------------------

    def request_started(self, request: _Request) -> None:
        """
        Called by `minerva.web.HttpIo` with an HTTP POST request.
        """
        assert self._mode is _Mode.UNKNOWN, self._mode
        self._mode = _Mode.HTTP
        self._parser = DelimitedStringDecoder(max_length=self.max_length)
        self._request = request

        body = request.content.read() if request.content is not None else b""
        # Proxies *might* strip whitespace around the request body.
        if body and not body.endswith(b"\n"):
            logger.info("Unusual: POST body did not end in newline for %r", request)
        if b"\r\n" in body:
            body = body.replace(b"\r\n", b"\n")
            logger.info("Unusual: found a CRLF in POST body for %r", request)

        headers = request.responseHeaders
        # Headers similar to the ones Gmail sends, to prevent caching.
        headers.setRawHeaders(
            "cache-control", ["no-cache, no-store, max-age=0, must-revalidate"]
        )
        headers.setRawHeaders("pragma", ["no-cache"])
        headers.setRawHeaders("expires", ["-1"])
        # "For Webkit browsers, it's critical to specify a Content-Type of
        # "text/plain" or "application/x-javascript" when returning script
        # content to an XHR for progressive handling."
        # -- http://www.kylescholz.com/blog/2010/01/progressive_xmlhttprequest_1.html
        headers.setRawHeaders("content-type", ["text/plain"])

        self.dataReceived(body)

    def request_aborted(self, reason: Failure) -> None:
        """
        Called if the client closed the connection before we finished the
        request.
        """
        logger.info("Peer aborted request for %r: %s", self, reason.getErrorMessage())
        self._request_aborted = True
        # It might already be terminating, but often not.
        self._terminating = True
        self._maybe_write_to_peer()

    # --- Producers ----------------------------------------------------------------

    def registerProducer(self, producer: PausableProducer, streaming: bool) -> None:
        """
        Called by the `ServerStream`.
        """
        if self._producer is not None:
            raise RuntimeError(
                f"Cannot register producer {producer!r}, because producer "
                f"{self._producer!r} was never unregistered."
            )
        self._producer = producer
        if streaming and self._paused:
            producer.pauseProducing()
        writable = self._request or self._tcp
        assert writable is not None
        # We are the producer for the underlying TCP transport or request.
        writable.registerProducer(self, streaming)
        self._maybe_write_to_peer()

    def unregisterProducer(self) -> None:
        """
        Called by the `ServerStream`.
        """
        self._producer = None
        writable = self._request or self._tcp
        assert writable is not None
        writable.unregisterProducer()

    # Called by Twisted.  We trust Twisted to call this only if we registered
    # as a push producer.
    def pauseProducing(self) -> None:
        self._paused = True
        if self._producer is not None:
            self._producer.pauseProducing()

    def resumeProducing(self) -> None:
        self._paused = False
        if self._producer is not None:
            self._producer.resumeProducing()

    def stopProducing(self) -> None:
        # Our connectionLost logic eventually deals with the producers.
        pass


class ServerTransportFactory(Factory[ServerTransport]):
    """
    Listen on TCP with this factory if you want Minerva clients to be able to
    connect with their Flash socket transport.
    """

    def __init__(
        self,
        clock: Clock,
        stream_tracker: StreamTrackerLike,
        policy_string: str | None = None,
    ) -> None:
        """
        `policy_string` is a Flash/Silverlight socket policy file, sent in
        response to a `<policy-file-request/>`.
        """
        self._clock = clock
        self.stream_tracker = stream_tracker
        self.set_policy_string(policy_string)

    def set_policy_string(self, policy_string: str | None) -> None:
        """
        Set the Flash/Silverlight socket policy.  Already-open connections
        will serve the old policy (though this is of little consequence).
        """
        if policy_string is None:
            policy_string = ""
        if not isinstance(policy_string, str):
            raise TypeError(f"policy_string must be a str, was {policy_string!r}")
        # NULL terminates the policy file.
        if "\x00" in policy_string:
            raise ValueError("policy_string cannot contain NULL")
        # TODO: verify that Flash Player closes the connection when it sees
        # just a NULL.
        self._policy_with_null = policy_string.encode("utf-8") + b"\x00"

    @override
    def buildProtocol(self, addr: IAddress | None) -> ServerTransport:
        transport = ServerTransport(
            self._clock, self.stream_tracker, self._policy_with_null
        )
        transport.factory = self
        return transport
