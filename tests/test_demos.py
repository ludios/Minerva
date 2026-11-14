"""
End-to-end tests for the demos (`minerva.demos`): minerva-site serves them,
with their compiled JavaScript, to headless Chrome.  Skipped if Chrome isn't
installed.
"""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.chrome import CHROME, Page, open_page
from tests.helpers import run_minerva_site

pytestmark = [
    pytest.mark.browser,
    pytest.mark.skipif(CHROME is None, reason="needs Chrome or Chromium"),
]


@pytest.fixture
def site_port(tmp_path: Path) -> Iterator[int]:
    with run_minerva_site(tmp_path / "minerva-site.log") as port:
        yield port


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
