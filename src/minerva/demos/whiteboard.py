"""
The whiteboard demo: everyone viewing `/whiteboard/` draws colored points on
the same board.  Its client is `js_minerva/demos/whiteboard.js`.

Clients send, and receive, JSON messages:

- `["Point", {"x": X, "y": Y, "color": "#RRGGBB"}]`: someone added a point.
- `["ClearBoard", null]`: someone cleared the board.
"""

import json
import logging
import re
from dataclasses import dataclass

from minerva.interfaces import Clock, DelayedCall
from minerva.stream import ServerStream

logger = logging.getLogger(__name__)

WIDTH = 800
HEIGHT = 600
_COLOR = re.compile(r"#[0-9A-Fa-f]{6}")


@dataclass(frozen=True, slots=True)
class Point:
    x: int
    y: int
    color: str

    def to_string(self) -> str:
        return json.dumps(["Point", {"x": self.x, "y": self.y, "color": self.color}])


@dataclass(frozen=True, slots=True)
class ClearBoard:
    def to_string(self) -> str:
        return json.dumps(["ClearBoard", None])


type Message = Point | ClearBoard


class InvalidMessage(Exception):
    pass


def parse_message(s: str) -> Message:
    """
    Parse a message from a client.  Raises `InvalidMessage`.
    """
    try:
        message = json.loads(s)
    except ValueError:
        raise InvalidMessage("not JSON") from None
    match message:
        # Browsers may report fractional coordinates (on zoomed pages, say).
        case [
            "Point",
            {"x": int() | float() as x, "y": int() | float() as y, "color": str(color)},
        ] if (
            not isinstance(x, bool)
            and not isinstance(y, bool)
            and 0 <= x < WIDTH
            and 0 <= y < HEIGHT
            and _COLOR.fullmatch(color)
        ):
            # Rounding a coordinate in the board's last half pixel would leave
            # the board.
            return Point(min(round(x), WIDTH - 1), min(round(y), HEIGHT - 1), color)
        case ["ClearBoard", None]:
            return ClearBoard()
        case _:
            raise InvalidMessage(f"bad message: {s!r}")


class WhiteboardProtocol:
    def __init__(self, factory: WhiteboardFactory) -> None:
        self.factory = factory
        self.stream: ServerStream | None = None

    def stream_started(self, stream: ServerStream) -> None:
        self.stream = stream
        self.factory.protocols.add(self)
        for point in self.factory.points:
            self.send(point.to_string())

    def stream_reset(self, reason_string: str, application_level: bool) -> None:
        self.factory.protocols.discard(self)
        self.stream = None

    def string_received(self, s: str) -> None:
        assert self.stream is not None
        try:
            message = parse_message(s)
        except InvalidMessage:
            logger.info("Bad whiteboard message: %r", s)
            self.stream.reset("bad whiteboard message")
            return
        match message:
            case Point():
                self.factory.add_point(message, sender=self)
            case ClearBoard():
                self.factory.clear_board(sender=self)

    def send(self, string: str) -> None:
        """
        Send `string`, unless the client is too far behind (perhaps it went
        away), in which case reset the stream.
        """
        assert self.stream is not None
        if self.stream.queue.get_max_consumption() > self.factory.max_queued_bytes:
            self.stream.reset("too much unacknowledged data")
        else:
            self.stream.send_string(string)


class WhiteboardFactory:
    """
    Keeps the board, and tells every client about every change.  Clears the
    board after `max_inactivity` seconds without a change.
    """

    max_inactivity = 20 * 60
    # Enough points to cover the board several times over.
    max_points = 10_000
    max_queued_bytes = 2 * 1024 * 1024

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self.protocols: set[WhiteboardProtocol] = set()
        # Ordered, so that new clients draw overlapping points the same way.
        self.points: dict[Point, None] = {}
        self._clear_call: DelayedCall | None = None

    def build_protocol(self) -> WhiteboardProtocol:
        return WhiteboardProtocol(self)

    def add_point(self, point: Point, sender: WhiteboardProtocol | None = None) -> None:
        if len(self.points) >= self.max_points:
            logger.info("The whiteboard is full; ignoring %r", point)
            return
        # A point that is drawn again goes to the end, because every client
        # draws it on top of the points since.
        self.points.pop(point, None)
        self.points[point] = None
        self._broadcast(point, sender)
        self._cancel_clear_call()
        self._clear_call = self._clock.callLater(self.max_inactivity, self.clear_board)

    def clear_board(self, sender: WhiteboardProtocol | None = None) -> None:
        self.points.clear()
        self._broadcast(ClearBoard(), sender)
        self._cancel_clear_call()

    def _broadcast(self, message: Message, sender: WhiteboardProtocol | None) -> None:
        string = message.to_string()
        # The sender already drew it.  (Copy the set, because send() may
        # reset streams.)
        for protocol in [p for p in self.protocols if p is not sender]:
            protocol.send(string)

    def _cancel_clear_call(self) -> None:
        if self._clear_call is not None and self._clear_call.active():
            self._clear_call.cancel()
        self._clear_call = None
