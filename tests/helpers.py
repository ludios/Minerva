"""
Small helpers shared by the tests.
"""

import re
import subprocess
import sys
import time
from collections.abc import Generator, Iterator, Sequence
from contextlib import contextmanager
from itertools import pairwise
from pathlib import Path
from typing import Any

from twisted.internet.defer import Deferred
from twisted.python.failure import Failure

from minerva.frames import HelloFrame, HttpFormat
from minerva.window import SACK


def dice(data: bytes, size: int) -> Iterator[bytes]:
    """
    Split `data` into consecutive pieces of (at most) `size` bytes.
    """
    for at in range(0, len(data), size):
        yield data[at : at + size]


def split_at(data: bytes, cuts: list[int]) -> list[bytes]:
    """
    Split `data` at the (sorted, possibly repeated) offsets in `cuts`.
    """
    bounds = [0, *cuts, len(data)]
    return [data[a:b] for a, b in pairwise(bounds)]


def make_hello(**overrides: Any) -> HelloFrame:
    """
    A valid `HelloFrame` (for a new stream, over a socket-like transport),
    with any fields replaced by `overrides`.
    """
    fields: dict[str, Any] = {
        "transport_number": 0,
        "request_new_stream": True,
        "stream_id": "x" * 26,
        "streaming_response": True,
        "max_receive_bytes": 2**30,
        "max_open_time": 2**30,
        "max_inactivity": 0,
        "last_sack_seen_by_client": SACK(-1, ()),
    }
    return HelloFrame(**(fields | overrides))


def make_http_hello(**overrides: Any) -> HelloFrame:
    """
    Like `make_hello`, but for an HTTP transport.
    """
    return make_hello(
        **({"http_format": HttpFormat.XHR, "streaming_response": False} | overrides)
    )


class ListLog[T](list[T]):
    """
    A list that remembers how much of it you've already looked at:

        log = ListLog()
        log.append("one")
        log.append("two")
        assert log.get_new() == ["one", "two"]
        log.append("three")
        assert log.get_new() == ["three"]
    """

    _seen = 0

    def get_new(self) -> list[T]:
        new = self[self._seen :]
        self._seen = len(self)
        return new


def _result_of[T](d: Deferred[T]) -> T | Failure:
    results: list[T | Failure] = []
    d.addBoth(results.append)
    if not results:
        raise AssertionError(f"{d!r} has no result yet")
    return results[0]


def success_result_of[T](d: Deferred[T]) -> T:
    """
    Return the result of the already-fired `d`, which must have succeeded.
    """
    result = _result_of(d)
    if isinstance(result, Failure):
        raise AssertionError(f"{d!r} failed: {result.getTraceback()}")
    return result


def failure_result_of[E: BaseException](d: Deferred[Any], expected: type[E]) -> E:
    """
    Return the exception that the already-fired `d` failed with, which must
    be an `expected`.
    """
    result = _result_of(d)
    if not isinstance(result, Failure):
        raise AssertionError(f"{d!r} succeeded with {result!r}")
    if not isinstance(result.value, expected):
        raise AssertionError(f"{d!r} failed unexpectedly: {result.getTraceback()}")
    return result.value


@contextmanager
def run_minerva_site(log: Path, args: Sequence[str] = ()) -> Generator[int]:
    """
    Run minerva-site on ephemeral ports, with the extra `args`, logging to
    `log`.  Yield its HTTP port.
    """
    command = [sys.executable, "-m", "minerva.site"]
    command += ["--http", "tcp:0:interface=127.0.0.1"]
    command += ["--minerva", "tcp:0:interface=127.0.0.1", *args]
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
