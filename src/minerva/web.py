"""
`WebPort`, the twisted.web resource that Minerva clients talk to.
"""

import functools
import hashlib
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import cast

import jinja2
from markupsafe import Markup
from twisted.web.resource import IResource, Resource
from twisted.web.server import NOT_DONE_YET, Request
from twisted.web.static import File

from minerva.interfaces import Clock, StreamTrackerLike
from minerva.transport import ServerTransport

PACKAGE_DIR = Path(__file__).parent
COMPILED_CLIENT_DIR = PACKAGE_DIR / "compiled_client"

templates = jinja2.Environment(
    loader=jinja2.FileSystemLoader(PACKAGE_DIR),
    # Check for modified templates on every render.
    auto_reload=True,
    autoescape=True,
)


def htmldumps(obj: object) -> Markup:
    """
    Like `json.dumps`, but safe to embed in an HTML `<script>`: `<`, `>`, and
    `&` are escaped, so the JSON can't close the script element or open an
    HTML comment.
    """
    s = json.dumps(obj)
    s = s.replace("<", r"\u003c").replace(">", r"\u003e").replace("&", r"\u0026")
    return Markup(s)


def file_digest(path: Path) -> str:
    """
    Return the MD5 hex digest of the file at `path` (cached until the file
    changes), for use as a cache breaker.
    """
    stat = path.stat()
    return _cached_file_digest(path, stat.st_mtime_ns, stat.st_size)


@functools.lru_cache(maxsize=64)
def _cached_file_digest(path: Path, mtime_ns: int, size: int) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "md5").hexdigest()


def put_child(parent: Resource, path: bytes, child: Resource) -> None:
    """
    `parent.putChild(path, child)`, for type checkers that (like ty) don't
    understand that `@implementer(IResource)` makes every `Resource` an
    `IResource`.
    """
    parent.putChild(path, cast(IResource, child))


def bad_request(request: Request, message: str) -> bytes:
    request.setResponseCode(400)
    request.setHeader(b"content-type", b"text/plain; charset=utf-8")
    return message.encode("utf-8")


class HttpIo(Resource):
    """
    The endpoint for the client's HTTP transports.  Every POST becomes a
    `ServerTransport`.
    """

    isLeaf = True

    def __init__(self, clock: Clock, stream_tracker: StreamTrackerLike) -> None:
        super().__init__()
        self._clock = clock
        self._stream_tracker = stream_tracker

    def render_POST(self, request: Request) -> int:
        transport = ServerTransport(self._clock, self._stream_tracker)
        request.notifyFinish().addErrback(transport.request_aborted)
        transport.request_started(request)
        return NOT_DONE_YET


_FRAME_ID = re.compile(rb"[A-Za-z0-9]{0,50}")


class XDRFrame(Resource):
    """
    A page to load into an iframe.  It sets `document.domain` so that it can
    talk to the parent page (which must set `document.domain` too), and it can
    make XHR requests on the parent's behalf, to another subdomain.
    """

    isLeaf = True

    def __init__(self, allowed_domains: frozenset[str], dev_mode: bool = False) -> None:
        """
        If `dev_mode`, the page loads the uncompiled JavaScript instead of the
        compiled `xdrframe.js`.
        """
        super().__init__()
        self._allowed_domains = allowed_domains
        self._dev_mode = dev_mode

    def render_GET(self, request: Request) -> bytes:
        args = request.args or {}
        frame_id = args.get(b"id", [b""])[0]
        domain = args.get(b"domain", [b""])[0].decode("ascii", "replace")
        if not _FRAME_ID.fullmatch(frame_id):
            return bad_request(request, "bad frame id")
        if domain not in self._allowed_domains:
            return bad_request(request, f"domain {domain!r} is not allowed")

        xdrframe_js = COMPILED_CLIENT_DIR / "xdrframe.js"
        html = templates.get_template("xdrframe.html").render(
            htmldumps=htmldumps,
            domain=domain,
            frame_id=frame_id.decode("ascii"),
            dev_mode=self._dev_mode,
            # Loaded from the parent page's domain, not our random subdomain,
            # so that it can be cached.
            xdrframe_js_href=f"/compiled_client/xdrframe.js?cb={file_digest(xdrframe_js)}",
        )
        request.setHeader(b"content-type", b"text/html; charset=utf-8")
        return html.encode("utf-8")


class WebPort(Resource):
    """
    Put this resource into your site's resource tree (conventionally at
    `/_minerva/`), so that Minerva clients can connect to your server.  Its
    children:

    - `io`: for the client's HTTP transports.
    - `xdrframe`: a cross-subdomain communication helper; compiled JS.
    - `xdrframe_dev`: the same, with uncompiled JS.
    - `FlashConnector.swf`: for the client's Flash socket transport.
    - `minerva-client.js`: the standalone Minerva client, for convenience.
    """

    def __init__(
        self,
        clock: Clock,
        stream_tracker: StreamTrackerLike,
        allowed_domains: Iterable[str] = (),
    ) -> None:
        """
        `allowed_domains` are the values the `xdrframe` may set
        `document.domain` to.
        """
        super().__init__()
        allowed = frozenset(allowed_domains)
        put_child(self, b"io", HttpIo(clock, stream_tracker))
        put_child(self, b"xdrframe", XDRFrame(allowed))
        put_child(self, b"xdrframe_dev", XDRFrame(allowed, dev_mode=True))
        put_child(
            self,
            b"FlashConnector.swf",
            File(str(COMPILED_CLIENT_DIR / "FlashConnector.swf")),
        )
        # Applications using Closure Library will build their own client
        # instead.
        put_child(
            self,
            b"minerva-client.js",
            File(str(COMPILED_CLIENT_DIR / "minerva-client.js")),
        )
