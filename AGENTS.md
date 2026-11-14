<!-- clank-right
languages       = ["python"]
# No "javascript" in `languages`: js_minerva/ is 2012 Closure Library code, not a Node project, and it keeps its own style (see "The JavaScript").
space_alignment = false
tools_extra     = ["java", "python2", "Xvfb"]
-->

# Project map

Minerva is a Comet server (Python, built on Twisted) and client (JavaScript, built on Closure Library), written in 2010-2012. It gives a web application a socket-like stream of strings over HTTP long-polling, HTTP streaming, or Flash sockets.

The branch `python3` carries the port of the server from Python 2 to Python 3.15, done in October 2026; `master` is still the 2012 Python 2 code. CHANGES.md lists what the port changed for users. TODO.md is the port's working log: read its "Decisions" before you change the Python API, and its "Known client bugs" before you report a bug in the JavaScript.

- src/minerva/ - the server package (4 spaces, formatted by `ruff format`, checked by ruff and ty).
	- frames.py, decoders.py, window.py, objcheck.py - the wire format: frames, the framers that split bytes into frames, the send and receive windows, and the strict validation of values from the wire.
	- transport.py, stream.py, web.py - `ServerTransport` (one per HTTP request or TCP connection), `ServerStream` and `StreamTracker`, and `WebPort` (the twisted.web resource that clients talk to).
	- interfaces.py, protocols.py, qan.py - what an application implements and uses: the `typing.Protocol`s, `SubprotocolFactory`, and QAN (question, answer, notification).
	- site.py - `minerva-site`, the development server: it serves the JavaScript tests, the demos, the chat page (chatapp/) and some testing tools.
	- demos/ - the whiteboard and the Bluesky stream, each with a server module, a page template, and files in static/ (the compiled JavaScript there is GENERATED).
	- tutorial/ - small complete servers, each with a page that uses the standalone client.
	- compiled_client/ - GENERATED: the compiled standalone client, xdrframe.js and FlashConnector.swf, checked in.
- js_minerva/ - the JavaScript client (cw/net/), its tests (cw/net/Test*.js), the demos' JavaScript (demos/), the externs for Closure Compiler, and deps.js (GENERATED).
- hx/ - the Flash connector, in Haxe.
- scripts/ - build_js.py, build_swfs.sh and build_autocachebreakers.py make the GENERATED files; flash-browser.nix builds the Flash browser for the tests; nixos-fix-venv.sh is described in "Before committing".
- tests/ - pytest. chrome.py and flash_browser.py drive the browsers; browser_server.py and helpers.py start the servers that the browser tests load pages from; mocks.py has the fakes.
- docs/ - the documentation from 2012 (.rst, and the .html built from it); docs/website/ is the page at ludios.org/minerva.

Every file that `git status` shows as untracked at the top of the repository is the user's own, from 2012 or work in progress: `_*.patch`, `_start_dev*`, `*_ivank.*`, `pypy-start_dev.sh`, dev_keys/, newdoc/, minerva/ (not the package, which is src/minerva/), docs/StandaloneMinerva.*, and js_minerva/cw/net/qan.ts. Never change, delete or commit them, and never run `git checkout --` or `git clean` on a directory that holds them.

# The Python

Everything that Minerva owns is snake_case. A method that implements a Twisted interface (`dataReceived`, `pauseProducing`, ...) keeps Twisted's camelCase name, because Twisted calls it; each such name must be listed under `extend-ignore-names` in pyproject.toml.

The code has no `# noqa`: restructure the code until ruff accepts it. A `# ty: ignore[...]` is acceptable only where the test passes a wrong type on purpose, or where ty does not understand Twisted's zope.interface declarations.

pytest turns every warning into an error (`filterwarnings` in pyproject.toml).

The core depends only on Twisted and Jinja2. What only a demo needs goes into the `demos` extra, and the demo's page must say how to install the extra when it is missing.

When a change is visible to an application or to a user of `minerva-site`, describe it in CHANGES.md, and in README.md where the README covers it.

# The JavaScript

js_minerva/ and Coreweb's JavaScript are compiled with the toolchain of 2012: Closure Library r2192 and Closure Compiler 20120917 (README.md, "Recompiling the compiled .js and .swf files"). So:

- Write ES3, as the surrounding code does: `var`, `function`, `goog.provide` and `goog.require`, JSDoc type annotations, camelCase, tabs. Closure Compiler 20120917 rejects newer syntax, and the compiled code must still parse in old browsers.
- There is no package.json, and nothing here runs in Node.
- The compiled files are checked in. After changing anything under js_minerva/, run `scripts/build_js.py` (it reads ../closure-library, ../closure-compiler and ../Coreweb, and runs `python2` and `java`; all are on this machine), check that each `.js.log` next to a compiled file says `0 error(s), 0 warning(s)`, and commit the rebuilt files together with the source change.
- `scripts/build_swfs.sh` needs Haxe, which is not installed on this machine.

# Before committing

	uv run ruff format
	uv run ruff check
	uv run ty check
	uv run pytest

All four must pass, and pytest must skip nothing: on this machine Chrome, ../closure-library, ../Coreweb and ../flash-browser are present, so the browser tests (headless Chrome, and Pale Moon with Flash Player under Xvfb) all run. The whole suite takes about 20 seconds.

On this machine, the `ruff` and `ty` that uv installs into .venv cannot run until `scripts/nixos-fix-venv.sh` has patched them. Until then, `uv run ruff` and `uv run ty` silently run the system's newer `ruff` and `ty`, which report other diagnostics than the versions in uv.lock. So after uv creates or changes .venv (it prints "Installed N packages"), run `scripts/nixos-fix-venv.sh`, and check that `uv run ty --version` prints the version of `ty` in uv.lock.
