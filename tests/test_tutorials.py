"""
Drive each tutorial's protocol through a real `ServerStream`.
"""

import json
from collections.abc import Callable
from typing import Any, cast

import pytest
from twisted.internet.interfaces import IReactorTime
from twisted.internet.task import Clock

from minerva.interfaces import StringFactory
from minerva.qan import (
    Notification,
    OkayAnswer,
    Question,
    qan_frame_to_string,
    string_to_qan_frame,
)
from minerva.stream import ServerStream
from minerva.tutorial import (
    standalone_1_rstring,
    standalone_2_unicode,
    standalone_3_json,
    standalone_4_multiaction,
    standalone_5_qan,
    standalone_6_qan_deferred,
)
from tests.mocks import DummySocketLikeTransport


class Client:
    """
    A stream with a transport attached, as if a browser had connected.
    """

    def __init__(self, clock: Clock, factory: StringFactory) -> None:
        self.stream = ServerStream(clock, "a stream id of unusual length", factory)
        self.transport = DummySocketLikeTransport()
        self.stream.transport_online(self.transport, True, None)
        self._seq_num = 0
        self._seen = 0

    def send(self, s: str) -> None:
        self.stream.strings_received(self.transport, [(self._seq_num, s)])
        self._seq_num += 1

    def received(self) -> list[str]:
        strings = [s for _, s in self.stream.queue.iter_items()]
        new, self._seen = strings[self._seen :], len(strings)
        return new

    def received_json(self) -> list[Any]:
        return [json.loads(s) for s in self.received()]


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def connect(clock: Clock) -> Callable[[StringFactory], Client]:
    return lambda factory: Client(clock, factory)


def test_1_rstring(connect: Callable[[StringFactory], Client]) -> None:
    client = connect(standalone_1_rstring.DemoFactory())
    client.send("hello")
    assert client.received() == ["Hey client, you sent me a string with 5 bytes"]


def test_2_unicode(connect: Callable[[StringFactory], Client]) -> None:
    client = connect(standalone_2_unicode.DemoFactory())
    client.send(json.dumps("caf\N{LATIN SMALL LETTER E WITH ACUTE} au lait"))
    assert client.received_json() == [
        "Hey client, you sent me a string with 12 characters; "
        "first word was caf\N{LATIN SMALL LETTER E WITH ACUTE}"
    ]
    client.send(json.dumps(""))
    assert client.received_json() == [
        "Hey client, you sent me a string with 0 characters; first word was "
    ]


def test_3_json(connect: Callable[[StringFactory], Client]) -> None:
    factory = standalone_3_json.DemoFactory()
    alice, bob = connect(factory), connect(factory)
    alice.send(json.dumps("hi"))
    assert alice.received_json() == ["You said: hi"]
    assert bob.received_json() == ["Client #1 said: hi"]


def test_4_multiaction(connect: Callable[[StringFactory], Client]) -> None:
    factory = standalone_4_multiaction.DemoFactory()
    alice, bob = connect(factory), connect(factory)
    alice.send(json.dumps(["broadcast", "hi all"]))
    assert alice.received_json() == ["You told everyone: hi all"]
    assert bob.received_json() == ["Client #1 told everyone: hi all"]

    bob.send(json.dumps(["privmsg", 1, "psst"]))
    assert bob.received_json() == ["You told #1: psst"]
    assert alice.received_json() == ["Client #2 told you: psst"]

    bob.send(json.dumps(["privmsg", 7, "anyone?"]))
    assert bob.received_json() == ["Sorry, #7 isn't connected."]

    bob.send(json.dumps(["dance"]))
    assert bob.received_json() == ["Sorry, I don't understand ['dance']"]


@pytest.mark.parametrize("module", [standalone_5_qan, standalone_6_qan_deferred])
def test_qan(
    clock: Clock, connect: Callable[[StringFactory], Client], module: Any
) -> None:
    factory = (
        module.DemoFactory()
        if module is standalone_5_qan
        else module.DemoFactory(clock)
    )
    alice, bob = connect(factory), connect(factory)

    alice.send(qan_frame_to_string(Notification(json.dumps(["broadcast", "hi"]))))
    clock.advance(0)
    assert alice.received() == [
        qan_frame_to_string(Notification(json.dumps("You told everyone: hi")))
    ]
    assert bob.received() == [
        qan_frame_to_string(Notification(json.dumps("Client #1 told everyone: hi")))
    ]

    bob.send(qan_frame_to_string(Question(json.dumps(["listclients"]), 1)))
    clock.advance(0)
    assert [string_to_qan_frame(s) for s in bob.received()] == [OkayAnswer("[1, 2]", 1)]


def test_6_answers_asynchronously(
    clock: Clock, connect: Callable[[StringFactory], Client]
) -> None:
    client = connect(standalone_6_qan_deferred.DemoFactory(cast(IReactorTime, clock)))
    client.send(qan_frame_to_string(Question(json.dumps(["listclients_in_1_sec"]), 1)))
    clock.advance(0.5)
    assert client.received() == []
    clock.advance(0.5)
    assert [string_to_qan_frame(s) for s in client.received()] == [OkayAnswer("[1]", 1)]
