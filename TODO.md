# Python 3.15 port — working TODO

> **Note to self (Claude):** always work off this file.  After any context
> compaction, re-read it first.  Tick boxes as you go, add notes under
> "Decisions" / "Behavior changes", and commit often on the `python3` branch.
> `XXX(port):` comments in code mark spots that need a second pass.

## The ask (from the user, AFK)

- Full conversion of the Python 2 code to Python 3.15.  Aims: (1) show what
  really good, modern Python 3.15 looks like; (2) let them play with the project.
- Modernize freely; snake_case where possible; spaces OK.
- Remove/replace: Securetypes, Strfrag, simplejson, Pyquitter, Refbinder (and
  anything else unneeded: zope.interface for our own interfaces, Webmagic,
  Coreweb's Python bits, brequire, twistd plugin).
- Keep **all** transports, including the Flash socket one.
- uv, type annotations, must pass `ty` and `ruff`.  Property tests (hypothesis)
  where they fit.
- JavaScript: leave mostly untouched; pull in old Closure Library/Compiler as
  needed.  (`js_minerva/cw/net/qan.ts` is the user's own untracked WIP — don't
  touch/commit it.  Same for other untracked files: patches, `_start_dev*`,
  `dev_keys/`, `newdoc/`, `minerva/_standalone_with_transportCreated.py`
  (kept at its original path; the root `minerva/` dir now holds only that).
  **Never `git add -A`; never `git checkout --` a dir with new files.**)
  The py2 `.pyc` files were moved to `~/minerva-py2-pyc-backup/`.
- Consult Fable (`claude -p --model claude-fable-5-1`) / Astra (`codex exec`)
  if needed.  Don't AskUserQuestion.  Commit as you go.

## Environment notes (NixOS!)

- uv-managed CPython can't run (no nix-ld).  Use nixpkgs Python:
  `/nix/store/lcfvy379m5j0parmzhs1icf6g0prck1q-python3-3.15.0/bin/python3.15`
  (`nix build --no-link --print-out-paths nixpkgs#python315`).
- `uv sync --python <that path>`; set `UV_PYTHON_DOWNLOADS=never` if needed.
- ruff/ty wheels are glibc-dynamic: after `uv sync`, run
  `scripts/nixos-fix-venv.sh` (patchelf's the ELF interpreter of `.venv/bin/{ruff,ty}`).
- Verified on 3.15.0: `lazy import`, builtin `frozendict`, builtin
  `sentinel(name)` (usable in `X | SENTINEL` annotations), `[*x for x in y]`.
  ruff 0.17.1 + ty 0.0.89 understand all of these.  Twisted 26.4 installs fine.
- System python2.7 exists (no Twisted for it) — not used.

## Decisions

- **Layout**: `src/minerva/` (src layout, uv_build backend), tests in `tests/`.
  JS stays in `js_minerva/` at repo root (no longer a Python package).
  Remove `setup.py`, `runtests.sh`, `twisted/plugins/`.
- **Formatting**: ruff format defaults (4 spaces).  `.editorconfig`: tabs only
  for JS/HTML/haxe (untouched), spaces for Python.
- **Twisted stays** as the networking core (no asyncio rewrite).
- **Naming rule**: snake_case for everything Minerva owns.  Methods that
  implement a *Twisted* interface keep Twisted's camelCase (`dataReceived`,
  `connectionLost`, `makeConnection`, `buildProtocol` on Twisted factories,
  `pauseProducing`/`resumeProducing`/`stopProducing`, `registerProducer`/
  `unregisterProducer`), since Twisted (or Twisted-style producers) call them.
- **bytes vs str**: the byte-stream framers (`decoders.py`) deal in `bytes`.
  Frames are decoded from ASCII bytes; every Minerva string the application
  sees or sends is a `str` restricted to `" "`..`"~"`.  `Frame.encode()` ->
  `bytes`.  Non-ASCII frame bytes => invalid frame.
- **Frames/SACK/TransportInfo/QAN frames**: `@dataclass(frozen=True, slots=True)`;
  unions as PEP 695 `type` aliases; dispatch with `match`.
- `HelloFrame` gets explicit typed fields; tri-state `succeedsTransport`
  becomes `wants_strings: bool` + `succeeds_transport: int | None`.
- Enums: `KillReason(StrEnum)`, `HttpFormat(IntEnum)`, transport `_Mode(Enum)`.
  `DontWriteSack` marker -> builtin `sentinel`.
- **Decoders**: `feed(data) -> list[bytes]`, raise `FrameTooLong` instead of
  returning `(frames, code)`.  `bytearray` buffers.
- **Our interfaces** (`IStringProtocol`, `IStringFactory`, `IQANProtocol`,
  transport-created/destroyed hooks, server transport) -> `typing.Protocol`.
  zope `@implementer` only where Twisted itself cares (producers).
- Drop `stringsReceived` (plural) optimization; protocols implement
  `string_received(s: str)`.
- **Logging**: stdlib `logging` (tests use `caplog`).
- **JSON**: stdlib `json`; no securedict (hash randomization makes it moot).
- **Webmagic**: inline only the tiny bits needed (no-cache headers, a small
  "BetterResource" with /page -> /page/ redirect, fakes in tests).  Templates
  via jinja2 `Environment(FileSystemLoader, auto_reload=True)` instead of
  FileCache.  Cache-breaker = md5 of the known file.
- **Dev server**: `minerva-site` console script (argparse + endpoints +
  `task.react`) replaces twistd plugin + `tap.py`.  Paths to closure-library and
  Coreweb's `js_coreweb`/`testres` are options (defaults: the `closure-library`
  submodule, and `../Coreweb`).
- `mserver.py` (1900 lines) split into cohesive modules; public API re-exported
  from `minerva/__init__.py` (with PEP 810 `lazy from ... import`).

## Review notes from Fable + Astra (2026-10-17; full text was in /tmp/minerva-consult/)

- mserver: `start=None` vs int comparisons (`start < self._lastStartParam`,
  `max(start, ...)`) raise in py3.  Use 0 / explicit None handling.
- mserver: `nonlocal = dict(...)` is a SyntaxError; use real `nonlocal`.
- `disconnectInactive` iterates `.values()` while `timedOut` deletes -> wrap in `list()`.
- `bunchedStrings.sort()` on (seqNum, str) tuples: duplicate seqNums possible
  (`0N a 0N b`) -> sort with `key=itemgetter(0)` (stable).
- `body[-1] != '\n'` on bytes -> `endswith`.  `request.args` is
  `dict[bytes, list[bytes]]`; `putChild` needs bytes; `render_*` returns bytes.
- Per-string exception handling when delivering to the protocol: catch per
  string, log, continue; stop if the stream got reset meanwhile.  (Old code:
  exception on string k silently dropped k+1..n although they were ACKed.)
- `TransportInfo.request_headers`: `field(hash=False)` (Headers unhashable).
- ty: zope interfaces are plain classes to ty -> define own `Clock` /
  `DelayedCall` / writable Protocols; `cast()` at the few annotated Twisted
  call sites.  `Factory` is `Generic[P]`; subclass Twisted `Protocol`.
- Put exceptions + Protocols in `interfaces.py` to avoid import cycles.
- Logging: bridge Twisted's log events into stdlib (`globalLogBeginner.
  beginLoggingTo([STDLibLogObserver()])`) in the CLI *and* in a session-scoped
  conftest fixture, so unhandled-Deferred errors show up in `caplog`.
- Tests: bare `map(...)` calls in test_mserver.py don't execute in py3!
  `http.Request(DummyChannel(), False)` uses a deprecated arg (filterwarnings=error).
  Use `twisted.web.test.requesthelper.DummyRequest/DummyChannel`.  Turn the
  `_BaseServerTransportTests` mixin into a fixture parametrized over decoders.
- Grep for silent `str(bytes)` -> `"b'...'"` after porting.
- Policy string: `str`, encoded once.

## Future work: the JavaScript client -> TypeScript (a suggested path)

The client is ~11k lines of Closure-style JS (goog.provide/require, JSDoc
types for Closure Compiler, `cw.Class`-style test classes), on a 2012 Closure
Library.  Suggested order, mirroring how the Python port went:

1. Keep the safety net: tests/test_js.py runs the existing JS suite against
   the Python server in headless Chrome, and tests/test_browser.py drives the
   compiled client.  Port each module's tests along with it (to e.g. vitest),
   and add a TS-client variant of the browser tests.
2. Leaf modules first, as ES modules: frames, decoders, window, qan (the
   user's untracked qan.ts already does this, inlining a small Deferred).
   Their JSDoc types translate almost mechanically; Google's old `gents` tool
   (in the clutz repo) automated Closure->TS, but hand-porting is probably
   less trouble at this size.
3. Replace Closure Library pieces with the platform: goog.async.Deferred ->
   Promises (but keep cancellation, which QAN uses: AbortSignal), goog.events
   -> EventTarget, goog.net.XhrIo + the readyState-3 XHR streaming hacks
   (xhrlike/xhdr/xhrmaster/xhrslave) -> fetch() with a ReadableStream body.
4. Transports: HTTP long-poll/streaming map well to fetch().  The Flash
   socket transport can't run in any current browser; the natural successor
   is a WebSocket transport (server: a small Twisted/autobahn or
   `websockets` endpoint speaking the same frames).  The cross-subdomain
   xdrframe machinery (document.domain) is also dead in modern browsers
   (document.domain setting is deprecated); HTTP/2 makes the per-host
   connection limit it worked around mostly moot.
5. Then client.js (ClientStream/ClientTransport, ~2.6k lines) last.

## Known client bugs (pre-existing in 2012 code; not fixed)

- `ClientStream.earlyFailure_` (e.g. Flash Player missing or blocked, or the
  XDR iframes failing) disposes the stream without calling the protocol's
  `streamReset`, so the application never hears that the stream died; a
  `sendString` right after `start()` then throws "Can't send in state
  5_DISCONNECTED".  tests/test_flash.py works around it (stops at "ERROR"
  lines, else times out).

## Hardening ideas (pre-existing in 2012 code; from Astra's review; not done)

- HTTP request bodies have no total size limit (Twisted spools them; we
  `read()` it all).  Needs a custom channel/Content-Length check.
- No global limit on concurrent streams / stream-creation rate.
- TCP connections are never force-closed after policy file / YouCloseIt, and
  there's no handshake timeout in UNKNOWN mode (existing TODOs in transport.py).
- QAN: unlimited concurrent peer questions.  A stream reset cancels the
  answers that are still being worked out, except the answer of a
  `body_received` call that reset the stream itself: either `QANHelper`
  has not stored that call's Deferred yet when the reset runs, or the call
  is a coroutine, which Twisted can't cancel from inside itself.  Such a
  call runs on, and its late answer is dropped.
- ServerStream producer registration: a pull producer that unregisters itself
  inside Twisted's synchronous resumeProducing leaves a stale
  `_primary_has_producer` flag.

## Demos: known problems (from the reviews of 2026-11-14; not fixed)

- Links: docs/website/index.html and both demo pages link to
  `github.com/ludios/Minerva/.../master/src/minerva/...` and
  `.../master/js_minerva/demos/...`.  Those paths exist only on `python3`, so
  the links are 404 until `python3` becomes `master`.
- Bluesky stream, load on Bluesky's services:
  - Every post that some viewer wants gets a profile lookup, though each
    viewer's limiter then drops most of them.
  - `make_fetch_profiles`'s `Agent` has no persistent pool, so each
    `getProfiles` batch opens a new TLS connection.
  - A failing AppView (HTTP 429, say) is asked again with every batch (4/s).
  - A second post by an author whose lookup is still running starts another
    lookup.
  - `JetstreamClient.start()` connects at once, whatever the backoff says:
    viewers that come and go make it reconnect each time.
- Bluesky stream, other:
  - An author who opts out (or gets labeled) is still shown until their
    cached profile expires (15 minutes).
  - A trailing slash in `--jetstream` or `--bluesky-appview` makes a
    `//xrpc/...` path, which both services answer with 404.
- Whiteboard:
  - The server doesn't send a point (or ClearBoard) back to its sender, so
    two viewers who draw and clear at the same moment can end up with
    different boards.
  - When the board is full (10,000 points), the sender's page still draws
    the point that the server ignored.
  - A point that is added again is sent to the connected viewers again, so
    their pages can hold more than 10,000 shapes.
  - whiteboard.css sizes `#whiteboard`, but the page's element is
    `#whiteboard-container`.
- Both pages rewrite their URL (`history.replaceState`) to add `mode=http`;
  making HTTP the default in js_minerva/cw/net/demo/shared.js would fix
  /chatapp/ too.
- `DemoProtocol` takes `subprotocol:<name>` after other commands too (a
  client that sent `begin_chat` first keeps getting chat messages), and
  duplicates `SubprotocolProtocol`'s dispatch.
- The checked-in standalone client (src/minerva/compiled_client/) is still
  the build from 2012 (Coreweb 4f2b7b8, Closure Compiler r2226).  A full
  `scripts/build_js.py` with today's ../Coreweb (735f263) and
  compiler-20120917 rewrites it; `scripts/build_js.py deps` and `... demos`
  leave it alone.

## Behavior changes (document in README/CHANGES)

- `objcheck`: `ensure_int("0")` raises `TypeError` (was `ValueError`).
  Huge floats (`1e999` -> inf) now raise `ValueError` (was an `OverflowError`
  that escaped the hello parser).  Strict int parsing no longer accepts a
  trailing newline (`"5\n"`) or non-ASCII digits.
- `ResetFrame.decode` without `|` raises `InvalidFrame` (was `ValueError`).
- Hello frames: any non-ASCII *string value* (even for unknown keys) is
  rejected, as before; frames containing non-ASCII *bytes* are now invalid.
- Decoders raise `FrameTooLong` instead of returning `(frames, TOO_LONG)`.
- Protocols implement only `string_received(s)` (no plural `stringsReceived`).
  An exception in `string_received` is logged per string and delivery goes on;
  after the protocol resets the stream, the rest of the batch isn't delivered.
- `ServerStream.reset()` validates `reason_string` (restricted, <= 255 chars).
- `ServerStream.notify_finish()` after the stream finished returns a fired
  Deferred (was: AttributeError on None).
- `write_strings(queue, start)`: `start` is an int (0 = everything), not None.
- `ServerTransportFactory(policy_string=...)` takes a `str` (was bytes `str`).
- `XDRFrame`: bad `id`/`domain` -> 400 (was a 500 from a raised ValueError).
  Template vars renamed (`frame_id`, `xdrframe_js_href`).
- `htmldumps` escapes `<`, `>`, `&` as `\u003c` etc. (was only `/` -> `\/`).
- Strings that arrive together with (before) a bad frame are delivered and
  SACKed before the transport is killed (py2 crashed on a None stream).
- `QANProtocolWrapper` handles a bad QAN frame (py2: NameError).
- Dev server: `uv run minerva-site --http ENDPOINT --minerva ENDPOINT` (argparse
  + Twisted endpoints) replaces `twistd minerva_site` (no daemonizing/pidfile;
  use systemd or similar).  `--coreweb PATH` added (default `../Coreweb`).
  Pyquitter auto-reloading dropped (use e.g. `watchfiles`).  Policy file lists
  the *actual* listening ports.  Twisted logs are routed into stdlib logging.
- DemoProtocol `send_demo` now also sends the `alphabet: ...` string (py2 passed
  it as `validate=`).
- Smoke-tested for real: HTTP long-poll (stream create, SACK, echo, reset) via
  curl, and Flash policy file + int32 echo/heartbeats via raw sockets.
- Twisted request "queued" handling dropped (modern Twisted never queues).
- QAN: notifications go through `maybeDeferred` too, so an `async def
  body_received` works for them (it would otherwise never run).  A non-`str`
  answer is logged and answered with UnknownErrorAnswer (py2: the peer got no
  answer at all).
- Tutorials: run with `python -m minerva.tutorial.standalone_N_...`; they use
  `task.react` + endpoints; 4-6 dispatch JSON messages with `match`; 6 uses an
  `async def body_received`.  Their HTML/JS pages are byte-for-byte unchanged.
- QAN: bodies are `str`; `KnownError(body)`/`UnknownError(body)` have `.body`.
  `body_received` may return a coroutine (`async def`).  `fail_all` no longer
  crashes on already-cancelled questions (py2 called `None.errback`).

## Phases

- [x] 0. Housekeeping: branch `python3`, move py2 `.pyc` junk out of the tree
      (backup to `~/minerva-py2-pyc-backup/`), TODO.md, pyproject.toml, uv.lock,
      ruff/ty/pytest config, `scripts/nixos-fix-venv.sh`.  Commit.
- [x] 1. `git mv` package to `src/minerva/`, tests to `tests/` (pure moves,
      separate commit to keep history traceable).
- [x] 2. Port leaf modules + tests: [x] `objcheck`, [x] `window`, [x] `decoders`,
      [x] `frames`, [x] `qan`.  Add hypothesis property tests.  ruff + ty clean.  Commit each.
- [x] 3. Port `mserver` -> split modules (`stream`, `transport`, `web`,
      `protocols`?), `interfaces` -> Protocols.  Port `mocks` into tests.
- [x] 4. Port `test_mserver` (3400 lines!) to pytest -> test_{stream,transport,
      integration,web}.py.  814 tests pass in ~5s.
- [x] 5. Dev site: `minerva_site` + `tap` -> `minerva/site.py` CLI; chatapp,
      dumbtest pages; test resources (SimpleResponse, UnicodeRainbow,
      NoOriginHeader, GetEndpointInfo, DisplayConnections, wait_resource).
- [x] 6. Tutorials (`minerva/tutorial/standalone_*.py`) -> runnable py3 scripts.
- [x] 7. Build scripts -> `scripts/`: build_autocachebreakers.py (ran it: same
      digest), build_js.py (ported but NOT yet run: needs old closure-library +
      compiler; CLOSURE_PYTHON=python2 for their tools), build_docs.sh, build_swfs.sh.
- [x] 8. Smoke test real server: minerva-site via curl (HTTP long-poll) and raw
      sockets (policy file, int32); tutorial 6 async QAN via curl.
      Automated: tests/test_browser.py drives the *compiled 2012 JS client* in
      headless Chrome (strings + async QAN over long-polling), ~7s; skipped
      without Chrome.  NOTE: `--dump-dom` fires at the load event, so the
      pages delay it with an <img> from WaitResource.  The standalone client
      can only long-poll; streaming/Flash/subdomains need the uncompiled
      client (closure-library; phase 11).
- [x] 9. README, CHANGES (behavior changes), .editorconfig, CI workflow.
- [x] 10. Review pass: self review (exception-safe stream calls); Astra and
      Fable reviewed the finished port against master (prompt was in
      /tmp/minerva-consult/review_prompt.md).  Fixed all their real bugs (most
      pre-existing in 2012), each with a test that fails without the fix;
      deferred DoS-hardening items are listed above.  No `XXX(port)` markers
      were needed.
- [x] 11. (stretch) closure-library for dev mode/JS tests; TS plan (above).
      DONE: downloaded closure-library r2192 (commit 7f2b29f, Sep 2012 — what
      the compiled client was built with) into ../closure-library.  The JS
      unit-test suite (190 tests, 23 browser-specific skips) passes in headless
      Chrome via tests/test_js.py (tests/chrome.py = tiny CDP client).  This
      found the missing `X-Content-Type-Options: nosniff` regression that broke
      HTTP streaming.  scripts/build_js.py also verified: with
      ../closure-compiler/build/compiler.jar from compiler-20120917.zip (r2180,
      via the Google Code archive: storage.googleapis.com/google-code-archive-
      downloads/v2/code.google.com/closure-compiler/) and CLOSURE_PYTHON=python2,
      deps.js regenerates identically and the client compiles with 0 errors /
      0 warnings / 97.5% typed (same as 2012); the new build passes the browser
      tests.  Kept the checked-in r2226 artifacts.
- [x] 12. Flash end-to-end tests.  scripts/flash-browser.nix builds Pale Moon
      35.0.1 (GTK2 build; Pale Moon keeps NPAPI) + Adobe Flash Player
      32.0.0.371 NPAPI (last release before the 2021-01-12 kill switch, so no
      binary patching needed) + Xvfb into ../flash-browser.  Pale Moon was
      dropped from nixpkgs-unstable (2026-09-21, GTK2), so it pins nixos-26.05
      for GTK2 and repacks the official tarball (sha256 matches palemoon.org's
      hashes.txt; .sig verified with trava90's key 0xC65285EC).  The Flash
      tarball is from the Wayback Machine, matching the sha256 that nixpkgs
      pinned in 2020 (commit d8fa222).  Flashpoint Archive's browser is
      Flashpoint Navigator, a Basilisk fork (same UXP platform as Pale Moon),
      but it has no Linux release binaries.  Pale Moon can't be
      remote-controlled, so pages POST their logs: browser_server.py's
      /log/ID, and js_minerva_tests.html?report=URL.  Profile prefs needed:
      plugin.state.flash=2 (else click-to-play) and
      browser.shell.checkDefaultBrowser=false (else a modal dialog).
      tests/test_flash.py: strings + async QAN over the Flash socket (~3s);
      test_js.py runs the JS suite in Pale Moon too: 190 tests, 20 skips
      (Chrome: 23), i.e. RealFlashSocketTests now run and pass.  Verified the
      tests fail without the plugin and with a policy file that doesn't allow
      the port.
- [x] 13. Merged DemosMinerva (2026-10-26; github.com/ludios/DemosMinerva,
      py2, last real change 2012) into `src/minerva/demos/` + `js_minerva/
      demos/`, served by minerva-site (`/whiteboard/`, `/bluesky-stream/`, and
      `_dev` variants).  History was not merged.
      The LiveJournal stream demo's source (atom.services.livejournal.com) is
      dead, so it became a Bluesky stream: Jetstream v2 over Twisted 26.4's
      `twisted.web.websocket` client (needs the `demos` extra =
      `twisted[tls,websocket]`, also in the dev group), skipping replies and
      self-labeled posts; authors' profiles are batch-checked via
      public.api.bsky.app `getProfiles` (any profile label, incl.
      `!no-unauthenticated`, means don't show); posts are sent in Jetstream
      order, 4/s per viewer on average (bursts of up to 4).  Twisted's
      WebSocket `connect()` never fires if TCP drops mid-handshake, so
      JetstreamClient handles that (and a connect timeout) itself; and its
      `textMessageReceived` gets a message that arrived in several TCP reads
      in pieces, which JetstreamProtocol puts together.  The demos' JS
      compiles with 0 warnings via
      `scripts/build_js.py demos`; Googstyle's CSS/images were replaced by the
      compiled CSS + two Closure Library images.  tests/test_demos.py runs both
      demos in headless Chrome (Bluesky against a fake Jetstream/AppView).
