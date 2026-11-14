"""
Tests for `minerva.web`: the HTTP transport (`HttpIo` and `ServerTransport`'s
HTTP support), `XDRFrame`, and `WebPort`.
"""

import json
from typing import Any, cast

import pytest
from hypothesis import given
from hypothesis import strategies as st
from twisted.internet.error import ConnectionLost
from twisted.internet.task import Clock
from twisted.internet.testing import StringTransport
from twisted.python.failure import Failure
from twisted.web.resource import IResource, Resource, getChildForRequest
from twisted.web.server import NOT_DONE_YET, Site
from twisted.web.static import File, StaticProducer

from minerva.decoders import DelimitedStringDecoder
from minerva.frames import (
    Frame,
    KillReason,
    ResetFrame,
    SackFrame,
    SeqNumFrame,
    ServerFrame,
    StreamCreatedFrame,
    StreamStatusFrame,
    StringFrame,
    TransportKillFrame,
    decode_frame_from_server,
)
from minerva.stream import ServerStream, StreamTracker
from minerva.transport import HTTP_RESPONSE_PREAMBLE
from minerva.web import (
    BetterResource,
    HttpIo,
    WebPort,
    XDRFrame,
    htmldumps,
    put_child,
)
from minerva.window import SACK
from tests.helpers import make_http_hello
from tests.mocks import (
    DummyStreamTracker,
    FakeRequest,
    MockProducer,
    MockServerStream,
    MockStringFactory,
)

STREAM_ID = "x" * 26

# What a non-streaming response ends with.
CLOSING = [SackFrame(SACK(-1)), StreamStatusFrame(SACK(-1))]


def post(resource: HttpIo, *frames: Frame, separator: bytes = b"\n") -> FakeRequest:
    """
    POST `frames` (each followed by `separator`) to `resource`.
    """
    request = FakeRequest(b"".join(f.encode() + separator for f in frames))
    assert resource.render(request) == NOT_DONE_YET
    return request


def response_frames(request: FakeRequest) -> list[ServerFrame]:
    *frames, last = request.written_bytes().split(b"\n")
    assert last == b""
    return [decode_frame_from_server(f) for f in frames]


def content_length(request: FakeRequest) -> int | None:
    values = request.responseHeaders.getRawHeaders(b"content-length")
    if values is None:
        return None
    [value] = values
    return int(value)


def encoded_length(frames: list[Any]) -> int:
    return sum(len(DelimitedStringDecoder.encode(f.encode())) for f in frames)


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def factory() -> MockStringFactory:
    return MockStringFactory()


@pytest.fixture
def mock_tracker(clock: Clock, factory: MockStringFactory) -> DummyStreamTracker:
    return DummyStreamTracker(clock, factory)


@pytest.fixture
def tracker(clock: Clock, factory: MockStringFactory) -> StreamTracker:
    return StreamTracker(clock, factory, inactive_check_interval=None)


@pytest.fixture
def mock_resource(clock: Clock, mock_tracker: DummyStreamTracker) -> HttpIo:
    return HttpIo(clock, mock_tracker)


@pytest.fixture
def resource(clock: Clock, tracker: StreamTracker) -> HttpIo:
    return HttpIo(clock, tracker)


def create_stream(resource: HttpIo, streaming: bool) -> None:
    """
    Make a request that only creates the stream.
    """
    request = post(
        resource, make_http_hello(wants_strings=True, streaming_response=streaming)
    )
    # A non-streaming request is finished right away, because the server
    # sent a StreamCreatedFrame.
    assert request.finished == (0 if streaming else 1)
    expected = [HTTP_RESPONSE_PREAMBLE, StreamCreatedFrame()]
    assert response_frames(request) == (expected if streaming else expected + CLOSING)


@pytest.mark.parametrize("separator", [b"\n", b"\r\n"])
@pytest.mark.parametrize("streaming", [False, True])
def test_body_frames_passed_to_stream(
    mock_resource: HttpIo,
    mock_tracker: DummyStreamTracker,
    separator: bytes,
    streaming: bool,
) -> None:
    """
    The frames in the POST body go to the stream, even with CRLF delimiters.
    """
    request = post(
        mock_resource,
        make_http_hello(wants_strings=True, streaming_response=streaming),
        StringFrame("string0"),
        StringFrame("string1"),
        StringFrame("string2"),
        separator=separator,
    )

    expected: list[Any] = [
        HTTP_RESPONSE_PREAMBLE,
        StreamCreatedFrame(),
        SackFrame(SACK(2)),
    ]
    if not streaming:
        expected += [SackFrame(SACK(2)), StreamStatusFrame(SACK(-1))]
    assert response_frames(request) == expected
    assert request.finished == (0 if streaming else 1)

    stream: MockServerStream = mock_tracker.get_stream(STREAM_ID)
    [transport] = stream.all_seen_transports
    assert stream.get_new() == [
        ["transport_online", transport, True, None],
        [
            "strings_received",
            transport,
            [(0, "string0"), (1, "string1"), (2, "string2")],
        ],
        *([] if streaming else [["transport_offline", transport]]),
    ]


def test_body_without_final_newline(
    mock_resource: HttpIo, mock_tracker: DummyStreamTracker
) -> None:
    """
    If the POST body doesn't end in a newline, the unterminated last "line"
    is ignored.
    """
    hello = make_http_hello(wants_strings=True, streaming_response=True)
    request = FakeRequest(
        b"\n".join(f.encode() for f in (hello, StringFrame("s0"), StringFrame("s1")))
    )
    mock_resource.render(request)

    stream: MockServerStream = mock_tracker.get_stream(STREAM_ID)
    [transport] = stream.all_seen_transports
    assert stream.get_new() == [
        ["transport_online", transport, True, None],
        ["strings_received", transport, [(0, "s0")]],
    ]


def send_another_string(
    clock: Clock,
    stream: ServerStream,
    request: FakeRequest,
    streaming: bool,
    before: list[Any],
) -> None:
    """
    A string sent after a non-streaming response finished is not written.
    """
    stream.send_string("extra_string")
    clock.advance(0.001)
    if streaming:
        assert response_frames(request) == [*before, StringFrame("extra_string")]
        assert request.finished == 0
    else:
        assert response_frames(request) == before
        assert request.finished == 1


@pytest.mark.parametrize("streaming", [False, True])
def test_s2c_strings_already_available(
    clock: Clock, resource: HttpIo, tracker: StreamTracker, streaming: bool
) -> None:
    """
    If S2C strings are waiting when a request arrives, it gets them and a
    SACK.  A non-streaming response is then finished (with a correct
    Content-Length); a streaming one is kept open.
    """
    stream = tracker.build_stream(STREAM_ID)
    stream.send_string("string0")
    stream.send_string("string1")

    request = post(
        resource,
        make_http_hello(wants_strings=True, streaming_response=streaming),
        StringFrame("string0"),
    )
    expected: list[Any] = [
        HTTP_RESPONSE_PREAMBLE,
        StreamCreatedFrame(),
        SeqNumFrame(0),
        StringFrame("string0"),
        StringFrame("string1"),
        SackFrame(SACK(0)),
    ]
    if not streaming:
        expected += [SackFrame(SACK(0)), StreamStatusFrame(SACK(-1))]
    assert response_frames(request) == expected
    assert request.finished == (0 if streaming else 1)
    assert content_length(request) == (None if streaming else encoded_length(expected))

    send_another_string(clock, stream, request, streaming, expected)


@pytest.mark.parametrize("streaming", [False, True])
def test_s2c_strings_soon_available(
    clock: Clock, resource: HttpIo, tracker: StreamTracker, streaming: bool
) -> None:
    """
    A request waits until S2C strings are available.  A non-streaming
    response is finished after writing them; a streaming one is kept open.
    """
    create_stream(resource, streaming)
    stream = tracker.get_stream(STREAM_ID)

    request = post(
        resource,
        make_http_hello(
            request_new_stream=False, wants_strings=True, streaming_response=streaming
        ),
    )
    assert response_frames(request) == []

    stream.send_string("string0")
    stream.send_string("string1")
    clock.advance(0.001)
    expected: list[Any] = [
        HTTP_RESPONSE_PREAMBLE,
        SeqNumFrame(0),
        StringFrame("string0"),
        StringFrame("string1"),
    ]
    if not streaming:
        expected += CLOSING
    assert response_frames(request) == expected
    assert request.finished == (0 if streaming else 1)
    assert content_length(request) == (None if streaming else encoded_length(expected))

    send_another_string(clock, stream, request, streaming, expected)


def test_response_headers(mock_resource: HttpIo) -> None:
    """
    The response has headers that prevent caching, and a Content-Type that
    works around bugs in browsers and anti-virus products.
    """
    request = FakeRequest(b"")
    mock_resource.render(request)
    headers = dict(request.responseHeaders.getAllRawHeaders())
    assert headers[b"Pragma"] == [b"no-cache"]
    assert headers[b"Cache-Control"] == [
        b"no-cache, no-store, max-age=0, must-revalidate"
    ]
    assert headers[b"Expires"] == [b"-1"]
    # Possibly prevents initial buffering of streaming responses in WebKit.
    assert headers[b"Content-Type"] == [b"text/plain"]
    # Without this, Chrome buffers the start of the response for MIME
    # sniffing, and HTTP streaming stalls.
    assert headers[b"X-Content-Type-Options"] == [b"nosniff"]


def test_client_aborts_request(
    mock_resource: HttpIo, mock_tracker: DummyStreamTracker
) -> None:
    """
    If the client aborts the request, the transport goes offline.
    """
    # streaming_response, so that the StreamCreatedFrame doesn't finish the
    # request.
    request = post(
        mock_resource, make_http_hello(wants_strings=True, streaming_response=True)
    )
    stream: MockServerStream = mock_tracker.get_stream(STREAM_ID)
    [transport] = stream.all_seen_transports
    assert stream.get_new() == [["transport_online", transport, True, None]]

    # With a real Request, this would be request.connectionLost(...).
    request.processingFailed(Failure(ConnectionLost()))
    assert stream.get_new() == [["transport_offline", transport]]
    # The request was already disconnected, so it wasn't finished.
    assert request.finished == 0


@pytest.mark.parametrize("streaming", [False, True])
def test_non_primary_transport_closed(resource: HttpIo, streaming: bool) -> None:
    """
    A transport that doesn't want strings is closed right away, even if
    there's nothing to write, and even if `streaming_response`.
    """
    create_stream(resource, streaming=False)
    request = post(
        resource,
        make_http_hello(request_new_stream=False, streaming_response=streaming),
    )
    expected = [HTTP_RESPONSE_PREAMBLE, *CLOSING]
    assert response_frames(request) == expected
    assert request.finished == 1
    # Content-Length is there even if streaming.
    assert content_length(request) == encoded_length(expected)


def test_max_open_time(clock: Clock, resource: HttpIo) -> None:
    """
    A request is closed `max_open_time` seconds after its hello frame
    arrives.
    """
    create_stream(resource, streaming=False)
    request = post(
        resource,
        make_http_hello(
            request_new_stream=False,
            transport_number=1,
            wants_strings=True,
            max_open_time=2,
        ),
    )
    assert response_frames(request) == []
    clock.advance(2)
    assert response_frames(request) == [HTTP_RESPONSE_PREAMBLE, *CLOSING]
    assert request.finished == 1


@pytest.mark.parametrize("client_resets_immediately", [True, False])
def test_secondary_transport_terminated_in_frames_received(
    clock: Clock, client_resets_immediately: bool
) -> None:
    """
    A regression test for a short-lived bug where `_terminating` wasn't
    checked before calling `close_gently` (see also
    `test_reset_in_string_received`).
    """
    factory = MockStringFactory(call_from=("string_received",), call_what=("reset",))
    resource = HttpIo(
        clock, StreamTracker(clock, factory, inactive_check_interval=None)
    )
    create_stream(resource, streaming=False)

    frames: list[Frame] = [
        # The bug happened only when the transport did not want strings.
        make_http_hello(request_new_stream=False),
        StringFrame("string0"),
        StringFrame("string1"),
        StringFrame("string2"),
    ]
    if client_resets_immediately:
        # This is ignored.
        frames.append(ResetFrame("client's reason", True))
    request = post(resource, *frames)

    assert request.finished == 1
    assert response_frames(request) == [
        HTTP_RESPONSE_PREAMBLE,
        SackFrame(SACK(2)),
        # Because it's a reset, there's no StreamStatusFrame.
        ResetFrame("reset forced by mock protocol", True),
    ]
    assert factory.instance.get_new()[1:] == [
        ["string_received", "string0"],
        ["stream_reset", "reset forced by mock protocol", True],
    ]


class TestHtmlDumps:
    @given(
        st.recursive(st.none() | st.booleans() | st.integers() | st.text(), st.lists)
    )
    def test_safe_in_script_and_still_json(self, value: object) -> None:
        """
        The output can't close a script element or open an HTML comment, and
        it still decodes to the same value.
        """
        dumped = str(htmldumps(value))
        assert not {"<", ">", "&"} & set(dumped)
        assert json.loads(dumped) == value

    def test_script_tag(self) -> None:
        assert json.loads(htmldumps("</script>")) == "</script>"
        assert "</script>" not in htmldumps(["</script>"])


class TestXDRFrame:
    def render(self, xdrframe: XDRFrame, **args: bytes) -> FakeRequest:
        request = FakeRequest()
        request.method = b"GET"
        request.args = {k.encode(): [v] for k, v in args.items()}
        request.write(xdrframe.render(request))
        return request

    @pytest.mark.parametrize("dev_mode", [False, True])
    def test_render(self, dev_mode: bool) -> None:
        xdrframe = XDRFrame(frozenset(["example.com"]), dev_mode=dev_mode)
        request = self.render(xdrframe, id=b"frame123", domain=b"example.com")
        html = request.written_bytes().decode()
        assert request.responseCode is None  # 200
        assert 'var domain = "example.com";' in html
        assert '__xdrframe_setupXDRFrame("frame123");' in html
        if dev_mode:
            assert "goog.require('cw.net.XHRSlave');" in html
        else:
            assert '"/compiled_client/xdrframe.js?cb=' in html

    @pytest.mark.parametrize(
        "args",
        [
            {"id": b"frame<script>", "domain": b"example.com"},
            {"id": b"x" * 51, "domain": b"example.com"},
            {"id": b"frame123", "domain": b"evil.example"},
            {"id": b"frame123"},
        ],
    )
    def test_bad_request(self, args: dict[str, bytes]) -> None:
        request = self.render(XDRFrame(frozenset(["example.com"])), **args)
        assert request.responseCode == 400


class _Leaf(BetterResource):
    isLeaf = True

    def render_GET(self, request: FakeRequest) -> bytes:
        return b"leaf"


class _PlainLeaf(Resource):
    isLeaf = True

    def render_GET(self, request: FakeRequest) -> bytes:
        return b"plain leaf"


class TestBetterResource:
    @pytest.fixture
    def root(self) -> BetterResource:
        """
        /leaf/, /plain, /dir/leaf/, and /empty (which has no children).
        """
        root = BetterResource()
        put_child(root, b"leaf", _Leaf())
        put_child(root, b"plain", _PlainLeaf())
        directory = BetterResource()
        put_child(directory, b"", _Leaf())
        put_child(directory, b"leaf", _Leaf())
        put_child(root, b"dir", directory)
        put_child(root, b"empty", BetterResource())
        return root

    def get(self, root: Resource, uri: bytes) -> FakeRequest:
        """
        Return the request for `uri`, after `root` has responded to it.
        """
        request = FakeRequest()
        request.method = b"GET"
        request.uri = uri
        request.postpath = uri.partition(b"?")[0].split(b"/")[1:]
        result = getChildForRequest(root, request).render(request)
        # (Twisted's 404 page writes its response itself.)
        if isinstance(result, bytes):
            request.write(result)
        return request

    @pytest.mark.parametrize("uri", [b"/leaf/", b"/leaf/?a=1", b"/dir/", b"/dir/leaf/"])
    def test_served_at_the_url_with_a_final_slash(
        self, root: BetterResource, uri: bytes
    ) -> None:
        request = self.get(root, uri)
        assert request.responseCode is None  # 200
        assert request.written_bytes() == b"leaf"

    @pytest.mark.parametrize(
        ("uri", "location"),
        [
            (b"/leaf", b"/leaf/"),
            (b"/leaf?a=1&b=/", b"/leaf/?a=1&b=/"),
            (b"/dir", b"/dir/"),
            (b"/dir/leaf", b"/dir/leaf/"),
        ],
    )
    def test_redirects_to_the_url_with_a_final_slash(
        self, root: BetterResource, uri: bytes, location: bytes
    ) -> None:
        request = self.get(root, uri)
        assert request.responseCode == 301
        assert request.responseHeaders.getRawHeaders(b"location") == [location]

    @pytest.mark.parametrize(
        "uri",
        [
            b"/leaf/more",
            b"/leaf/more/",
            b"/leaf//",
            b"/dir/leaf/more",
            b"/plain/more",
            b"/nothing",
            b"/dir/nothing",
            # Not a redirect to /empty/, which doesn't exist.
            b"/empty",
            b"/empty/",
        ],
    )
    def test_not_found(self, root: BetterResource, uri: bytes) -> None:
        assert self.get(root, uri).responseCode == 404

    @pytest.mark.parametrize("uri", [b"/plain", b"/plain/"])
    def test_child_that_is_not_a_better_resource_is_not_redirected(
        self, root: BetterResource, uri: bytes
    ) -> None:
        request = self.get(root, uri)
        assert request.responseCode is None  # 200
        assert request.written_bytes() == b"plain leaf"

    @pytest.mark.parametrize(
        ("uri", "code"),
        [
            (b"/io", 301),
            (b"/io/more", 404),
            (b"/xdrframe", 301),
            (b"/xdrframe/more?id=f1&domain=example.com", 404),
        ],
    )
    def test_web_port(
        self, clock: Clock, mock_tracker: DummyStreamTracker, uri: bytes, code: int
    ) -> None:
        web_port = WebPort(clock, mock_tracker, allowed_domains=["example.com"])
        assert self.get(web_port, uri).responseCode == code


def test_web_port_children(clock: Clock, mock_tracker: DummyStreamTracker) -> None:
    web_port = WebPort(clock, mock_tracker, allowed_domains=["example.com"])
    children: dict[bytes, IResource] = web_port.children
    assert isinstance(children[b"io"], HttpIo)
    assert isinstance(children[b"xdrframe"], XDRFrame)
    assert isinstance(children[b"xdrframe_dev"], XDRFrame)
    for name in (b"FlashConnector.swf", b"minerva-client.js"):
        child = children[name]
        assert isinstance(child, File)
        assert child.exists()


@pytest.mark.parametrize("name", [b"FlashConnector.swf", b"minerva-client.js"])
@pytest.mark.parametrize("method", [b"GET", b"HEAD"])
def test_web_port_files_must_be_revalidated(
    clock: Clock, mock_tracker: DummyStreamTracker, name: bytes, method: bytes
) -> None:
    """
    The responses say that a cached copy of the client is stale at once, or
    a browser could keep running an old client after an upgrade.
    """
    request = FakeRequest()
    request.method = method
    request.postpath = [name]
    getChildForRequest(WebPort(clock, mock_tracker), request).render(request)
    # Close the file that a response to GET is being produced from.
    for registration in request.producers:
        assert registration is not None
        cast(StaticProducer, registration[0]).stopProducing()

    headers = request.responseHeaders
    assert headers.getRawHeaders(b"cache-control") == [b"max-age=0, private"]
    assert headers.getRawHeaders(b"expires") == [b"-1"]


@pytest.mark.parametrize("streaming", [False, True])
def test_get_info(resource: HttpIo, tracker: StreamTracker, streaming: bool) -> None:
    create_stream(resource, streaming=True)
    request = FakeRequest(
        make_http_hello(
            request_new_stream=False,
            transport_number=3,
            wants_strings=True,
            streaming_response=streaming,
        ).encode()
        + b"\n"
    )
    request.requestHeaders.setRawHeaders(b"user-agent", [b"test"])
    resource.render(request)
    stream = tracker.get_stream(STREAM_ID)
    transport = stream._primary_transport
    assert transport is not None
    info = transport.get_info()
    assert info.transport_number == 3
    assert info.is_primary is True
    assert info.streaming_from_peer is False
    assert info.streaming_to_peer is streaming
    assert info.request_headers is request.requestHeaders
    assert info.host == request.getHost()


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        (b"", KillReason.FRAME_CORRUPTION),
        (make_http_hello().encode(), KillReason.FRAME_CORRUPTION),  # unterminated
        (b"{" * 100, KillReason.FRAME_CORRUPTION),
        # An empty frame, which is invalid
        (b"\n", KillReason.INVALID_FRAME_TYPE_OR_ARGUMENTS),
    ],
    ids=["empty", "unterminated hello", "garbage", "empty frame"],
)
def test_body_without_complete_hello_is_answered(
    mock_resource: HttpIo, body: bytes, reason: KillReason
) -> None:
    """
    A request body is complete, so if it has no complete hello frame, the
    request is answered right away rather than left hanging.
    """
    request = FakeRequest(body)
    mock_resource.render(request)
    assert request.finished == 1
    assert response_frames(request)[-1] == TransportKillFrame(reason)


def test_upload_only_request_counts_as_activity(
    clock: Clock, resource: HttpIo, tracker: StreamTracker
) -> None:
    create_stream(resource, streaming=False)
    clock.advance(100)
    post(resource, make_http_hello(request_new_stream=False), StringFrame("still here"))
    assert tracker.get_stream(STREAM_ID).last_received == clock.seconds()


def test_request_finished_even_if_detaching_raises(
    mock_resource: HttpIo, mock_tracker: DummyStreamTracker
) -> None:
    request = post(
        mock_resource, make_http_hello(wants_strings=True, streaming_response=True)
    )
    stream: MockServerStream = mock_tracker.get_stream(STREAM_ID)
    [transport] = stream.all_seen_transports

    def broken(transport: object) -> None:
        raise ZeroDivisionError

    stream.transport_offline = broken  # ty: ignore[invalid-assignment]
    with pytest.raises(ZeroDivisionError):
        transport.close_gently()
    assert request.finished == 1


def test_client_aborts_streaming_request_with_producer(clock: Clock) -> None:
    """
    twisted.web drops a request's channel before telling us that the client
    went away.  With a producer registered, unregistering it from the aborted
    request used to raise, wedging the stream with a dead primary transport.
    (This needs a real Request and HTTPChannel; FakeRequest can't show it.)
    """
    tracker = StreamTracker(clock, MockStringFactory(), inactive_check_interval=None)
    root = Resource()
    put_child(root, b"io", HttpIo(clock, tracker))
    channel = Site(root).buildProtocol(None)
    assert channel is not None
    channel.makeConnection(StringTransport())
    body = make_http_hello(wants_strings=True, streaming_response=True).encode() + b"\n"
    channel.dataReceived(
        b"POST /io HTTP/1.1\r\nHost: x\r\nContent-Length: %d\r\n\r\n%s"
        % (len(body), body)
    )
    stream = tracker.get_stream(STREAM_ID)
    producer = MockProducer()
    stream.registerProducer(producer, streaming=True)

    channel.connectionLost(Failure(ConnectionLost()))
    assert stream._primary_transport is None
    assert producer.get_new() == ["pauseProducing"]
    # The stream still works when the client comes back.
    post(
        HttpIo(clock, tracker),
        make_http_hello(
            request_new_stream=False, wants_strings=True, streaming_response=True
        ),
    )
    assert stream._primary_transport is not None
    assert producer.get_new() == ["resumeProducing"]
