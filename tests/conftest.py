import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from hypothesis import settings

# Twisted-heavy tests can be slow on a loaded machine; don't fail on timing.
settings.register_profile("default", deadline=None)
settings.load_profile("default")


@pytest.fixture(scope="module")
def browser_server_port() -> Iterator[int]:
    """
    Run tests/browser_server.py; yield its HTTP port.  (Per module, because
    the pages see the client ids that its protocols hand out.)
    """
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
