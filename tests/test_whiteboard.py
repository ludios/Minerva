"""
Tests for `minerva.demos.whiteboard`.
"""

import itertools
import json

import pytest
from twisted.internet.task import Clock

from minerva.demos.whiteboard import (
    ClearBoard,
    InvalidMessage,
    Point,
    WhiteboardFactory,
    WhiteboardProtocol,
    parse_message,
)
from minerva.stream import ServerStream
from tests.mocks import DummySocketLikeTransport

_stream_ids = itertools.count()


class TestParseMessage:
    def test_point(self) -> None:
        assert parse_message(
            '["Point", {"x": 0, "y": 599, "color": "#E06666"}]'
        ) == Point(0, 599, "#E06666")

    def test_fractional_coordinates_are_rounded(self) -> None:
        assert parse_message(
            '["Point", {"x": 10.4, "y": 10.6, "color": "#e06666"}]'
        ) == Point(10, 11, "#e06666")

    def test_clear_board(self) -> None:
        assert parse_message('["ClearBoard", null]') == ClearBoard()

    @pytest.mark.parametrize(
        "message",
        [
            "not JSON",
            "[]",
            '["Point"]',
            '["Point", {"x": 1, "y": 1}]',
            '["Point", {"x": 800, "y": 1, "color": "#E06666"}]',
            '["Point", {"x": 1, "y": -1, "color": "#E06666"}]',
            '["Point", {"x": "1", "y": 1, "color": "#E06666"}]',
            '["Point", {"x": true, "y": 1, "color": "#E06666"}]',
            '["Point", {"x": 1, "y": 1, "color": "red"}]',
            '["Point", {"x": 1, "y": 1, "color": "#E06666\\"><script>"}]',
            '["ClearBoard", {}]',
            '["Erase", null]',
        ],
    )
    def test_invalid(self, message: str) -> None:
        with pytest.raises(InvalidMessage):
            parse_message(message)

    def test_point_round_trips(self) -> None:
        point = Point(1, 2, "#ABCDEF")
        assert parse_message(point.to_string()) == point


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def factory(clock: Clock) -> WhiteboardFactory:
    return WhiteboardFactory(clock)


def connect(clock: Clock, factory: WhiteboardFactory) -> WhiteboardProtocol:
    stream = ServerStream(clock, f"whiteboard-stream-{next(_stream_ids)}", factory)
    stream.transport_online(DummySocketLikeTransport(), True, None)
    protocol = stream._protocol
    assert isinstance(protocol, WhiteboardProtocol)
    return protocol


def sent(protocol: WhiteboardProtocol) -> list[object]:
    assert protocol.stream is not None
    return [json.loads(s) for _, s in protocol.stream.queue.iter_items()]


def point(x: int, y: int, color: str = "#E06666") -> str:
    return json.dumps(["Point", {"x": x, "y": y, "color": color}])


class TestWhiteboard:
    def test_points_go_to_everyone_else(
        self, clock: Clock, factory: WhiteboardFactory
    ) -> None:
        alice, bob = connect(clock, factory), connect(clock, factory)
        alice.string_received(point(1, 2))
        assert sent(alice) == []
        assert sent(bob) == [["Point", {"x": 1, "y": 2, "color": "#E06666"}]]

    def test_new_clients_get_the_board(
        self, clock: Clock, factory: WhiteboardFactory
    ) -> None:
        alice = connect(clock, factory)
        alice.string_received(point(1, 2))
        alice.string_received(point(3, 4, "#000000"))
        # The same point again doesn't need drawing twice.
        alice.string_received(point(1, 2))
        assert sent(connect(clock, factory)) == [
            ["Point", {"x": 1, "y": 2, "color": "#E06666"}],
            ["Point", {"x": 3, "y": 4, "color": "#000000"}],
        ]

    def test_clear_board(self, clock: Clock, factory: WhiteboardFactory) -> None:
        alice, bob = connect(clock, factory), connect(clock, factory)
        alice.string_received(point(1, 2))
        bob.string_received('["ClearBoard", null]')
        assert sent(alice) == [["ClearBoard", None]]
        assert sent(connect(clock, factory)) == []

    def test_board_clears_itself_when_idle(
        self, clock: Clock, factory: WhiteboardFactory
    ) -> None:
        alice, bob = connect(clock, factory), connect(clock, factory)
        alice.string_received(point(1, 2))
        clock.advance(factory.max_inactivity - 1)
        alice.string_received(point(3, 4))
        clock.advance(factory.max_inactivity - 1)
        assert factory.points
        clock.advance(1)
        assert not factory.points
        assert sent(alice)[-1] == sent(bob)[-1] == ["ClearBoard", None]
        # Nothing more to clear (once the streams have sent their strings).
        clock.advance(1)
        assert clock.getDelayedCalls() == []

    def test_full_board_ignores_new_points(
        self, clock: Clock, factory: WhiteboardFactory
    ) -> None:
        factory.max_points = 2
        alice, bob = connect(clock, factory), connect(clock, factory)
        for x in range(3):
            alice.string_received(point(x, 0))
        assert [p.x for p in factory.points] == [0, 1]
        assert len(sent(bob)) == 2

    def test_bad_message_resets_the_stream(
        self, clock: Clock, factory: WhiteboardFactory
    ) -> None:
        alice = connect(clock, factory)
        stream = alice.stream
        assert stream is not None
        alice.string_received('["Point", {"x": 1}]')
        assert stream.disconnected
        assert alice not in factory.protocols

    def test_reset_streams_get_nothing(
        self, clock: Clock, factory: WhiteboardFactory
    ) -> None:
        alice, bob = connect(clock, factory), connect(clock, factory)
        assert bob.stream is not None
        bob.stream.reset("bye")
        assert factory.protocols == {alice}
        # Doesn't try to send to bob's disconnected stream.
        alice.string_received(point(1, 2))

    def test_client_that_falls_too_far_behind_is_reset(
        self, clock: Clock, factory: WhiteboardFactory
    ) -> None:
        factory.max_queued_bytes = 500
        alice, bob = connect(clock, factory), connect(clock, factory)
        bob_stream = bob.stream
        assert bob_stream is not None
        # bob never SACKs, so his queue only grows.
        for x in range(10):
            alice.string_received(point(x, 0))
        assert bob_stream.disconnected
        assert factory.protocols == {alice}
        assert bob_stream.queue.get_max_consumption() <= 500 + 100
