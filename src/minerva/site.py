"""
`minerva-site`, Minerva's development server.  It serves the in-browser
JavaScript tests, the demos (see `minerva.demos`), and a few other test pages
and resources.

    uv run minerva-site --http tcp:8111:interface=127.0.0.1 --minerva tcp:8112

Then open http://127.0.0.1:8111/ in your browser.  The pages that use the
uncompiled JavaScript need Closure Library and Coreweb's JavaScript; by default
Closure Library is the repository's `closure-library` submodule, and Coreweb is
found next to the repository (`../Coreweb`).  Those pages also need
`js_minerva/`, which is in the repository but not in the installed package.
"""

import argparse
import html
import json
import logging
import textwrap
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import NoReturn, Protocol, cast, override

from twisted.internet import task
from twisted.internet.address import IPv4Address, IPv6Address
from twisted.internet.defer import Deferred
from twisted.internet.endpoints import serverFromString
from twisted.internet.interfaces import IReactorCore, IReactorTCP
from twisted.logger import ILogObserver, STDLibLogObserver, globalLogBeginner
from twisted.python.failure import Failure
from twisted.web.http import HTTPChannel
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET, Request, Site

from minerva.demos import bskystream
from minerva.demos.whiteboard import WhiteboardFactory
from minerva.interfaces import Clock, StringFactory, StringProtocol
from minerva.stream import ServerStream, StreamTracker
from minerva.transport import ServerTransportFactory
from minerva.web import (
    PACKAGE_DIR,
    BetterResource,
    RevalidatedFile,
    WebPort,
    bad_request,
    file_digest,
    htmldumps,
    put_child,
    templates,
)

logger = logging.getLogger(__name__)

# The repository checkout that this module is in (if it is in one).
_REPO_DIR = PACKAGE_DIR.parent.parent
# The uncompiled JavaScript client.  It is not part of the installed package.
_JS_MINERVA_DIR = _REPO_DIR / "js_minerva"


# --- The demo protocol ----------------------------------------------------------


def restricted_string_alphabet() -> str:
    return "".join(map(chr, range(0x20, 0x7E + 1)))


class DemoProtocol:
    """
    Understands a few commands that the chat demo and the JavaScript tests
    send.  The other demos send `subprotocol:<name>` first, after which their
    own protocol (from `factory.subfactories`) gets the stream.
    """

    def __init__(self, factory: DemoFactory, clock: Clock, id: int) -> None:
        self.factory = factory
        self._clock = clock
        self._id = id
        self.stream: ServerStream | None = None
        self._subprotocol: StringProtocol | None = None
        self._reset = False
        self._chatting = False

    def stream_started(self, stream: ServerStream) -> None:
        self.stream = stream

    def _send_demo(self, iteration: int) -> None:
        """
        Send more and bigger strings with every iteration, for end-to-end
        testing.
        """
        if self._reset or iteration > 20:
            return
        assert self.stream is not None
        self._clock.callLater(0.2, self._send_demo, iteration + 1)
        string = " ".join([f"#{iteration}"] * (iteration * 5))
        for _ in range(iteration):
            self.stream.send_string(string)

    def string_received(self, s: str) -> None:
        if self._subprotocol is not None:
            self._subprotocol.string_received(s)
            return
        stream = self.stream
        assert stream is not None
        match s.partition(":"):
            case ("subprotocol", ":", name) if name in self.factory.subfactories:
                self._subprotocol = self.factory.subfactories[name].build_protocol()
                self._subprotocol.stream_started(stream)
            case ("echo", ":", payload):
                stream.send_string(payload)
            case ("echo_twice", ":", payload):
                stream.send_string(payload)
                self._clock.callLater(0, stream.send_string, payload)
            case ("reset_me", ":", reason):
                stream.reset(reason)
            case ("string_then_reset_me", ":", reason):
                # This string effectively closes a long-polling primary
                # transport, so the client usually won't see the reset frame.
                stream.send_string(f"about to reset with reasonString {reason}")
                stream.reset(reason)
            case ("send_demo", "", ""):
                stream.send_string("starting_send_demo")
                stream.send_string(f"alphabet: {restricted_string_alphabet()}")
                self._send_demo(1)
            case ("begin_chat", "", ""):
                self._chatting = True
                self.factory.chatters.add(self)
            case ("broadcast", ":", text):
                for chatter in self.factory.chatters:
                    assert chatter.stream is not None
                    chatter.stream.send_string(f"TEXT|{self._id}|{text}")
            case _:
                stream.send_string("unknown_message_type")

    def stream_reset(self, reason_string: str, application_level: bool) -> None:
        logger.info("Stream reset: %r, %r", reason_string, application_level)
        self._reset = True
        self.factory.chatters.discard(self)
        if self._subprotocol is not None:
            self._subprotocol.stream_reset(reason_string, application_level)


class DemoFactory:
    def __init__(
        self, clock: Clock, subfactories: Mapping[str, StringFactory] | None = None
    ) -> None:
        self._clock = clock
        self._counter = 0
        self.chatters: set[DemoProtocol] = set()
        self.subfactories = subfactories or {}

    def build_protocol(self) -> DemoProtocol:
        self._counter += 1
        return DemoProtocol(self, self._clock, self._counter)


# --- Pages ------------------------------------------------------------------------


def _render_template(request: Request, name: str, **variables: object) -> bytes:
    request.setHeader(b"content-type", b"text/html; charset=utf-8")
    return (
        templates.get_template(name).render(htmldumps=htmldumps, **variables).encode()
    )


class ChatAppPage(BetterResource):
    isLeaf = True

    def __init__(self, domain: str | None, main_socket_port: int | None) -> None:
        super().__init__()
        self._domain = domain
        self._main_socket_port = main_socket_port

    def render_GET(self, request: Request) -> bytes:
        standalone_client = (request.args or {}).get(b"standaloneClient", [b"0"])[
            0
        ] == b"1"
        return _render_template(
            request,
            "chatapp/chatapp.html",
            domain=self._domain,
            dev_mode=True,
            main_socket_port=self._main_socket_port,
            standalone_client=standalone_client,
        )


class DumbTestPage(BetterResource):
    isLeaf = True

    def __init__(self, main_socket_port: int | None) -> None:
        super().__init__()
        self._main_socket_port = main_socket_port

    def render_GET(self, request: Request) -> bytes:
        return _render_template(
            request, "dumbtest/dumbtest.html", main_socket_port=self._main_socket_port
        )


DEMOS_STATIC_DIR = PACKAGE_DIR / "demos" / "static"


def demos_static_href(name: str) -> str:
    """
    The URL of the demos' static file `name`, with a cache breaker.
    """
    return f"/demos_static/{name}?cb={file_digest(DEMOS_STATIC_DIR / name)}"


class DemoPage(BetterResource):
    """
    A demo's page (see `minerva.demos`).  With `dev_mode`, it loads the
    uncompiled JavaScript.
    """

    isLeaf = True

    def __init__(
        self,
        template: str,
        domain: str | None,
        main_socket_port: int | None,
        dev_mode: bool,
        **variables: object,
    ) -> None:
        super().__init__()
        self._template = template
        self._variables = variables | {
            "domain": domain,
            "main_socket_port": main_socket_port,
            "dev_mode": dev_mode,
        }

    def render_GET(self, request: Request) -> bytes:
        return _render_template(
            request,
            self._template,
            static_href=demos_static_href,
            **self._variables,
        )


class WaitResource(Resource):
    """
    Responds after the number of seconds in the `?wait=` query argument
    (default 30, at most 600).  Used by the chat demo to test whether the
    browser shows a loading spinner.
    """

    isLeaf = True
    _BLANK_GIF = bytes.fromhex(
        "47494638396101000100800000ffffff00000021f90400000000002c00000000010001000002024401003b"
    )

    def __init__(self, clock: Clock) -> None:
        super().__init__()
        self._clock = clock

    def _wait_time(self, request: Request) -> int:
        try:
            wait = int((request.args or {})[b"wait"][0])
        except KeyError, IndexError, ValueError:
            return 30
        return wait if 0 <= wait <= 600 else 30

    def _respond_later(self, request: Request, body: bytes) -> int:
        request.setHeader(
            b"cache-control", b"no-cache, no-store, max-age=0, must-revalidate"
        )
        request.setHeader(b"access-control-allow-origin", b"*")

        def respond() -> None:
            # ty is confused by twisted.web.http.Request sometimes assigning
            # `self.write = lambda data: None`.
            request.write(body)  # ty: ignore[missing-argument, invalid-argument-type]
            request.finish()

        call = self._clock.callLater(self._wait_time(request), respond)
        request.notifyFinish().addErrback(lambda _: call.cancel())
        return NOT_DONE_YET

    def render_GET(self, request: Request) -> int:
        request.setHeader(b"content-type", b"image/gif")
        return self._respond_later(request, self._BLANK_GIF)

    def render_POST(self, request: Request) -> int:
        return self._respond_later(request, b"// Done waiting.")


class FormSandbox(BetterResource):
    isLeaf = True

    def render_GET(self, request: Request) -> bytes:
        return b"""\
GET.

<form name="input" action="/form_sandbox/" method="POST">
<input type="text" name="user">
<input type="submit" value="Submit">
</form>
"""

    def render_POST(self, request: Request) -> bytes:
        # Not HTML, so that it can't reflect a script.
        request.setHeader(b"content-type", b"text/plain; charset=utf-8")
        assert request.content is not None
        request.content.seek(0)
        return f"POST with request.content: {request.content.read()!r}".encode()


# --- Resources used by the JavaScript tests (see TestXHDR.js) -----------------------


class NoOriginHeader(BetterResource):
    isLeaf = True

    def render_GET(self, request: Request) -> bytes:
        return b"GET"

    def render_POST(self, request: Request) -> bytes:
        return b"POST"


class SimpleResponse(BetterResource):
    isLeaf = True

    def render_GET(self, request: Request) -> bytes:
        # XDR needs this header to work at all.
        request.setHeader(b"access-control-allow-origin", b"*")
        request.setHeader(b"content-type", b"text/plain")
        args = {
            k.decode("utf-8", "replace"): [v.decode("utf-8", "replace") for v in vs]
            for k, vs in (request.args or {}).items()
        }
        return json.dumps({"you_sent_args": args}).encode()

    def render_POST(self, request: Request) -> bytes:
        request.setHeader(b"access-control-allow-origin", b"*")
        assert request.content is not None
        body = request.content.read().decode("utf-8")
        return json.dumps({"you_posted_utf8": body}).encode()


def parse_ranges(value: str) -> list[range]:
    """
    Parse `"1-126,57344-65533"` into inclusive ranges.  Raises `ValueError`.
    """
    ranges = []
    for part in value.split(","):
        start, end = map(int, part.split("-"))
        if not 0 <= start <= end <= 0x10FFFF:
            raise ValueError(f"bad range {part!r}")
        ranges.append(range(start, end + 1))
    return ranges


class UnicodeRainbow(BetterResource):
    """
    Responds with the UTF-8 encoding of every code point in `?ranges=`.
    """

    isLeaf = True

    def render_GET(self, request: Request) -> bytes:
        request.setHeader(b"access-control-allow-origin", b"*")
        try:
            ranges = parse_ranges((request.args or {})[b"ranges"][0].decode())
        except KeyError, IndexError, ValueError:
            return bad_request(request, "bad or missing ranges")
        request.setHeader(b"content-type", b"text/plain; charset=utf-8")
        # Surrogates can't be encoded, but the tests don't ask for them.
        return "".join(chr(c) for r in ranges for c in r).encode("utf-8", "replace")

    def render_POST(self, request: Request) -> bytes:
        return self.render_GET(request)


class GetEndpointInfo(BetterResource):
    """
    Tells TestClient.js which port the Flash socket endpoint listens on.
    """

    isLeaf = True

    def __init__(self, main_socket_port: int | None) -> None:
        super().__init__()
        self._main_socket_port = main_socket_port

    def render_GET(self, request: Request) -> bytes:
        return json.dumps({"mainSocketPort": self._main_socket_port}).encode()


class DisplayConnections(BetterResource):
    isLeaf = True

    def render_GET(self, request: Request) -> bytes:
        connections = cast(ConnectionTrackingSite, request.site).connections
        return f"<pre>\n{html.escape(repr(connections))}\n</pre>\n".encode()


# --- The site -----------------------------------------------------------------------


class _TrackingChannel(HTTPChannel):
    """
    Sets TCP_NODELAY (important for Comet latency) and keeps track of the
    open connections.
    """

    @override
    def connectionMade(self) -> None:
        super().connectionMade()
        if (set_no_delay := getattr(self.transport, "setTcpNoDelay", None)) is not None:
            set_no_delay(True)
        cast(ConnectionTrackingSite, self.factory).connections.add(self)
        logger.debug("Connection made: %r", self)

    @override
    def connectionLost(self, reason: Failure) -> None:
        super().connectionLost(reason)
        cast(ConnectionTrackingSite, self.factory).connections.discard(self)
        logger.debug("Connection lost: %r", self)


class ConnectionTrackingSite(Site):
    protocol = _TrackingChannel  # ty: ignore[invalid-assignment]

    def __init__(self, resource: Resource, timeout: float = 75) -> None:
        """
        `timeout` is the keep-alive timeout for idle HTTP connections.
        """
        super().__init__(resource, timeout=timeout)
        self.connections: set[HTTPChannel] = set()


def make_site(
    clock: Clock,
    stream_tracker: StreamTracker,
    domain: str | None,
    main_socket_port: int | None,
    closure_library: Path,
    coreweb: Path,
) -> ConnectionTrackingSite:
    root = BetterResource()

    def static(path: Path) -> RevalidatedFile:
        return RevalidatedFile(str(path))

    put_child(root, b"", static(PACKAGE_DIR / "index.html"))
    put_child(
        root, b"js_minerva_tests.html", static(PACKAGE_DIR / "js_minerva_tests.html")
    )
    put_child(root, b"compiled_client", static(PACKAGE_DIR / "compiled_client"))
    put_child(root, b"closure-library", static(closure_library))
    put_child(root, b"js_coreweb", static(coreweb / "js_coreweb"))
    put_child(root, b"js_minerva", static(_JS_MINERVA_DIR))
    put_child(root, b"@testres_Coreweb", static(coreweb / "coreweb" / "testres"))

    test_resources = BetterResource()
    put_child(test_resources, b"DisplayConnections", DisplayConnections())
    put_child(test_resources, b"SimpleResponse", SimpleResponse())
    put_child(test_resources, b"UnicodeRainbow", UnicodeRainbow())
    put_child(test_resources, b"NoOriginHeader", NoOriginHeader())
    put_child(test_resources, b"GetEndpointInfo", GetEndpointInfo(main_socket_port))
    put_child(root, b"@testres_Minerva", test_resources)

    allowed_domains = [domain] if domain else []
    put_child(root, b"_minerva", WebPort(clock, stream_tracker, allowed_domains))
    put_child(root, b"chatapp", ChatAppPage(domain, main_socket_port))
    put_child(root, b"dumbtest", DumbTestPage(main_socket_port))
    demos = [
        (b"whiteboard", "demos/whiteboard.html", {}),
        (
            b"bluesky-stream",
            "demos/bskystream.html",
            {"extra_installed": bskystream.extra_installed()},
        ),
    ]
    for path, template, variables in demos:
        for dev_mode in [False, True]:
            put_child(
                root,
                path + (b"_dev" if dev_mode else b""),
                DemoPage(template, domain, main_socket_port, dev_mode, **variables),
            )
    put_child(root, b"demos_static", static(DEMOS_STATIC_DIR))
    put_child(root, b"wait_resource", WaitResource(clock))
    put_child(root, b"form_sandbox", FormSandbox())
    if (docs := _REPO_DIR / "docs").is_dir():
        put_child(root, b"docs", static(docs))

    return ConnectionTrackingSite(root)


def policy_file(socket_ports: Sequence[int]) -> str:
    """
    A Flash socket policy file that allows connections to `socket_ports`
    from anywhere.  (You might want to be more restrictive, which can help
    avoid a certain DoS attack.)
    """
    to_ports = ",".join(map(str, socket_ports))
    return (
        "<cross-domain-policy>\n"
        f'<allow-access-from domain="*" to-ports="{to_ports}"/>\n'
        "</cross-domain-policy>"
    )


# --- The command line ---------------------------------------------------------------


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="minerva-site",
        description=(
            "Run the Minerva development server, which serves the "
            "client-side unit tests, demos, and some testing tools."
        ),
        epilog=(
            "Endpoints are Twisted endpoint descriptions, like "
            "'tcp:8111:interface=127.0.0.1' or "
            "'ssl:444:privateKey=privateAndPublic.pem'.  "
            "See https://docs.twisted.org/en/stable/core/howto/endpoints.html"
        ),
    )
    parser.add_argument(
        "-t",
        "--http",
        action="append",
        default=[],
        metavar="ENDPOINT",
        help="an endpoint for the HTTP server (repeatable)",
    )
    parser.add_argument(
        "-m",
        "--minerva",
        action="append",
        default=[],
        metavar="ENDPOINT",
        help="an endpoint for Minerva's Flash socket listener (repeatable)",
    )
    parser.add_argument(
        "-d",
        "--domain",
        help=(
            "the domain to set document.domain to (without the port).  "
            "Without it, Minerva over HTTP may only work in one or two tabs at once."
        ),
    )
    parser.add_argument(
        "-c",
        "--closure-library",
        type=Path,
        default=_REPO_DIR / "closure-library",
        help="the path to Closure Library (default: %(default)s)",
    )
    parser.add_argument(
        "--coreweb",
        type=Path,
        default=_REPO_DIR.parent / "Coreweb",
        help="the path to a Coreweb checkout (default: %(default)s)",
    )
    parser.add_argument(
        "--jetstream",
        default=bskystream.JETSTREAM,
        metavar="URL",
        help="the Bluesky Jetstream for the Bluesky stream demo (default: %(default)s)",
    )
    parser.add_argument(
        "--bluesky-appview",
        default=bskystream.APPVIEW,
        metavar="URL",
        help=(
            "the Bluesky AppView that the Bluesky stream demo looks up "
            "profiles with (default: %(default)s)"
        ),
    )
    parser.add_argument(
        "-n",
        "--no-tracebacks",
        action="store_true",
        help="don't display tracebacks in error pages",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="log more")
    args = parser.parse_args(argv)
    if not args.http and not args.minerva:
        parser.error("start at least one HTTP server or Minerva socket listener")
    return args


def _warn(message: str) -> None:
    # Paths in the message stay in one piece.
    wrapped = textwrap.fill(message, 70, break_long_words=False, break_on_hyphens=False)
    logger.warning("\n%s", wrapped)


def _warn_about_setup(args: argparse.Namespace) -> None:
    if not args.domain:
        _warn(
            "--domain not specified.  Browser clients will connect only to the "
            "default hostname; they will not use subdomains to bypass per-hostname "
            "connection limits.  Minerva over HTTP might work simultaneously in just "
            "one or two tabs.  Additional connections may stall erratically."
        )
    if not (args.closure_library / "closure" / "goog" / "base.js").is_file():
        _warn(
            f"Could not find Closure Library at {args.closure_library}.  Many pages "
            "on minerva-site will be broken.  If that path is the "
            "`closure-library` submodule in a checkout of Minerva's repository, "
            "run `git submodule update --init` in that checkout to fetch it; if "
            "it is not, pass the path of a Closure Library with --closure-library."
        )
    if not (args.coreweb / "js_coreweb").is_dir():
        _warn(
            f"Could not find Coreweb at {args.coreweb}.  Pages that use the "
            "uncompiled JavaScript will be broken; pass --coreweb."
        )
    if not _JS_MINERVA_DIR.is_dir():
        _warn(
            f"Could not find Minerva's uncompiled JavaScript: {_JS_MINERVA_DIR} is "
            "not a directory.  Pages that use the uncompiled JavaScript will be "
            "broken.  js_minerva/ is not part of the installed package: "
            "minerva-site finds it only if the `minerva` package itself is "
            "imported from a checkout of Minerva's repository (as it is after "
            "`uv sync` in that checkout)."
        )
    if not bskystream.extra_installed():
        _warn(
            "The Bluesky stream demo needs Minerva's `demos` extra; install it "
            "with `uv sync --extra demos` or `pip install -e '.[demos]'`."
        )


class _SystemEvents(Protocol):
    """
    The part of `IReactorCore` that `serve` uses, for type checkers that (like
    ty) don't understand zope.interface.
    """

    def addSystemEventTrigger(
        self, phase: str, event_type: str, callable: Callable[[], object], /
    ) -> object: ...


async def serve(reactor: IReactorCore, args: argparse.Namespace) -> None:
    # Every reactor provides the `Clock` protocol.
    clock: Clock = reactor
    subfactories: dict[str, StringFactory] = {"whiteboard": WhiteboardFactory(clock)}
    if bskystream.extra_installed():
        bsky_factory = bskystream.make_factory(
            cast(IReactorTCP, reactor), args.jetstream, args.bluesky_appview
        )
        # Don't try to reconnect when the reactor drops the connection.
        cast(_SystemEvents, reactor).addSystemEventTrigger(
            "before", "shutdown", bsky_factory.jetstream.stop
        )
        subfactories["bskystream"] = bsky_factory
    tracker = StreamTracker(clock, DemoFactory(clock, subfactories))
    socket_factory = ServerTransportFactory(clock, tracker)

    socket_ports = []
    for description in args.minerva:
        port = await serverFromString(reactor, description).listen(socket_factory)
        host = port.getHost()
        assert isinstance(host, IPv4Address | IPv6Address), host
        socket_ports.append(host.port)
        logger.info("Minerva socket listener on %s", host)
    socket_factory.set_policy_string(policy_file(socket_ports))

    site = make_site(
        clock,
        tracker,
        domain=args.domain,
        main_socket_port=socket_ports[0] if socket_ports else None,
        closure_library=args.closure_library,
        coreweb=args.coreweb,
    )
    site.displayTracebacks = not args.no_tracebacks
    for description in args.http:
        port = await serverFromString(reactor, description).listen(site)
        logger.info("HTTP server on %s", port.getHost())

    # Serve until interrupted.
    await Deferred()


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # Send Twisted's own log events to the standard library's logging.
    observer = cast(ILogObserver, STDLibLogObserver())  # zope.interface, again
    globalLogBeginner.beginLoggingTo([observer], redirectStandardIO=False)


def main(argv: Sequence[str] | None = None) -> NoReturn:
    args = parse_args(argv)
    configure_logging(args.verbose)
    _warn_about_setup(args)
    task.react(serve, [args])


if __name__ == "__main__":
    main()
