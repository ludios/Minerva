"""
Tests for `minerva.site`, the development server.
"""

import json
import re
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path

import pytest
from twisted.internet.task import Clock
from twisted.web.resource import Resource, getChildForRequest
from twisted.web.server import NOT_DONE_YET
from twisted.web.static import File

from minerva.demos import bskystream
from minerva.site import (
    DEMOS_STATIC_DIR,
    DemoFactory,
    DemoProtocol,
    WaitResource,
    _warn_about_setup,
    make_site,
    parse_args,
    parse_ranges,
    policy_file,
    restricted_string_alphabet,
)
from minerva.stream import ServerStream, StreamTracker
from minerva.web import RevalidatedFile, file_digest
from tests.mocks import DummySocketLikeTransport, FakeRequest, MockStringFactory


@pytest.fixture
def clock() -> Clock:
    return Clock()


class TestDemoProtocol:
    @pytest.fixture
    def factory(self, clock: Clock) -> DemoFactory:
        return DemoFactory(clock)

    def start(
        self, clock: Clock, factory: DemoFactory
    ) -> tuple[ServerStream, DemoProtocol]:
        stream = ServerStream(clock, "a stream id of unusual length", factory)
        stream.transport_online(DummySocketLikeTransport(), True, None)
        protocol = stream._protocol
        assert isinstance(protocol, DemoProtocol)
        return stream, protocol

    def sent(self, stream: ServerStream) -> list[str]:
        return [s for _, s in stream.queue.iter_items()]

    @pytest.mark.parametrize(
        ("received", "sent"),
        [
            ("echo:hello", ["hello"]),
            ("echo:a:b", ["a:b"]),
            ("echo:", [""]),
            ("echo", ["unknown_message_type"]),
            ("send_demo:", ["unknown_message_type"]),
            ("what?", ["unknown_message_type"]),
        ],
    )
    def test_commands(
        self, clock: Clock, factory: DemoFactory, received: str, sent: list[str]
    ) -> None:
        stream, protocol = self.start(clock, factory)
        protocol.string_received(received)
        assert self.sent(stream) == sent

    def test_echo_twice(self, clock: Clock, factory: DemoFactory) -> None:
        stream, protocol = self.start(clock, factory)
        protocol.string_received("echo_twice:hi")
        assert self.sent(stream) == ["hi"]
        clock.advance(0)
        assert self.sent(stream) == ["hi", "hi"]

    def test_reset_me(self, clock: Clock, factory: DemoFactory) -> None:
        stream, protocol = self.start(clock, factory)
        protocol.string_received("reset_me:because")
        assert stream.disconnected

    def test_send_demo(self, clock: Clock, factory: DemoFactory) -> None:
        stream, protocol = self.start(clock, factory)
        protocol.string_received("send_demo")
        assert self.sent(stream) == [
            "starting_send_demo",
            f"alphabet: {restricted_string_alphabet()}",
            " ".join(["#1"] * 5),
        ]
        clock.advance(0.2)
        assert self.sent(stream)[3:] == [" ".join(["#2"] * 10)] * 2

    def test_chat(self, clock: Clock, factory: DemoFactory) -> None:
        stream1, protocol1 = self.start(clock, factory)
        stream2, protocol2 = self.start(clock, factory)
        protocol1.string_received("begin_chat")
        protocol2.string_received("begin_chat")
        protocol1.string_received("broadcast:hello all")
        assert self.sent(stream1) == self.sent(stream2) == ["TEXT|1|hello all"]

        stream1.reset_from_peer("bye", True)
        assert factory.chatters == {protocol2}

    def test_subprotocol(self, clock: Clock) -> None:
        """
        After `subprotocol:<name>`, a demo's own protocol gets the stream.
        """
        subfactory = MockStringFactory()
        stream, protocol = self.start(clock, DemoFactory(clock, {"demo": subfactory}))
        protocol.string_received("subprotocol:demo")
        protocol.string_received("echo:hi")
        assert subfactory.instance.get_new() == [
            ["stream_started", stream],
            ["string_received", "echo:hi"],
        ]
        assert self.sent(stream) == []
        stream.reset("bye")
        assert subfactory.instance.get_new() == [["stream_reset", "bye", True]]

    def test_unknown_subprotocol(self, clock: Clock, factory: DemoFactory) -> None:
        stream, protocol = self.start(clock, factory)
        protocol.string_received("subprotocol:whiteboard")
        assert self.sent(stream) == ["unknown_message_type"]


def test_restricted_string_alphabet() -> None:
    alphabet = restricted_string_alphabet()
    assert alphabet[0] == " "
    assert alphabet[-1] == "~"
    assert len(alphabet) == 95


class TestParseRanges:
    def test_valid(self) -> None:
        assert parse_ranges("1-126,57344-65533") == [range(1, 127), range(57344, 65534)]

    @pytest.mark.parametrize("bad", ["", "1", "1-", "2-1", "-1-5", "1-1114112", "a-b"])
    def test_invalid(self, bad: str) -> None:
        with pytest.raises(ValueError):
            parse_ranges(bad)


def test_policy_file() -> None:
    assert policy_file([843, 8112]) == (
        "<cross-domain-policy>\n"
        '<allow-access-from domain="*" to-ports="843,8112"/>\n'
        "</cross-domain-policy>"
    )


class TestParseArgs:
    def test_defaults(self) -> None:
        args = parse_args(["--http", "tcp:8111"])
        assert args.http == ["tcp:8111"]
        assert args.minerva == []
        assert args.domain is None
        assert isinstance(args.closure_library, Path)

    def test_repeatable(self) -> None:
        args = parse_args(["-t", "tcp:1", "-t", "tcp:2", "-m", "tcp:3"])
        assert args.http == ["tcp:1", "tcp:2"]
        assert args.minerva == ["tcp:3"]

    def test_bluesky(self) -> None:
        args = parse_args(["--http", "tcp:8111"])
        assert args.jetstream == "wss://jetstream.us-east.bsky.network"
        assert args.bluesky_appview == "https://public.api.bsky.app"
        jetstream = ["--jetstream", "ws://localhost:6008"]
        appview = ["--bluesky-appview", "http://localhost:2584"]
        args = parse_args(["--http", "tcp:8111", *jetstream, *appview])
        assert args.jetstream == "ws://localhost:6008"
        assert args.bluesky_appview == "http://localhost:2584"

    def test_needs_a_server(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            parse_args([])
        assert "start at least one" in capsys.readouterr().err


def test_warns_when_js_minerva_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """
    At startup, `minerva-site` says so when it can't find the uncompiled
    JavaScript client (as when the `minerva` package is not imported from a
    checkout of the repository).
    """
    warning = "Could not find Minerva's uncompiled JavaScript"
    args = parse_args(["--http", "tcp:8111"])
    monkeypatch.setattr("minerva.site._JS_MINERVA_DIR", tmp_path)
    _warn_about_setup(args)
    assert warning not in caplog.text

    monkeypatch.setattr("minerva.site._JS_MINERVA_DIR", tmp_path / "missing")
    _warn_about_setup(args)
    assert warning in caplog.text


def test_warns_when_closure_library_is_missing(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """
    At startup, `minerva-site` says so when the Closure Library path lacks
    closure/goog/base.js (as when the submodule has not been fetched).
    """
    warning = "Could not find Closure Library"
    args = parse_args(["--http", "tcp:8111", "--closure-library", str(tmp_path)])
    _warn_about_setup(args)
    assert warning in caplog.text

    caplog.clear()
    (tmp_path / "closure" / "goog").mkdir(parents=True)
    (tmp_path / "closure" / "goog" / "base.js").touch()
    _warn_about_setup(args)
    assert warning not in caplog.text


def make_root(clock: Clock, tmp_path: Path) -> Resource:
    tracker = StreamTracker(clock, DemoFactory(clock), inactive_check_interval=None)
    site = make_site(
        clock,
        tracker,
        domain="example.com",
        main_socket_port=8112,
        closure_library=tmp_path / "closure-library",
        coreweb=tmp_path / "Coreweb",
    )
    return site.resource


class TestSite:
    @pytest.fixture
    def root(self, clock: Clock, tmp_path: Path) -> Resource:
        return make_root(clock, tmp_path)

    def get(
        self, root: Resource, path: bytes, **args: bytes
    ) -> tuple[Resource, FakeRequest]:
        request = FakeRequest()
        request.method = b"GET"
        request.postpath = path.split(b"/")[1:]
        request.args = {k.encode(): [v] for k, v in args.items()}
        resource = getChildForRequest(root, request)
        result = resource.render(request)
        if isinstance(result, bytes):
            request.write(result)
        return resource, request

    def test_index(self, root: Resource) -> None:
        request = FakeRequest()
        request.postpath = [b""]
        resource = getChildForRequest(root, request)
        assert isinstance(resource, File)
        assert resource.path.endswith("index.html")

    @pytest.mark.parametrize("standalone", [b"0", b"1"])
    def test_chatapp(self, root: Resource, standalone: bytes) -> None:
        _, request = self.get(root, b"/chatapp/", standaloneClient=standalone)
        page = request.written_bytes().decode()
        assert '__demo_shared_domain = "example.com";' in page
        assert "__demo_mainSocketPort = 8112;" in page
        assert (
            f"standaloneClient = {'true' if standalone == b'1' else 'false'};" in page
        )
        assert ("compiled_client/minerva-client.js" in page) == (standalone == b"1")

    @pytest.mark.parametrize(
        ("path", "code"),
        [
            (b"/chatapp", 301),
            (b"/chatapp/more", 404),
            (b"/whiteboard", 301),
            (b"/@testres_Minerva/GetEndpointInfo", 301),
            (b"/@testres_Minerva/GetEndpointInfo/more", 404),
            (b"/_minerva/io", 301),
            (b"/_minerva/io/more", 404),
            # Not a `BetterResource` (nor was it on master), so not redirected.
            (b"/wait_resource", None),
            (b"/wait_resource/more", 404),
        ],
    )
    def test_one_url_per_page(
        self, root: Resource, path: bytes, code: int | None
    ) -> None:
        request = FakeRequest()
        request.method = b"GET"
        request.uri = path
        request.postpath = path.split(b"/")[1:]
        getChildForRequest(root, request).render(request)
        assert request.responseCode == code

    def test_dumbtest(self, root: Resource) -> None:
        _, request = self.get(root, b"/dumbtest/")
        assert "__demo_mainSocketPort = 8112;" in request.written_bytes().decode()

    @pytest.mark.parametrize(
        ("path", "script"),
        [
            (b"/whiteboard/", "/demos_static/whiteboard.js?cb="),
            (b"/whiteboard_dev/", "goog.require('whiteboard');"),
            (b"/bluesky-stream/", "/demos_static/bskystream.js?cb="),
            (b"/bluesky-stream_dev/", "goog.require('bskystream');"),
        ],
    )
    def test_demos(self, root: Resource, path: bytes, script: str) -> None:
        _, request = self.get(root, path)
        page = request.written_bytes().decode()
        assert '__demo_shared_domain = "example.com";' in page
        assert "__demo_mainSocketPort = 8112;" in page
        assert script in page
        assert ("/closure-library/" in page) == path.endswith(b"_dev/")

    def test_bluesky_stream_without_the_extra(
        self, clock: Clock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(bskystream, "extra_installed", lambda: False)
        _, request = self.get(make_root(clock, tmp_path), b"/bluesky-stream/")
        page = request.written_bytes().decode()
        assert "bskystream-unavailable" in page
        assert "/demos_static/bskystream.js" not in page
        assert "__bskystream_init();" not in page

    def test_demos_static(self, root: Resource) -> None:
        _, request = self.get(root, b"/whiteboard/")
        digest = file_digest(DEMOS_STATIC_DIR / "whiteboard.css")
        assert (
            f"/demos_static/whiteboard.css?cb={digest}"
            in request.written_bytes().decode()
        )

        request = FakeRequest()
        request.postpath = [b"demos_static", b"whiteboard.css"]
        resource = getChildForRequest(root, request)
        # Files in a served directory must be revalidated too.
        assert isinstance(resource, RevalidatedFile)
        assert resource.path == str(DEMOS_STATIC_DIR / "whiteboard.css")

    def test_endpoint_info(self, root: Resource) -> None:
        _, request = self.get(root, b"/@testres_Minerva/GetEndpointInfo/")
        assert json.loads(request.written_bytes()) == {"mainSocketPort": 8112}

    def test_simple_response(self, root: Resource) -> None:
        _, request = self.get(root, b"/@testres_Minerva/SimpleResponse/", a=b"0")
        assert json.loads(request.written_bytes()) == {"you_sent_args": {"a": ["0"]}}

    def test_unicode_rainbow(self, root: Resource) -> None:
        _, request = self.get(
            root, b"/@testres_Minerva/UnicodeRainbow/", ranges=b"65-67,9731-9731"
        )
        assert request.written_bytes().decode() == "ABC\N{SNOWMAN}"

    def test_unicode_rainbow_bad_ranges(self, root: Resource) -> None:
        _, request = self.get(root, b"/@testres_Minerva/UnicodeRainbow/", ranges=b"9-1")
        assert request.responseCode == 400

    def test_xdrframe_allows_the_domain(self, root: Resource) -> None:
        _, request = self.get(
            root, b"/_minerva/xdrframe/", id=b"f1", domain=b"example.com"
        )
        assert request.responseCode is None
        assert b'__xdrframe_setupXDRFrame("f1");' in request.written_bytes()


def test_form_sandbox_post_is_not_html() -> None:
    from minerva.site import FormSandbox

    request = FakeRequest(b"<script>alert(1)</script>")
    FormSandbox().render(request)
    assert request.responseHeaders.getRawHeaders(b"content-type") == [
        b"text/plain; charset=utf-8"
    ]


class TestWaitResource:
    def test_get(self, clock: Clock) -> None:
        request = FakeRequest()
        request.method = b"GET"
        request.args = {b"wait": [b"3"]}
        assert WaitResource(clock).render(request) == NOT_DONE_YET
        clock.advance(2.9)
        assert request.finished == 0
        clock.advance(0.1)
        assert request.finished == 1
        assert request.written_bytes().startswith(b"GIF89a")

    @pytest.mark.parametrize("wait", [b"-1", b"601", b"x"])
    def test_bad_wait_means_30_seconds(self, clock: Clock, wait: bytes) -> None:
        request = FakeRequest()
        request.args = {b"wait": [wait]}
        WaitResource(clock).render(request)
        clock.advance(29.9)
        assert request.finished == 0
        clock.advance(0.1)
        assert request.finished == 1

    def test_cancelled_if_client_goes_away(self, clock: Clock) -> None:
        request = FakeRequest()
        WaitResource(clock).render(request)
        request.processingFailed(Exception("gone"))
        assert clock.getDelayedCalls() == []


def test_command_line(tmp_path: Path) -> None:
    """
    `minerva-site` listens on the endpoints it's given (here, ephemeral
    ports), and tells clients the actual socket port.
    """
    command = [
        sys.executable,
        "-m",
        "minerva.site",
        "--http",
        "tcp:0:interface=127.0.0.1",
    ]
    command += ["--minerva", "tcp:0:interface=127.0.0.1", "--coreweb", str(tmp_path)]
    with subprocess.Popen(command, stderr=subprocess.PIPE, text=True) as server:
        try:
            assert server.stderr is not None
            ports: dict[str, int] = {}
            while len(ports) < 2:
                line = server.stderr.readline()
                assert line, "minerva-site exited early"
                if match := re.search(
                    r"(HTTP server|socket listener) on .*port=(\d+)", line
                ):
                    ports[match[1]] = int(match[2])
            http_port, socket_port = ports["HTTP server"], ports["socket listener"]

            url = f"http://127.0.0.1:{http_port}/@testres_Minerva/GetEndpointInfo/"
            with urllib.request.urlopen(url, timeout=10) as response:
                assert json.load(response) == {"mainSocketPort": socket_port}

            with socket.create_connection(
                ("127.0.0.1", socket_port), timeout=10
            ) as sock:
                sock.sendall(b"<policy-file-request/>\x00")
                assert f'to-ports="{socket_port}"'.encode() in sock.recv(4096)
        finally:
            server.terminate()
            # Drain stderr, so that the server can log its shutdown.
            server.communicate(timeout=10)
    assert server.returncode == 0
