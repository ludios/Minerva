"""
Small helpers shared by the tests.
"""

from collections.abc import Iterator
from itertools import pairwise
from typing import Any

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
