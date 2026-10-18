"""
Run the JavaScript client's own test suite (js_minerva_tests.html, served by
minerva-site) in headless Chrome, and in a browser with Flash Player (see
tests/flash_browser.py).  This exercises the uncompiled client against the
server, including real HTTP long-polling and streaming streams, and (with
Flash) Flash socket streams.

Skipped unless Closure Library, Coreweb, and the browser are available.  Set
MINERVA_CLOSURE_LIBRARY and MINERVA_COREWEB to their paths if they aren't next
to this repository.
"""

import os
import queue
import re
import subprocess
import sys
import threading
import time
import urllib.parse
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from tests import flash_browser
from tests.chrome import CHROME, open_page

REPO = Path(__file__).parent.parent
CLOSURE_LIBRARY = Path(
    os.environ.get("MINERVA_CLOSURE_LIBRARY", REPO.parent / "closure-library")
)
COREWEB = Path(os.environ.get("MINERVA_COREWEB", REPO.parent / "Coreweb"))

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(
        not (CLOSURE_LIBRARY / "closure" / "goog" / "base.js").is_file(),
        reason=f"needs Closure Library at {CLOSURE_LIBRARY}",
    ),
    pytest.mark.skipif(
        not (COREWEB / "js_coreweb").is_dir(), reason=f"needs Coreweb at {COREWEB}"
    ),
]


@pytest.fixture
def site_port(tmp_path: Path) -> Iterator[int]:
    """
    Run minerva-site on ephemeral ports; yield its HTTP port.
    """
    log = tmp_path / "minerva-site.log"
    command = [sys.executable, "-m", "minerva.site"]
    command += [
        "--http",
        "tcp:0:interface=127.0.0.1",
        "--minerva",
        "tcp:0:interface=127.0.0.1",
    ]
    command += ["--closure-library", str(CLOSURE_LIBRARY), "--coreweb", str(COREWEB)]
    # Log to a file, so that a full pipe can't block the server.
    with (
        log.open("w") as log_file,
        subprocess.Popen(command, stderr=log_file) as server,
    ):
        try:
            deadline = time.monotonic() + 30
            while not (
                match := re.search(r"HTTP server on .*port=(\d+)", log.read_text())
            ):
                assert server.poll() is None, log.read_text()
                assert time.monotonic() < deadline, log.read_text()
                time.sleep(0.05)
            yield int(match[1])
        finally:
            server.terminate()


def check_results(results: str) -> str:
    """
    Check the text of #TestRunnerPage-results, and return it.
    """
    summary = re.search(r"BEGIN-SUMMARY\*\| (.*) \|\*END-SUMMARY", results)
    assert summary, results
    tests, errors, failures, skips = map(int, summary[1].split(","))
    problems = [
        line
        for line in results.splitlines()
        if not line.endswith(("... OK",)) and "SKIP" not in line
    ]
    assert (errors, failures) == (0, 0), "\n".join(problems)
    assert tests > 150
    assert skips < tests / 4
    return results


@pytest.mark.skipif(CHROME is None, reason="needs Chrome or Chromium")
def test_js_minerva_tests(site_port: int) -> None:
    with open_page(f"http://127.0.0.1:{site_port}/js_minerva_tests.html") as page:
        page.wait_for(
            "document.body.innerText.includes('|*END-SUMMARY*|')", timeout=180
        )
        results = page.evaluate(
            "document.getElementById('TestRunnerPage-results').innerText"
        )
    check_results(results)


@contextmanager
def receive_posts() -> Generator[tuple[str, queue.Queue[str]]]:
    """
    Run an HTTP server; yield its URL, and a queue of the bodies POSTed to it.
    """
    posts: queue.Queue[str] = queue.Queue()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            posts.put(self.rfile.read(int(self.headers["Content-Length"])).decode())
            self.send_response(204)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/", posts
        finally:
            server.shutdown()


@pytest.mark.skipif(
    not flash_browser.available(),
    reason=f"needs a Flash browser at {flash_browser.BROWSER}, and Xvfb",
)
def test_js_minerva_tests_with_flash(site_port: int) -> None:
    with (
        receive_posts() as (report_url, reports),
        flash_browser.virtual_display() as display,
    ):
        query = urllib.parse.urlencode({"report": report_url})
        url = f"http://127.0.0.1:{site_port}/js_minerva_tests.html?{query}"
        with flash_browser.open_page(url, display) as browser:
            deadline = time.monotonic() + 180
            while True:
                try:
                    results = check_results(reports.get(timeout=0.25))
                    break
                except queue.Empty:
                    assert browser.poll() is None, "browser exited"
                    assert time.monotonic() < deadline, "timed out"
    # Chrome skips these.
    flash_tests = [line for line in results.splitlines() if "RealFlashSocket" in line]
    assert flash_tests, results
    assert all(line.endswith("... OK") for line in flash_tests), flash_tests
