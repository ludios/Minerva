# Changes

## 26.10.0: the Python 3.15 port

The server was ported from Python 2 to Python 3.15.  The wire protocol and
the JavaScript client are unchanged: the compiled 2012 client is tested against
the new server in headless Chrome.

### Project

- Packaged with `pyproject.toml` and [uv](https://docs.astral.sh/uv/) (src
  layout), instead of `setup.py`.  Requires Python 3.15.
- Type-annotated throughout, and checked with ty and ruff.  The tests are
  pytest-native, with hypothesis property tests for the frame codecs, framers,
  send/receive windows, and validation.
- Dependencies are just Twisted and Jinja2.  Gone: Securetypes (Python's hash
  randomization makes it moot), Strfrag (`bytearray` buffers), simplejson,
  Pyquitter, Refbinder, Brequire, Webmagic (the few bits used were inlined),
  and Coreweb's Python code (its JavaScript is still used by the uncompiled
  client).  zope.interface is used only where Twisted needs it; Minerva's own
  interfaces are `typing.Protocol`s.
- Logging uses the standard library's `logging`.
- `minerva.mserver` was split into `minerva.stream`, `minerva.transport`,
  `minerva.web`, and `minerva.protocols`; `minerva.mutils` is gone.  The public
  API is importable from `minerva` itself.
- The `twistd minerva_site` plugin is replaced by a `minerva-site` command
  (`uv run minerva-site --http ENDPOINT --minerva ENDPOINT`), which takes
  Twisted endpoint descriptions.  It doesn't daemonize; use systemd or
  similar.  It has a new `--coreweb PATH` option, and its Flash policy file
  lists the ports it actually listens on.  Auto-reloading (Pyquitter) is gone;
  use a tool like `watchfiles` instead.
- The tutorials run with `python -m minerva.tutorial.standalone_N_...`.
- Build scripts moved to `scripts/` and were ported to Python 3.

### API

- Everything Minerva owns is snake_case: `ServerStream.send_string`,
  `notify_finish`, `StreamTracker.get_stream`, ...  Methods implementing
  Twisted interfaces (`dataReceived`, `registerProducer`, `pauseProducing`,
  ...) keep Twisted's names.
- Your protocols implement `stream_started`, `stream_reset`, and
  `string_received`, and optionally `transport_created` and
  `transport_destroyed`.  The `stringsReceived` (plural) optimization is gone.
  Your factory implements `build_protocol`.
- Minerva strings are `str`s (still restricted to `" "` to `"~"`).
- Frames, SACKs, `TransportInfo`, and QAN frames are frozen dataclasses with
  snake_case fields; transport kill reasons are a `KillReason` enum.
- QAN: bodies are `str`s.  `body_received` may be an `async def` (or return
  a Deferred).  `KnownError(body)` and `UnknownError(body)` have a `.body`.
- `ServerStream.reset()` checks that its reason is a restricted string of at
  most 255 characters.
- `ServerTransportFactory`'s policy string is a `str`.
- The framers (`minerva.decoders`) raise `FrameTooLong`, instead of returning
  status codes.
- `htmldumps` escapes `<`, `>`, and `&` (instead of `/`).

### Behavior

- When a protocol's `string_received` raises, the exception is logged and the
  remaining strings are still delivered.  (Before, the rest of the batch was
  silently dropped, although it had been acknowledged.)  When a protocol
  resets its stream, it gets no more strings.
- Strings that arrive in the same batch as (but before) an invalid frame or
  a bad SACK are now delivered and acknowledged before the transport is
  killed.  (Before, this crashed.)
- After a primary-transport switch, a registered push producer is no longer
  left paused forever.  A client aborting a streaming HTTP request while a
  producer is registered no longer leaves the stream wedged.
- A protocol may reset the stream from `transport_destroyed` during a
  transport switch (before, this raised an `AssertionError`), and a transport
  that attaches to a stream that died meanwhile gets a reset frame instead
  of silence.
- QAN: when the stream resets, the answers still being worked out for the
  peer's questions are cancelled, and late answers are dropped quietly.
- `StreamTracker.stop()` stops its periodic check for abandoned streams.
- A bad QAN frame now resets the stream as intended.  (Before, it raised a
  `NameError`.)
- Hello frames with huge numbers (like `1e999`), and reset frames without a
  `|`, are now rejected as invalid.  (Before, they raised exceptions that
  escaped the frame decoder.)  Strict number parsing no longer accepts a
  trailing newline or non-ASCII digits.  Frames that contain non-ASCII bytes
  are invalid.
- QAN: `fail_all()` no longer crashes on questions that were already
  cancelled.  A question answered with something other than a `str` gets an
  error-answer, rather than no answer at all.
- A retransmitted string that was already waiting in the receive window (for
  an earlier gap to fill) was counted again, inflating the window's size and
  possibly killing the transport for a false overflow.  It's now ignored.
- An HTTP request whose body has no complete hello frame is answered right
  away (with a transport kill frame), instead of hanging until the client
  gives up.
- If the protocol factory raises, the stream is reset, instead of keeping
  the transport attached forever.
- Uploads over HTTP transports that don't receive strings now count as
  activity, so the stream isn't reset as idle.
- A client can't push sequence numbers past 2**53.
- `notify_finish()` on a finished stream returns an already-fired Deferred.
- The `xdrframe` page responds with 400 Bad Request for a bad `id` or
  `domain`, rather than an internal server error.
