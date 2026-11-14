"""
End-to-end tests for the demos (`minerva.demos`): minerva-site serves them,
with their compiled JavaScript, to headless Chrome.  The Bluesky stream demo
gets its posts and profiles from a fake Jetstream and AppView.  Skipped if
Chrome isn't installed.
"""

import contextlib
import json
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from websockets.exceptions import ConnectionClosed
from websockets.http11 import Request, Response
from websockets.sync.server import ServerConnection, serve

from tests.chrome import CHROME, Page, open_page
from tests.helpers import run_minerva_site
from tests.test_bskystream import event, images, profile

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(CHROME is None, reason="needs Chrome or Chromium"),
]


class FakeBluesky:
    """
    A fake Jetstream and AppView, on one port: it sends `events` to every
    WebSocket client, and answers `getProfiles` requests with `profiles`.
    """

    def __init__(self, events: list[str], profiles: list[dict[str, Any]]) -> None:
        self._events = events
        self._profiles = {p["did"]: p for p in profiles}
        self._server = serve(
            self._send_events, "127.0.0.1", 0, process_request=self._get_profiles
        )
        self.url = f"127.0.0.1:{self._server.socket.getsockname()[1]}"

    def _send_events(self, connection: ServerConnection) -> None:
        for e in self._events:
            connection.send(e)
        # Wait until the client goes away (which minerva-site does abruptly).
        with contextlib.suppress(ConnectionClosed):
            for _ in connection:
                pass

    def _get_profiles(
        self, connection: ServerConnection, request: Request
    ) -> Response | None:
        url = urlsplit(request.path)
        if url.path != "/xrpc/app.bsky.actor.getProfiles":
            return None
        dids = parse_qs(url.query)["actors"]
        profiles = [self._profiles[did] for did in dids if did in self._profiles]
        return connection.respond(200, json.dumps({"profiles": profiles}))

    def __enter__(self) -> FakeBluesky:
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self._server.shutdown()


@pytest.fixture
def bluesky() -> Iterator[FakeBluesky]:
    events = [
        event({"text": "Hello from the fake Jetstream"}),
        event({"text": "A reply", "reply": {"parent": {}, "root": {}}}),
        event({"text": "Labeled", "labels": {"values": [{"val": "nudity"}]}}),
        event({"text": "Please don't show this"}, did="did:plc:shy"),
        event(
            {"text": "こんにちは", "langs": ["ja"], "embed": images(2)},
            did="did:plc:bob",
        ),
        event({"text": "My account is gone"}, did="did:plc:gone"),
        event({"text": "The end", "langs": []}),
    ]
    profiles = [
        profile("did:plc:alice", "alice.test"),
        profile("did:plc:bob", "bob.test"),
        profile("did:plc:shy", "shy.test", ["!no-unauthenticated"]),
    ]
    with FakeBluesky(events, profiles) as bluesky:
        yield bluesky


@pytest.fixture
def site_port(tmp_path: Path, bluesky: FakeBluesky) -> Iterator[int]:
    args = ["--jetstream", f"ws://{bluesky.url}"]
    args += ["--bluesky-appview", f"http://{bluesky.url}"]
    with run_minerva_site(tmp_path / "minerva-site.log", args) as port:
        yield port


def test_bluesky_stream(site_port: int) -> None:
    rows = (
        "Array.from(document.querySelectorAll('#bskystream-container > div'))"
        ".map(function(row) { return row.innerText; })"
    )
    with open_page(f"http://127.0.0.1:{site_port}/bluesky-stream/") as page:
        page.wait_for(f"{rows}.join('\\n').includes('The end')", timeout=30)
        # The page asked for HTTP itself (there's no Flash anymore).
        assert page.evaluate("location.search") == "?mode=http"
        assert [" ".join(row.split()) for row in page.evaluate(rows)] == [
            "@alice.test Hello from the fake Jetstream en",
            "@bob.test こんにちは [2 images] ja",
            "@alice.test The end",
        ]
        assert page.evaluate("document.querySelector('.post-author').href") == (
            "https://bsky.app/profile/did:plc:alice/post/3myedgexaos2f"
        )


def click(
    page: Page, selector: str, x: float | None = None, y: float | None = None
) -> None:
    """
    Click on the element at `selector`: at (`x`, `y`) inside it, or at its
    center.
    """
    left, top, width, height = page.evaluate(
        f"(function(r) {{ return [r.left, r.top, r.width, r.height]; }})"
        f"(document.querySelector({json.dumps(selector)}).getBoundingClientRect())"
    )
    x = left + (width / 2 if x is None else x)
    y = top + (height / 2 if y is None else y)
    for type in ["mousePressed", "mouseReleased"]:
        page.call(
            "Input.dispatchMouseEvent",
            type=type,
            x=x,
            y=y,
            button="left",
            clickCount=1,
        )


def test_whiteboard(site_port: int) -> None:
    url = f"http://127.0.0.1:{site_port}/whiteboard/"
    points = "document.querySelectorAll('#drawArea ellipse').length"
    with open_page(url) as alice:
        alice.wait_for("!!document.querySelector('#drawArea svg')", timeout=30)
        # A fractional position, as on a zoomed page.
        click(alice, "#drawAreaOverlay", 100.4, 50.6)
        assert alice.wait_for(points, timeout=10) == 1
        with open_page(url) as bob:
            # Bob gets the board so far,
            assert bob.wait_for(points, timeout=30) == 1
            assert (
                bob.evaluate(
                    "document.querySelector('#drawArea ellipse').getAttribute('cx')"
                )
                == "100"
            )
            # and new points.
            click(bob, "#drawAreaOverlay", 300, 200)
            alice.wait_for(f"{points} == 2", timeout=30)
            click(alice, ".clear-board-button")
            bob.wait_for(f"{points} == 0", timeout=30)
