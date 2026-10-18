"""
End-to-end tests: the compiled JavaScript client in headless Chrome, talking
to the server over HTTP long-polling.  Skipped if Chrome isn't installed.
"""

import pytest

from tests.chrome import CHROME, open_page

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(CHROME is None, reason="needs Chrome or Chromium"),
]


def browse(url: str, last_line: str) -> list[str]:
    """
    Load `url`, wait until the page logs `last_line` to #output, and return
    all the lines it logged.
    """
    output = "document.getElementById('output').innerText"
    with open_page(url) as page:
        page.wait_for(f"{output}.includes({last_line!r})", timeout=30)
        return page.evaluate(output).splitlines()


def test_strings(browser_server_port: int) -> None:
    assert browse(f"http://127.0.0.1:{browser_server_port}/strings", "reset: done") == [
        "started",
        "got: Hey client, you sent me a string with 5 bytes",
        "got: Hey client, you sent me a string with 14 bytes",
        "reset: done",
    ]


def test_qan_with_async_answer(browser_server_port: int) -> None:
    assert browse(f"http://127.0.0.1:{browser_server_port}/qan", "reset: done") == [
        "started",
        "answer: [1]",
        "reset: done",
    ]
