"""
End-to-end tests of the Flash socket transport: the compiled JavaScript
client and the real FlashConnector.swf, in a browser with Adobe Flash Player,
talking to the server over TCP.  Skipped without that browser; see
tests/flash_browser.py.
"""

import secrets
import time
import urllib.request
from collections.abc import Iterator

import pytest

from tests import flash_browser

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(
        not flash_browser.available(),
        reason=(
            f"needs a Flash browser at {flash_browser.BROWSER} (see "
            "scripts/flash-browser.nix), and Xvfb"
        ),
    ),
]


@pytest.fixture(scope="module")
def display() -> Iterator[str]:
    with flash_browser.virtual_display() as display:
        yield display


def browse(port: int, path: str, display: str) -> list[str]:
    """
    Load `path` from the browser server, wait until the page logs a
    "reset: ..." or "ERROR ..." line, and return all the lines it logged.
    """
    run = secrets.token_hex(8)
    with flash_browser.open_page(
        f"http://127.0.0.1:{port}{path}?run={run}", display
    ) as browser:
        deadline = time.monotonic() + 30
        while True:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/log/{run}") as log:
                lines = log.read().decode().splitlines()
            if any(line.startswith(("reset: ", "ERROR ")) for line in lines):
                return lines
            assert browser.poll() is None, f"browser exited; page logged {lines}"
            # The client can give up on a stream without calling streamReset
            # (in ClientStream.earlyFailure_, e.g. if Flash Player doesn't load).
            assert time.monotonic() < deadline, f"timed out; page logged {lines}"
            time.sleep(0.1)


def test_strings(browser_server_port: int, display: str) -> None:
    assert browse(browser_server_port, "/flash/strings", display) == [
        "started",
        "got: Hey client, you sent me a string with 5 bytes",
        "got: Hey client, you sent me a string with 14 bytes",
        "reset: done",
    ]


def test_qan_with_async_answer(browser_server_port: int, display: str) -> None:
    assert browse(browser_server_port, "/flash/qan", display) == [
        "started",
        "answer: [1]",
        "reset: done",
    ]
