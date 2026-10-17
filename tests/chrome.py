"""
A tiny Chrome DevTools Protocol client, for running pages in headless Chrome
and reading what they produce.
"""

import itertools
import json
import shutil
import subprocess
import tempfile
import time
import urllib.request
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from websockets.sync.client import ClientConnection, connect

CHROME = next(
    filter(None, map(shutil.which, ["google-chrome", "chromium", "chromium-browser"])),
    None,
)


class Page:
    def __init__(self, websocket: ClientConnection) -> None:
        self._websocket = websocket
        self._ids = itertools.count(1)

    def call(self, method: str, **params: Any) -> Any:
        id = next(self._ids)
        self._websocket.send(json.dumps({"id": id, "method": method, "params": params}))
        while True:
            message = json.loads(self._websocket.recv())
            if message.get("id") == id:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message["result"]

    def evaluate(self, expression: str) -> Any:
        result = self.call(
            "Runtime.evaluate", expression=expression, returnByValue=True
        )
        return result["result"].get("value")

    def wait_for(self, expression: str, timeout: float) -> Any:
        """
        Wait until `expression` is truthy, and return its value.
        """
        deadline = time.monotonic() + timeout
        while not (value := self.evaluate(expression)):
            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"{expression!r} still falsy after {timeout} seconds"
                )
            time.sleep(0.25)
        return value


@contextmanager
def open_page(url: str) -> Generator[Page]:
    """
    Open `url` in a new headless Chrome.
    """
    assert CHROME is not None
    # Chrome's child processes may still be writing to the profile on exit.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        port_file = Path(profile) / "DevToolsActivePort"
        command = [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--user-data-dir={profile}",
            "--remote-debugging-port=0",
            "about:blank",
        ]
        with subprocess.Popen(command, stderr=subprocess.DEVNULL) as chrome:
            try:
                while not port_file.exists() or not port_file.read_text().strip():
                    time.sleep(0.05)
                port = int(port_file.read_text().split()[0])
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list") as r:
                    [target] = [t for t in json.load(r) if t["type"] == "page"]
                with connect(
                    target["webSocketDebuggerUrl"], max_size=None
                ) as websocket:
                    page = Page(websocket)
                    page.call("Page.navigate", url=url)
                    yield page
            finally:
                chrome.terminate()
