"""
The Bluesky stream demo: `/bluesky-stream/` shows a live sample of public
Bluesky posts.  Its client is `js_minerva/demos/bskystream.js`.

While anyone is watching, the server stays connected to Bluesky's Jetstream
(https://bsky.network/docs/jetstream/), which sends every new post as JSON
over a WebSocket.  It skips replies, posts without text, and posts that their
authors labeled (as adult content, say).  It looks up the authors' profiles
(in batches, with a cache) to skip those who asked apps not to show their
posts to logged-out viewers, and those with moderation labels.  Then it sends
each viewer the posts in the language they picked, at most a few a second.

Clients send `["SetPreferences", {"language": "en"}]` (or `null` for all
languages).  They receive `["NewPost", {"url": ..., "handle": ..., "text": ...,
"langs": [...], "media": "2 images" | "video" | null}]`.

This needs the `demos` extra (`twisted[tls,websocket]`).
"""

import importlib.util
import json
import logging
import re
from collections import OrderedDict, deque
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, cast
from urllib.parse import urlencode

from twisted.application.internet import backoffPolicy
from twisted.internet.defer import CancelledError, Deferred, succeed
from twisted.internet.interfaces import IReactorTCP, IReactorTime
from twisted.python.failure import Failure
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers

# Lazy (PEP 810), so that this module imports without the `demos` extra.
lazy from twisted.web.websocket import WebSocketClientEndpoint, WebSocketTransport

from minerva.interfaces import Clock, DelayedCall
from minerva.stream import ServerStream

logger = logging.getLogger(__name__)

# Bluesky's own Jetstream (v2) and public AppView.
JETSTREAM = "wss://jetstream.us-east.bsky.network"
APPVIEW = "https://public.api.bsky.app"
_SUBSCRIBE = (
    "/xrpc/network.bsky.jetstream.subscribeEvents"
    "?collections=app.bsky.feed.post&kinds=commit"
)
USER_AGENT = b"Minerva-demo (+https://github.com/ludios/Minerva)"

_DID = re.compile(r"did:[a-z]+:[A-Za-z0-9._:%-]{1,256}")
_RKEY = re.compile(r"[A-Za-z0-9._:~-]{1,512}")
_HANDLE = re.compile(r"[A-Za-z0-9.-]{1,253}")
_LANGUAGE = re.compile(r"[a-z]{2,3}")


def extra_installed() -> bool:
    """
    Whether the `demos` extra, which this demo needs, is installed.
    """
    return all(
        importlib.util.find_spec(name)
        for name in ("wsproto", "OpenSSL", "service_identity")
    )


def dumps(obj: object) -> str:
    """
    `json.dumps`, but with DEL escaped too, so that the JSON is a restricted
    string (`" "` to `"~"`).
    """
    # DEL can only be in a JSON string, so its escape is valid there.
    return json.dumps(obj).replace("\x7f", r"\u007f")


# --- Posts --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Post:
    did: str
    rkey: str
    text: str
    langs: tuple[str, ...]
    media: str | None

    def url(self) -> str:
        return f"https://bsky.app/profile/{self.did}/post/{self.rkey}"

    def to_string(self, handle: str) -> str:
        return dumps(
            [
                "NewPost",
                {
                    "url": self.url(),
                    "handle": handle,
                    "text": self.text,
                    "langs": self.langs,
                    "media": self.media,
                },
            ]
        )


def _languages(langs: object) -> tuple[str, ...]:
    """
    `["en-US", "ja"]` -> `("en", "ja")`.
    """
    if not isinstance(langs, list):
        return ()
    primary = (
        lang.partition("-")[0].lower() for lang in langs if isinstance(lang, str)
    )
    return tuple(dict.fromkeys(lang for lang in primary if _LANGUAGE.fullmatch(lang)))[
        :3
    ]


def _media(embed: object) -> str | None:
    match embed:
        case {"$type": "app.bsky.embed.recordWithMedia", "media": media}:
            return _media(media)
        case {"$type": "app.bsky.embed.images", "images": list(images)}:
            return f"{len(images)} image{'' if len(images) == 1 else 's'}"
        case {"$type": "app.bsky.embed.video"}:
            return "video"
        case _:
            return None


def parse_event(event: str) -> Post | None:
    """
    Return the new post in the Jetstream `event`, or `None` if it isn't a new
    post that we want to show: a reply, a post without text, or a post with
    content labels.
    """
    try:
        message = json.loads(event)
    except ValueError:
        return None
    match message:
        case {
            "$type": "message",
            "payload": {
                "$type": "network.bsky.jetstream.subscribeEvents#commit",
                "operation": "create",
                "collection": "app.bsky.feed.post",
                "did": str(did),
                "rkey": str(rkey),
                "record": {"text": str(text)} as record,
            },
        } if _DID.fullmatch(did) and _RKEY.fullmatch(rkey):
            pass
        case _:
            return None
    if "reply" in record or record.get("labels") or not text.strip():
        return None
    return Post(
        did=did,
        rkey=rkey,
        # Bluesky allows 300 graphemes, which can be many more characters.
        text=text[:1000],
        langs=_languages(record.get("langs")),
        media=_media(record.get("embed")),
    )


class RateLimiter:
    """
    A token bucket: allows `rate` events a second on average, in bursts of up
    to `burst`.
    """

    def __init__(self, clock: Clock, rate: float, burst: float) -> None:
        self._clock = clock
        self._rate = rate
        self._burst = burst
        self._tokens = burst
        self._updated = clock.seconds()

    def allow(self) -> bool:
        now = self._clock.seconds()
        elapsed = now - self._updated
        self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
        self._updated = now
        if self._tokens < 1:
            return False
        self._tokens -= 1
        return True


# --- Authors ------------------------------------------------------------------------

type FetchProfiles = Callable[[Sequence[str]], Deferred[list[Any]]]


class ProfileLookupFailed(Exception):
    pass


def make_fetch_profiles(
    reactor: IReactorTCP, appview: str, timeout: float = 15
) -> FetchProfiles:
    """
    Return a function that fetches profiles (`app.bsky.actor.defs#profileView
    Detailed`s) from `appview`, for up to 25 DIDs at a time.
    """
    agent = Agent(reactor, connectTimeout=timeout)

    async def fetch(dids: Sequence[str]) -> list[Any]:
        query = urlencode([("actors", did) for did in dids])
        url = f"{appview}/xrpc/app.bsky.actor.getProfiles?{query}"
        headers = Headers({b"user-agent": [USER_AGENT]})
        response = await agent.request(b"GET", url.encode(), headers)
        body = await readBody(response)
        if response.code != 200:
            raise ProfileLookupFailed(f"HTTP {response.code}: {body[:200]!r}")
        match json.loads(body):
            case {"profiles": list(profiles)}:
                return profiles
            case _:
                raise ProfileLookupFailed(f"unexpected response: {body[:200]!r}")

    return lambda dids: Deferred.fromCoroutine(fetch(dids)).addTimeout(
        timeout, cast(IReactorTime, reactor)
    )


class ProfileChecker:
    """
    Finds out whether we may show an author's posts, and their handle.  We
    may if their profile has no labels: no `!no-unauthenticated` (they asked
    apps not to show their posts to logged-out viewers), no adult-content
    labels, and no labels from Bluesky's moderators.

    Looks up profiles in batches, and caches the answers.  If a lookup fails,
    the answer is no.
    """

    # The most that `app.bsky.actor.getProfiles` takes.
    batch_size = 25
    batch_delay = 0.25
    cache_size = 20_000
    cache_time = 15 * 60

    def __init__(self, clock: Clock, fetch_profiles: FetchProfiles) -> None:
        self._clock = clock
        self._fetch_profiles = fetch_profiles
        self._pending: dict[str, list[Deferred[str | None]]] = {}
        self._fetch_call: DelayedCall | None = None
        # DID -> (handle or None, expiry time), least recently used first.
        self._cache: OrderedDict[str, tuple[str | None, float]] = OrderedDict()

    def check(self, did: str) -> Deferred[str | None]:
        """
        Return a `Deferred` that fires with `did`'s handle if we may show their
        posts, else with `None`.
        """
        if (cached := self._cache.get(did)) is not None:
            handle, expiry = cached
            if self._clock.seconds() < expiry:
                self._cache.move_to_end(did)
                return succeed(handle)
            del self._cache[did]
        d: Deferred[str | None] = Deferred()
        self._pending.setdefault(did, []).append(d)
        if len(self._pending) >= self.batch_size:
            self._fetch()
        elif self._fetch_call is None:
            self._fetch_call = self._clock.callLater(self.batch_delay, self._fetch)
        return d

    def _fetch(self) -> None:
        if self._fetch_call is not None and self._fetch_call.active():
            self._fetch_call.cancel()
        self._fetch_call = None
        batch, self._pending = self._pending, {}
        self._fetch_profiles(list(batch)).addCallbacks(
            self._fetched,
            self._fetch_failed,
            callbackArgs=(batch,),
            errbackArgs=(batch,),
        )

    def _fetched(
        self, profiles: list[Any], batch: dict[str, list[Deferred[str | None]]]
    ) -> None:
        handles: dict[str, str] = {}
        for profile in profiles:
            match profile:
                case {"did": str(did), "handle": str(handle)}:
                    if _HANDLE.fullmatch(handle) and not profile.get("labels"):
                        handles[did] = handle
        expiry = self._clock.seconds() + self.cache_time
        for did, waiting in batch.items():
            # Missing profiles (deleted accounts, say) are a no, too.
            handle = handles.get(did)
            self._cache[did] = (handle, expiry)
            for d in waiting:
                d.callback(handle)
        while len(self._cache) > self.cache_size:
            self._cache.popitem(last=False)

    def _fetch_failed(
        self, failure: Failure, batch: dict[str, list[Deferred[str | None]]]
    ) -> None:
        logger.warning(
            "Couldn't look up Bluesky profiles: %s", failure.getErrorMessage()
        )
        for waiting in batch.values():
            for d in waiting:
                d.callback(None)


# --- Jetstream ----------------------------------------------------------------------


class _Abortable(Protocol):
    def abortConnection(self) -> None: ...


class JetstreamProtocol:
    """
    A `twisted.web.websocket.WebSocketProtocol` that passes Jetstream's
    messages on to a `JetstreamClient`.
    """

    # In characters.  Much more than any Jetstream message has.
    max_message_length = 1024 * 1024

    def __init__(self, client: JetstreamClient) -> None:
        self._client = client
        self.transport: WebSocketTransport | None = None
        # The pieces so far of a message that is still arriving.
        self._partial = ""

    def negotiationStarted(self, transport: WebSocketTransport) -> None:
        self.transport = transport

    def negotiationFinished(self) -> None:
        pass

    def textMessageReceived(self, message: str) -> None:
        # Twisted 26.4 calls this once for each piece of a message that
        # arrived in several TCP reads, and doesn't say whether the message is
        # complete.  A Jetstream message is one JSON object, and no proper
        # prefix of a JSON object is valid JSON.  So the message is complete
        # when the pieces so far are valid JSON.
        self._partial += message
        try:
            json.loads(self._partial)
        except ValueError:
            if len(self._partial) > self.max_message_length:
                logger.warning(
                    "Jetstream sent %d characters that aren't a JSON message",
                    len(self._partial),
                )
                self._partial = ""
                self.abort()
            return
        message, self._partial = self._partial, ""
        self._client.message_received(self, message)

    def bytesMessageReceived(self, data: bytes | bytearray) -> None:
        pass

    def pongReceived(self, payload: bytes) -> None:
        pass

    def connectionLost(self, reason: Failure) -> None:
        self._client.connection_lost(self, reason)

    def abort(self) -> None:
        """
        Drop the connection now, even mid-handshake (when the WebSocket
        transport can't send a close frame yet), by aborting the TCP (or TLS)
        connection under it.
        """
        tcp = cast(_Abortable | None, getattr(self.transport, "transport", None))
        if tcp is not None:
            tcp.abortConnection()


type Connect = Callable[[JetstreamClient], Deferred[JetstreamProtocol]]


def connect_to_jetstream(reactor: IReactorTCP, jetstream: str) -> Connect:
    """
    Return a function that connects a `JetstreamClient` to the Jetstream at
    `jetstream` (like `JETSTREAM`), subscribed to new posts.
    """
    endpoint = WebSocketClientEndpoint.new(reactor, jetstream + _SUBSCRIBE)
    return lambda client: Deferred.fromCoroutine(endpoint.connect(client))


_RETRY_DELAY = backoffPolicy(maxDelay=60)


class JetstreamClient:
    """
    While started, stays connected to Jetstream (reconnecting with backoff),
    and calls `message_received` with each message.
    """

    connect_timeout = 30.0
    # Jetstream sends many posts a second, so a long silence means trouble.
    max_silence = 30.0

    def __init__(
        self,
        clock: Clock,
        connect: Connect,
        message_received: Callable[[str], object],
        retry_delay: Callable[[int], float] = _RETRY_DELAY,
    ) -> None:
        self._clock = clock
        self._connect = connect
        self._message_received = message_received
        self._retry_delay = retry_delay
        self._running = False
        self._failures = 0
        self._connecting: Deferred[JetstreamProtocol] | None = None
        self._retry_call: DelayedCall | None = None
        self._silence_call: DelayedCall | None = None
        # The current connection, from before its handshake until it's lost.
        self._protocol: JetstreamProtocol | None = None

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._try_to_connect()

    def stop(self) -> None:
        self._running = False
        if self._retry_call is not None:
            self._retry_call.cancel()
            self._retry_call = None
        if self._connecting is not None:
            self._connecting.cancel()
        self._drop_connection()

    def buildProtocol(self, url: str) -> JetstreamProtocol:
        """
        Called by `WebSocketClientEndpoint`, for which we are the factory.
        """
        self._protocol = JetstreamProtocol(self)
        return self._protocol

    def _try_to_connect(self) -> None:
        self._retry_call = None
        logger.info("Connecting to Jetstream")
        d = self._connecting = self._connect(self)
        d.addTimeout(self.connect_timeout, cast(IReactorTime, self._clock))
        d.addCallbacks(self._connected, self._connect_failed)

    def _connected(self, protocol: JetstreamProtocol) -> None:
        self._connecting = None
        logger.info("Connected to Jetstream")
        self._reset_silence_timer()

    def _connect_failed(self, failure: Failure) -> None:
        self._connecting = None
        self._drop_connection()
        if self._running:
            # (If it was cancelled, connection_lost() already said why.)
            if not failure.check(CancelledError):
                logger.warning("Couldn't connect to Jetstream: %r", failure.value)
            self._retry_later()

    def message_received(self, protocol: JetstreamProtocol, message: str) -> None:
        if protocol is self._protocol:
            self._failures = 0
            self._reset_silence_timer()
            self._message_received(message)

    def connection_lost(self, protocol: JetstreamProtocol, reason: Failure) -> None:
        if protocol is not self._protocol:
            # One that we dropped.
            return
        self._protocol = None
        self._cancel_silence_timer()
        if self._running:
            logger.warning(
                "Lost the connection to Jetstream: %s", reason.getErrorMessage()
            )
        if self._connecting is not None:
            # Lost mid-handshake, when Twisted's `connect()` never finishes;
            # _connect_failed() will retry.
            self._connecting.cancel()
        elif self._running:
            self._retry_later()

    def _silent_too_long(self) -> None:
        self._silence_call = None
        logger.warning("Jetstream sent nothing for %s seconds", self.max_silence)
        self._drop_connection()
        self._retry_later()

    def _drop_connection(self) -> None:
        self._cancel_silence_timer()
        if (protocol := self._protocol) is not None:
            self._protocol = None
            protocol.abort()

    def _retry_later(self) -> None:
        delay = self._retry_delay(self._failures)
        self._failures += 1
        logger.info("Reconnecting to Jetstream in %.1f seconds", delay)
        self._retry_call = self._clock.callLater(delay, self._try_to_connect)

    def _reset_silence_timer(self) -> None:
        self._cancel_silence_timer()
        self._silence_call = self._clock.callLater(
            self.max_silence, self._silent_too_long
        )

    def _cancel_silence_timer(self) -> None:
        if self._silence_call is not None and self._silence_call.active():
            self._silence_call.cancel()
        self._silence_call = None


# --- The demo -----------------------------------------------------------------------


class BskyStreamProtocol:
    """
    A viewer of the stream.
    """

    max_posts_per_second = 4.0

    def __init__(self, factory: BskyStreamFactory) -> None:
        self.factory = factory
        self.stream: ServerStream | None = None
        # The language to show posts in, or None for all.
        self.language: str | None = None
        self._limiter = RateLimiter(
            factory.clock, self.max_posts_per_second, burst=self.max_posts_per_second
        )

    def stream_started(self, stream: ServerStream) -> None:
        self.stream = stream
        self.factory.add_viewer(self)

    def stream_reset(self, reason_string: str, application_level: bool) -> None:
        self.factory.remove_viewer(self)
        self.stream = None

    def string_received(self, s: str) -> None:
        assert self.stream is not None
        try:
            message = json.loads(s)
        except ValueError:
            message = None
        match message:
            case ["SetPreferences", {"language": str() | None as language}] if (
                language is None or _LANGUAGE.fullmatch(language)
            ):
                self.language = language
            case _:
                logger.info("Bad Bluesky stream message: %r", s)
                self.stream.reset("bad bskystream message")

    def wants(self, post: Post) -> bool:
        return self.language is None or self.language in post.langs

    def send_post(self, string: str) -> None:
        """
        Send `string` (a `NewPost` message), unless this viewer has had enough
        posts for now.  If the client is too far behind (perhaps it went away),
        reset the stream instead.
        """
        assert self.stream is not None
        if not self._limiter.allow():
            return
        if self.stream.queue.get_max_consumption() > self.factory.max_queued_bytes:
            self.stream.reset("too much unacknowledged data")
        else:
            self.stream.send_string(string)


class BskyStreamFactory:
    """
    Builds the protocols for the viewers, and feeds them posts from Jetstream
    while there are any.
    """

    max_queued_bytes = 2 * 1024 * 1024

    def __init__(
        self, clock: Clock, connect: Connect, fetch_profiles: FetchProfiles
    ) -> None:
        self.clock = clock
        self.jetstream = JetstreamClient(clock, connect, self._event_received)
        self._profiles = ProfileChecker(clock, fetch_profiles)
        # Posts whose authors are being checked, in Jetstream's order.
        self._checking: deque[_CheckingAuthor] = deque()
        self.viewers: set[BskyStreamProtocol] = set()

    def build_protocol(self) -> BskyStreamProtocol:
        return BskyStreamProtocol(self)

    def add_viewer(self, viewer: BskyStreamProtocol) -> None:
        self.viewers.add(viewer)
        self.jetstream.start()

    def remove_viewer(self, viewer: BskyStreamProtocol) -> None:
        self.viewers.discard(viewer)
        if not self.viewers:
            self.jetstream.stop()

    def _event_received(self, event: str) -> None:
        post = parse_event(event)
        if post is not None and any(viewer.wants(post) for viewer in self.viewers):
            checking = _CheckingAuthor(post)
            self._checking.append(checking)
            self._profiles.check(post.did).addCallback(self._author_checked, checking)

    def _author_checked(self, handle: str | None, checking: _CheckingAuthor) -> None:
        checking.handle = handle
        checking.done = True
        # Send the posts in Jetstream's order, though the checks of their
        # authors may finish in a different order.
        while self._checking and self._checking[0].done:
            done = self._checking.popleft()
            if done.handle is not None:
                self._send(done.post, done.handle)

    def _send(self, post: Post, handle: str) -> None:
        string = post.to_string(handle)
        # Copy the set, because send_post() may reset streams.
        for viewer in list(self.viewers):
            if viewer.wants(post):
                viewer.send_post(string)


@dataclass(slots=True)
class _CheckingAuthor:
    post: Post
    done: bool = False
    # If done: the author's handle, if we may show their posts.
    handle: str | None = None


def make_factory(
    reactor: IReactorTCP, jetstream: str = JETSTREAM, appview: str = APPVIEW
) -> BskyStreamFactory:
    """
    The factory that `minerva-site` uses, connecting to the Jetstream at
    `jetstream` and the AppView at `appview`.
    """
    return BskyStreamFactory(
        cast(Clock, reactor),
        connect_to_jetstream(reactor, jetstream),
        make_fetch_profiles(reactor, appview),
    )
