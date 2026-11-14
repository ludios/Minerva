"""
Tests for `minerva.demos.bskystream`.  (tests/test_demos.py runs the demo
end to end, against a fake Jetstream.)
"""

import itertools
import json
from collections.abc import Sequence
from typing import Any

import pytest
from twisted.internet.defer import Deferred, TimeoutError
from twisted.internet.task import Clock
from twisted.python.failure import Failure

from minerva.demos.bskystream import (
    BskyStreamFactory,
    BskyStreamProtocol,
    JetstreamClient,
    JetstreamProtocol,
    Post,
    ProfileChecker,
    RateLimiter,
    dumps,
    parse_event,
)
from minerva.frames import is_restricted_string
from minerva.stream import ServerStream
from tests.helpers import success_result_of
from tests.mocks import DummySocketLikeTransport

_stream_ids = itertools.count()


def event(record: dict[str, Any] | None = None, **payload: Any) -> str:
    """
    A Jetstream (v2) event for a new post, with `record` and `payload` fields
    replaced.
    """
    return json.dumps(
        {
            "$type": "message",
            "payload": {
                "$type": "network.bsky.jetstream.subscribeEvents#commit",
                "cid": "bafyreihifs5i4zugcbjdbo2mzcodbercty4n74heyy4z3lx5l4gpvbi5fu",
                "collection": "app.bsky.feed.post",
                "did": "did:plc:alice",
                "operation": "create",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "createdAt": "2026-10-21T04:40:28.431Z",
                    "langs": ["en"],
                    "text": "Hello, world",
                }
                | (record or {}),
                "rev": "3myedgfltva2r",
                "rkey": "3myedgexaos2f",
                "seq": 26261164305,
                "time": "2026-10-21T04:40:29.266225Z",
            }
            | payload,
        }
    )


def images(n: int) -> dict[str, Any]:
    return {
        "$type": "app.bsky.embed.images",
        "images": [{"alt": "", "image": {}} for _ in range(n)],
    }


class TestParseEvent:
    def test_post(self) -> None:
        assert parse_event(event()) == Post(
            did="did:plc:alice",
            rkey="3myedgexaos2f",
            text="Hello, world",
            langs=("en",),
            media=None,
        )

    @pytest.mark.parametrize(
        ("langs", "expected"),
        [
            (["en-US", "ja"], ("en", "ja")),
            (["EN", "en-GB"], ("en",)),
            (["x", 5, "toolong", "de"], ("de",)),
            (["en", "ja", "ko", "de"], ("en", "ja", "ko")),
            ("en", ()),
            (None, ()),
        ],
    )
    def test_languages(self, langs: object, expected: tuple[str, ...]) -> None:
        post = parse_event(event({"langs": langs}))
        assert post is not None
        assert post.langs == expected

    @pytest.mark.parametrize(
        ("embed", "media"),
        [
            (images(1), "1 image"),
            (images(2), "2 images"),
            (
                {"$type": "app.bsky.embed.recordWithMedia", "media": images(3)},
                "3 images",
            ),
            ({"$type": "app.bsky.embed.video", "video": {}}, "video"),
            ({"$type": "app.bsky.embed.external", "external": {}}, None),
        ],
    )
    def test_media(self, embed: dict[str, Any], media: str | None) -> None:
        post = parse_event(event({"embed": embed}))
        assert post is not None
        assert post.media == media

    def test_long_text_is_cut(self) -> None:
        post = parse_event(event({"text": "x" * 5000}))
        assert post is not None
        assert len(post.text) == 1000

    @pytest.mark.parametrize(
        "unwanted",
        [
            event({"reply": {"parent": {}, "root": {}}}),
            event({"labels": {"values": [{"val": "porn"}]}}),
            event({"text": " \n "}),
            event({"text": None}),
            event(operation="delete"),
            event(collection="app.bsky.feed.like"),
            event(did="did:plc:<script>"),
            event(rkey="../../etc"),
            json.dumps({"$type": "message", "payload": {"$type": "...#identity"}}),
            # Jetstream v1's format.
            json.dumps({"did": "did:plc:alice", "kind": "commit", "commit": {}}),
            "not JSON",
        ],
    )
    def test_unwanted(self, unwanted: str) -> None:
        assert parse_event(unwanted) is None


def test_post_to_string_is_restricted() -> None:
    post = Post(
        "did:plc:alice",
        "3abc",
        "caf\N{LATIN SMALL LETTER E WITH ACUTE}\x7f\n",
        ("fr",),
        None,
    )
    string = post.to_string("alice.test")
    assert is_restricted_string(string)
    assert json.loads(string) == [
        "NewPost",
        {
            "url": "https://bsky.app/profile/did:plc:alice/post/3abc",
            "handle": "alice.test",
            "text": "caf\N{LATIN SMALL LETTER E WITH ACUTE}\x7f\n",
            "langs": ["fr"],
            "media": None,
        },
    ]


def test_dumps_escapes_del() -> None:
    assert dumps("\x7f") == r'"\u007f"'


def test_rate_limiter() -> None:
    clock = Clock()
    limiter = RateLimiter(clock, rate=2, burst=3)
    assert [limiter.allow() for _ in range(4)] == [True, True, True, False]
    clock.advance(0.5)
    assert [limiter.allow() for _ in range(2)] == [True, False]
    clock.advance(100)
    assert [limiter.allow() for _ in range(4)] == [True, True, True, False]


# --- Authors ------------------------------------------------------------------------


def profile(did: str, handle: str, labels: Sequence[str] = ()) -> dict[str, Any]:
    return {
        "did": did,
        "handle": handle,
        "labels": [{"src": did, "val": label} for label in labels],
    }


class FakeAppView:
    """
    Stands in for `make_fetch_profiles`'s function.
    """

    def __init__(self, *profiles: dict[str, Any]) -> None:
        self.profiles = {p["did"]: p for p in profiles}
        self.requests: list[tuple[list[str], Deferred[list[Any]]]] = []

    def fetch(self, dids: Sequence[str]) -> Deferred[list[Any]]:
        d: Deferred[list[Any]] = Deferred()
        self.requests.append((list(dids), d))
        return d

    def respond(self) -> None:
        dids, d = self.requests[-1]
        d.callback([self.profiles[did] for did in dids if did in self.profiles])


class TestProfileChecker:
    @pytest.fixture
    def clock(self) -> Clock:
        return Clock()

    @pytest.fixture
    def appview(self) -> FakeAppView:
        return FakeAppView(
            profile("did:plc:alice", "alice.test"),
            profile("did:plc:bob", "bob.test"),
            profile("did:plc:shy", "shy.test", ["!no-unauthenticated"]),
            profile("did:plc:spam", "spam.test", ["spam"]),
            profile("did:plc:weird", "<b>weird</b>"),
        )

    @pytest.fixture
    def checker(self, clock: Clock, appview: FakeAppView) -> ProfileChecker:
        return ProfileChecker(clock, appview.fetch)

    def test_batches_lookups(
        self, clock: Clock, appview: FakeAppView, checker: ProfileChecker
    ) -> None:
        dids = ["did:plc:alice", "did:plc:bob", "did:plc:alice"]
        results = [checker.check(did) for did in dids]
        assert appview.requests == []
        clock.advance(checker.batch_delay)
        [(requested, _)] = appview.requests
        assert requested == ["did:plc:alice", "did:plc:bob"]
        appview.respond()
        assert [success_result_of(d) for d in results] == [
            "alice.test",
            "bob.test",
            "alice.test",
        ]

    def test_full_batch_is_looked_up_right_away(
        self, appview: FakeAppView, checker: ProfileChecker
    ) -> None:
        for n in range(checker.batch_size + 1):
            checker.check(f"did:plc:user{n}")
        [(requested, _)] = appview.requests
        assert len(requested) == checker.batch_size

    @pytest.mark.parametrize(
        "did",
        [
            "did:plc:shy",  # asked not to be shown to logged-out viewers
            "did:plc:spam",  # has a moderation label
            "did:plc:weird",  # has a bad handle
            "did:plc:gone",  # has no profile
        ],
    )
    def test_no(
        self, clock: Clock, appview: FakeAppView, checker: ProfileChecker, did: str
    ) -> None:
        d = checker.check(did)
        clock.advance(checker.batch_delay)
        appview.respond()
        assert success_result_of(d) is None

    def test_failed_lookup_is_a_no_and_not_cached(
        self, clock: Clock, appview: FakeAppView, checker: ProfileChecker
    ) -> None:
        d = checker.check("did:plc:alice")
        clock.advance(checker.batch_delay)
        appview.requests[-1][1].errback(Failure(ConnectionRefusedError()))
        assert success_result_of(d) is None
        checker.check("did:plc:alice")
        clock.advance(checker.batch_delay)
        assert len(appview.requests) == 2

    def test_caches_answers(
        self, clock: Clock, appview: FakeAppView, checker: ProfileChecker
    ) -> None:
        checker.check("did:plc:alice")
        checker.check("did:plc:shy")
        clock.advance(checker.batch_delay)
        appview.respond()
        assert success_result_of(checker.check("did:plc:alice")) == "alice.test"
        assert success_result_of(checker.check("did:plc:shy")) is None
        assert len(appview.requests) == 1
        clock.advance(checker.cache_time)
        checker.check("did:plc:alice")
        clock.advance(checker.batch_delay)
        assert len(appview.requests) == 2

    def test_cache_forgets_the_least_recently_used(
        self, clock: Clock, appview: FakeAppView, checker: ProfileChecker
    ) -> None:
        checker.cache_size = 2
        for did in ["did:plc:alice", "did:plc:bob"]:
            checker.check(did)
        clock.advance(checker.batch_delay)
        appview.respond()
        checker.check("did:plc:alice")  # now bob is the least recently used
        checker.check("did:plc:shy")
        clock.advance(checker.batch_delay)
        appview.respond()
        checker.check("did:plc:alice")
        clock.advance(checker.batch_delay)
        assert len(appview.requests) == 2
        checker.check("did:plc:bob")
        clock.advance(checker.batch_delay)
        assert len(appview.requests) == 3


# --- Jetstream ----------------------------------------------------------------------


class FakeTcpTransport:
    aborted = False

    def abortConnection(self) -> None:
        self.aborted = True


class FakeWebSocketTransport:
    """
    What `JetstreamProtocol` gets from Twisted: the WebSocket transport, which
    has the TCP transport as `.transport`.
    """

    def __init__(self) -> None:
        self.transport = FakeTcpTransport()


class FakeJetstream:
    """
    Stands in for `connect_to_jetstream`'s function.
    """

    def __init__(self) -> None:
        self.attempts: list[tuple[JetstreamClient, Deferred[JetstreamProtocol]]] = []
        self.protocol: JetstreamProtocol | None = None

    def connect(self, client: JetstreamClient) -> Deferred[JetstreamProtocol]:
        d: Deferred[JetstreamProtocol] = Deferred()
        self.attempts.append((client, d))
        return d

    def tcp_connected(self) -> JetstreamProtocol:
        client, _ = self.attempts[-1]
        self.protocol = client.buildProtocol("wss://jetstream.example/")
        self.protocol.negotiationStarted(FakeWebSocketTransport())  # ty: ignore[invalid-argument-type]
        return self.protocol

    def handshake(self) -> JetstreamProtocol:
        protocol = self.tcp_connected()
        _, d = self.attempts[-1]
        d.callback(protocol)
        protocol.negotiationFinished()
        return protocol

    @property
    def aborted(self) -> bool:
        assert self.protocol is not None
        transport = self.protocol.transport
        assert isinstance(transport, FakeWebSocketTransport)
        return transport.transport.aborted


class TestJetstreamClient:
    @pytest.fixture
    def clock(self) -> Clock:
        return Clock()

    @pytest.fixture
    def jetstream(self) -> FakeJetstream:
        return FakeJetstream()

    @pytest.fixture
    def messages(self) -> list[str]:
        return []

    @pytest.fixture
    def client(
        self, clock: Clock, jetstream: FakeJetstream, messages: list[str]
    ) -> JetstreamClient:
        # Retry after 10 seconds, then 20, 30, ...
        return JetstreamClient(
            clock, jetstream.connect, messages.append, lambda n: 10.0 * (n + 1)
        )

    def test_passes_on_messages(
        self, client: JetstreamClient, jetstream: FakeJetstream, messages: list[str]
    ) -> None:
        client.start()
        client.start()
        assert len(jetstream.attempts) == 1
        jetstream.handshake().textMessageReceived("hi")
        assert messages == ["hi"]

    def test_reconnects_with_backoff(
        self,
        clock: Clock,
        client: JetstreamClient,
        jetstream: FakeJetstream,
        messages: list[str],
    ) -> None:
        client.start()
        jetstream.handshake().connectionLost(Failure(ConnectionError()))
        clock.advance(9.9)
        assert len(jetstream.attempts) == 1
        clock.advance(0.1)
        assert len(jetstream.attempts) == 2
        jetstream.attempts[-1][1].errback(Failure(ConnectionRefusedError()))
        clock.advance(19.9)
        assert len(jetstream.attempts) == 2
        clock.advance(0.1)
        assert len(jetstream.attempts) == 3
        # A message means the connection works, so the backoff starts over.
        protocol = jetstream.handshake()
        protocol.textMessageReceived("hi")
        protocol.connectionLost(Failure(ConnectionError()))
        clock.advance(10)
        assert len(jetstream.attempts) == 4

    def test_reconnects_when_jetstream_goes_quiet(
        self,
        clock: Clock,
        client: JetstreamClient,
        jetstream: FakeJetstream,
        messages: list[str],
    ) -> None:
        client.start()
        protocol = jetstream.handshake()
        clock.advance(client.max_silence - 1)
        protocol.textMessageReceived("hi")
        clock.advance(client.max_silence - 1)
        assert not jetstream.aborted
        clock.advance(1)
        assert jetstream.aborted
        # The aborted connection can't deliver messages or cause more retries.
        protocol.textMessageReceived("late")
        protocol.connectionLost(Failure(ConnectionError()))
        assert messages == ["hi"]
        clock.advance(10)
        assert len(jetstream.attempts) == 2
        clock.advance(1000)
        assert len(jetstream.attempts) == 2

    def test_connection_lost_mid_handshake(
        self, clock: Clock, client: JetstreamClient, jetstream: FakeJetstream
    ) -> None:
        """
        Twisted's `WebSocketClientEndpoint.connect` never finishes if the
        connection is lost during the handshake, so the client notices.
        """
        client.start()
        jetstream.tcp_connected().connectionLost(Failure(ConnectionError()))
        clock.advance(10)
        assert len(jetstream.attempts) == 2

    def test_handshake_timeout(
        self, clock: Clock, client: JetstreamClient, jetstream: FakeJetstream
    ) -> None:
        client.start()
        jetstream.tcp_connected()
        clock.advance(client.connect_timeout)
        assert jetstream.aborted
        assert jetstream.attempts[0][1].called
        clock.advance(10)
        assert len(jetstream.attempts) == 2

    def test_stop_while_connecting(
        self, clock: Clock, client: JetstreamClient, jetstream: FakeJetstream
    ) -> None:
        client.start()
        jetstream.tcp_connected()
        client.stop()
        assert jetstream.aborted
        clock.advance(1000)
        assert len(jetstream.attempts) == 1
        assert clock.getDelayedCalls() == []

    def test_stop_while_connected(
        self,
        clock: Clock,
        client: JetstreamClient,
        jetstream: FakeJetstream,
        messages: list[str],
    ) -> None:
        client.start()
        protocol = jetstream.handshake()
        client.stop()
        assert jetstream.aborted
        protocol.connectionLost(Failure(ConnectionError()))
        clock.advance(1000)
        assert len(jetstream.attempts) == 1
        assert clock.getDelayedCalls() == []
        # It can start again.
        client.start()
        jetstream.handshake().textMessageReceived("hi")
        assert messages == ["hi"]

    def test_stop_while_waiting_to_retry(
        self, clock: Clock, client: JetstreamClient, jetstream: FakeJetstream
    ) -> None:
        client.start()
        jetstream.attempts[-1][1].errback(Failure(TimeoutError()))
        client.stop()
        clock.advance(1000)
        assert len(jetstream.attempts) == 1


# --- The demo -----------------------------------------------------------------------


class TestBskyStream:
    @pytest.fixture
    def clock(self) -> Clock:
        return Clock()

    @pytest.fixture
    def jetstream(self) -> FakeJetstream:
        return FakeJetstream()

    @pytest.fixture
    def appview(self) -> FakeAppView:
        return FakeAppView(
            profile("did:plc:alice", "alice.test"),
            profile("did:plc:bob", "bob.test"),
            profile("did:plc:shy", "shy.test", ["!no-unauthenticated"]),
        )

    @pytest.fixture
    def factory(
        self, clock: Clock, jetstream: FakeJetstream, appview: FakeAppView
    ) -> BskyStreamFactory:
        return BskyStreamFactory(clock, jetstream.connect, appview.fetch)

    def connect(self, clock: Clock, factory: BskyStreamFactory) -> BskyStreamProtocol:
        stream = ServerStream(clock, f"bsky-stream-{next(_stream_ids)}", factory)
        stream.transport_online(DummySocketLikeTransport(), True, None)
        protocol = stream._protocol
        assert isinstance(protocol, BskyStreamProtocol)
        return protocol

    def posts(self, viewer: BskyStreamProtocol) -> list[str]:
        """
        The texts of the posts that `viewer` was sent.
        """
        assert viewer.stream is not None
        return [json.loads(s)[1]["text"] for _, s in viewer.stream.queue.iter_items()]

    def deliver(
        self,
        clock: Clock,
        jetstream: FakeJetstream,
        appview: FakeAppView,
        *events: str,
    ) -> None:
        """
        Send `events` from Jetstream, and answer the profile lookup.
        """
        assert jetstream.protocol is not None
        requests = len(appview.requests)
        for e in events:
            jetstream.protocol.textMessageReceived(e)
        clock.advance(ProfileChecker.batch_delay)
        if len(appview.requests) > requests:
            appview.respond()

    def test_connects_to_jetstream_only_while_watched(
        self, clock: Clock, factory: BskyStreamFactory, jetstream: FakeJetstream
    ) -> None:
        assert not factory.jetstream.running
        alice = self.connect(clock, factory)
        bob = self.connect(clock, factory)
        assert factory.jetstream.running
        assert len(jetstream.attempts) == 1
        jetstream.handshake()
        assert alice.stream is not None
        assert bob.stream is not None
        alice.stream.reset("bye")
        assert factory.jetstream.running
        bob.stream.reset("bye")
        assert not factory.jetstream.running
        assert jetstream.aborted

    def test_sends_posts(
        self,
        clock: Clock,
        factory: BskyStreamFactory,
        jetstream: FakeJetstream,
        appview: FakeAppView,
    ) -> None:
        viewer = self.connect(clock, factory)
        jetstream.handshake()
        self.deliver(
            clock,
            jetstream,
            appview,
            event({"text": "one"}),
            event({"text": "a reply", "reply": {}}),
            event({"text": "shy", "embed": images(2)}, did="did:plc:shy"),
            event({"text": "two", "embed": images(2)}, did="did:plc:bob"),
        )
        assert viewer.stream is not None
        assert [json.loads(s) for _, s in viewer.stream.queue.iter_items()] == [
            [
                "NewPost",
                {
                    "url": "https://bsky.app/profile/did:plc:alice/post/3myedgexaos2f",
                    "handle": "alice.test",
                    "text": "one",
                    "langs": ["en"],
                    "media": None,
                },
            ],
            [
                "NewPost",
                {
                    "url": "https://bsky.app/profile/did:plc:bob/post/3myedgexaos2f",
                    "handle": "bob.test",
                    "text": "two",
                    "langs": ["en"],
                    "media": "2 images",
                },
            ],
        ]

    def test_language_preference(
        self,
        clock: Clock,
        factory: BskyStreamFactory,
        jetstream: FakeJetstream,
        appview: FakeAppView,
    ) -> None:
        everything = self.connect(clock, factory)
        japanese = self.connect(clock, factory)
        japanese.string_received('["SetPreferences", {"language": "ja"}]')
        jetstream.handshake()
        self.deliver(
            clock,
            jetstream,
            appview,
            event({"text": "hello", "langs": ["en"]}),
            event({"text": "konnichiwa", "langs": ["ja", "en"]}),
            event({"text": "?", "langs": []}),
        )
        assert self.posts(everything) == ["hello", "konnichiwa", "?"]
        assert self.posts(japanese) == ["konnichiwa"]
        japanese.string_received('["SetPreferences", {"language": null}]')
        self.deliver(clock, jetstream, appview, event({"text": "hi again"}))
        assert self.posts(japanese) == ["konnichiwa", "hi again"]

    def test_keeps_jetstreams_order(
        self,
        clock: Clock,
        factory: BskyStreamFactory,
        jetstream: FakeJetstream,
        appview: FakeAppView,
    ) -> None:
        """
        Posts by authors whose profiles are cached don't overtake posts that
        are waiting for a lookup.
        """
        viewer = self.connect(clock, factory)
        jetstream.handshake()
        self.deliver(clock, jetstream, appview, event({"text": "alice 1"}))
        assert jetstream.protocol is not None
        jetstream.protocol.textMessageReceived(
            event({"text": "bob"}, did="did:plc:bob")
        )
        jetstream.protocol.textMessageReceived(event({"text": "alice 2"}))
        assert self.posts(viewer) == ["alice 1"]
        clock.advance(ProfileChecker.batch_delay)
        appview.respond()
        assert self.posts(viewer) == ["alice 1", "bob", "alice 2"]

    def test_unwanted_posts_need_no_lookups(
        self,
        clock: Clock,
        factory: BskyStreamFactory,
        jetstream: FakeJetstream,
        appview: FakeAppView,
    ) -> None:
        viewer = self.connect(clock, factory)
        viewer.string_received('["SetPreferences", {"language": "ja"}]')
        jetstream.handshake()
        self.deliver(clock, jetstream, appview, event({"langs": ["en"]}))
        assert appview.requests == []

    def test_viewers_get_a_few_posts_a_second(
        self,
        clock: Clock,
        factory: BskyStreamFactory,
        jetstream: FakeJetstream,
        appview: FakeAppView,
    ) -> None:
        viewer = self.connect(clock, factory)
        jetstream.handshake()
        burst = int(viewer.max_posts_per_second)
        self.deliver(
            clock, jetstream, appview, *(event({"text": str(n)}) for n in range(10))
        )
        assert len(self.posts(viewer)) == burst
        clock.advance(1)
        self.deliver(clock, jetstream, appview, event({"text": "later"}))
        assert self.posts(viewer)[-1] == "later"

    @pytest.mark.parametrize(
        "message",
        [
            "not JSON",
            '["SetPreferences", {"language": "English"}]',
            '["SetPreferences", {}]',
            '["Subscribe", "everything"]',
        ],
    )
    def test_bad_message_resets_the_stream(
        self, clock: Clock, factory: BskyStreamFactory, message: str
    ) -> None:
        viewer = self.connect(clock, factory)
        stream = viewer.stream
        assert stream is not None
        viewer.string_received(message)
        assert stream.disconnected
        assert not factory.viewers
        assert not factory.jetstream.running

    def test_viewer_that_falls_too_far_behind_is_reset(
        self,
        clock: Clock,
        factory: BskyStreamFactory,
        jetstream: FakeJetstream,
        appview: FakeAppView,
    ) -> None:
        factory.max_queued_bytes = 300
        viewer = self.connect(clock, factory)
        stream = viewer.stream
        assert stream is not None
        jetstream.handshake()
        # The viewer never SACKs, so its queue only grows.
        for n in range(3):
            self.deliver(clock, jetstream, appview, event({"text": str(n)}))
            clock.advance(1)
        assert stream.disconnected
