"""
Run the JavaScript client's own test suite (js_minerva_tests.html, served by
minerva-site) in headless Chrome.  This exercises the uncompiled client against
the server, including real HTTP long-polling and streaming streams.

Skipped unless Chrome, Closure Library, and Coreweb are available.  Set
MINERVA_CLOSURE_LIBRARY and MINERVA_COREWEB to their paths if they aren't next
to this repository.
"""

import os
import re
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.chrome import CHROME, open_page

REPO = Path(__file__).parent.parent
CLOSURE_LIBRARY = Path(
    os.environ.get("MINERVA_CLOSURE_LIBRARY", REPO.parent / "closure-library")
)
COREWEB = Path(os.environ.get("MINERVA_COREWEB", REPO.parent / "Coreweb"))

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(CHROME is None, reason="needs Chrome or Chromium"),
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


def test_js_minerva_tests(site_port: int) -> None:
    with open_page(f"http://127.0.0.1:{site_port}/js_minerva_tests.html") as page:
        summary_pattern = r"/BEGIN-SUMMARY\*\| (.*) \|\*END-SUMMARY/"
        summary = page.wait_for(
            f"(document.body.innerText.match({summary_pattern}) || [])[1]", timeout=180
        )
        results = page.evaluate(
            "document.getElementById('TestRunnerPage-results').innerText"
        )
    tests, errors, failures, skips = map(int, summary.split(","))
    problems = [
        line
        for line in results.splitlines()
        if not line.endswith(("... OK",)) and "SKIP" not in line
    ]
    assert (errors, failures) == (0, 0), "\n".join(problems)
    assert tests > 150
    assert skips < tests / 4
