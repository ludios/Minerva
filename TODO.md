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
  Coreweb's `js_coreweb`/`testres` are options (default: siblings of repo).
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

## Behavior changes (document in README/CHANGES)

- `objcheck`: `ensure_int("0")` raises `TypeError` (was `ValueError`).
  Huge floats (`1e999` -> inf) now raise `ValueError` (was an `OverflowError`
  that escaped the hello parser).  Strict int parsing no longer accepts a
  trailing newline (`"5\n"`) or non-ASCII digits.
- `ResetFrame.decode` without `|` raises `InvalidFrame` (was `ValueError`).
- Hello frames: any non-ASCII *string value* (even for unknown keys) is
  rejected, as before; frames containing non-ASCII *bytes* are now invalid.
- Decoders raise `FrameTooLong` instead of returning `(frames, TOO_LONG)`.
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
- [ ] 3. Port `mserver` -> split modules (`stream`, `transport`, `web`,
      `protocols`?), `interfaces` -> Protocols.  Port `mocks` into tests.
- [ ] 4. Port `test_mserver` (3400 lines!) to pytest.  This is the big one.
- [ ] 5. Dev site: `minerva_site` + `tap` -> `minerva/site.py` CLI; chatapp,
      dumbtest pages; test resources (SimpleResponse, UnicodeRainbow,
      NoOriginHeader, GetEndpointInfo, DisplayConnections, wait_resource).
- [ ] 6. Tutorials (`minerva/tutorial/standalone_*.py`) -> runnable py3 scripts.
- [ ] 7. Build scripts: `build_autocachebreakers.py` (port), JS build scripts
      (depend on Coreweb `_closurebuild`; port or replace), docs scripts.
- [ ] 8. Smoke test real server: run `minerva-site`, curl HTTP transport with a
      hand-written hello frame; TCP int32 + policy file via a tiny Python client.
      Maybe headless browser if available.
- [ ] 9. README, CHANGES (behavior changes), .editorconfig, CI workflow.
- [ ] 10. Review pass: `/code-review`-style self review; consult Fable/Astra;
      grep `XXX(port)`.
- [ ] 11. (stretch) closure-library for dev mode/JS tests; note TS plan.
