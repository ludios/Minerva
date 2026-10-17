"""
End-to-end tests: the compiled JavaScript client in headless Chrome, talking
to the server over HTTP long-polling.  Skipped if Chrome isn't installed.
"""

import html
import re
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

CHROME = next(
    filter(None, map(shutil.which, ["google-chrome", "chromium", "chromium-browser"])),
    None,
)
pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(CHROME is None, reason="needs Chrome or Chromium"),
]


@pytest.fixture(scope="module")
def server_port() -> Iterator[int]:
    with subprocess.Popen(
        [sys.executable, "-m", "tests.browser_server"],
        cwd=Path(__file__).parent.parent,
        stdout=subprocess.PIPE,
        text=True,
    ) as server:
        try:
            assert server.stdout is not None
            yield int(server.stdout.readline())
        finally:
            server.terminate()


def browse(url: str, profile: Path) -> list[str]:
    """
    Load `url` and return the lines the page logged to #output.
    """
    assert CHROME is not None
    dom = subprocess.run(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--user-data-dir={profile}",
            "--timeout=20000",
            "--dump-dom",
            url,
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    ).stdout
    match = re.search(r'<pre id="output">(.*?)</pre>', dom, re.DOTALL)
    assert match is not None, dom
    return html.unescape(match.group(1)).splitlines()


def test_strings(server_port: int, tmp_path: Path) -> None:
    assert browse(f"http://127.0.0.1:{server_port}/strings", tmp_path) == [
        "started",
        "got: Hey client, you sent me a string with 5 bytes",
        "got: Hey client, you sent me a string with 14 bytes",
        "reset: done",
    ]


def test_qan_with_async_answer(server_port: int, tmp_path: Path) -> None:
    assert browse(f"http://127.0.0.1:{server_port}/qan", tmp_path) == [
        "started",
        "answer: [1]",
        "reset: done",
    ]
