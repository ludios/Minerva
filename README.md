Minerva
=======

Minerva is a robust Comet server and client.  You can use it to build web
applications that need a socket-like abstraction.  Its server is built on top
of Twisted.  The JavaScript client uses Closure Library.

Some uses for Minerva: chat applications, games, real-time collaboration,
dashboards, monitoring systems.

Read more: https://ludios.org/minerva/

> Minerva dates from 2010-2012.  The server was ported to Python 3.15 in 2026
> (see [CHANGES.md](CHANGES.md)); the JavaScript client is unchanged.


## Highlights

*	Reliable and in-order message delivery: The Minerva client and server attach
	sequence numbers to messages and send/receive ACKs.  Messages never get lost or
	re-ordered, even when the HTTP transports are used.

*	Serialization-agnostic: Your application isn't forced to use JSON, XML, or
	anything else.

*	Cross-browser: Minerva works in old and new versions of IE, Firefox, Chrome,
	Safari, and Opera.  Minerva disables the page-loading spinner in all browsers.

*	Multiple transports: Minerva runs over HTTP long-polling, HTTP streaming, and
	Flash sockets.  Its design easily supports new transports.

*	Robust timeout logic: Stuck requests and sockets are detected and aborted.

*	Handles tab addicts: To work around browsers' per-domain active request
	limits (usually just 4-6 requests), Minerva can send HTTP requests to random
	subdomains.  Your web application will work as usual when you open it in a
	dozen tabs.  If you want to use this on your HTTPS site, a wildcard cert is required.


## Setup

You need Python 3.15 and [uv](https://docs.astral.sh/uv/):

```
uv sync
```

<details>
<summary>On NixOS</summary>

uv's downloaded Pythons and the `ruff`/`ty` wheels need a glibc dynamic linker
in the usual place, which NixOS (without nix-ld) doesn't have.  Use Nix's
Python, and patch the two binaries after syncing:

```
uv sync --python "$(nix build --no-link --print-out-paths nixpkgs#python315)/bin/python3.15"
scripts/nixos-fix-venv.sh
```
</details>


## Using Minerva in your application

Implement a string protocol and a factory for it, and put a `WebPort` into
your site:

```python
from twisted.internet import task
from twisted.internet.defer import Deferred
from twisted.internet.endpoints import serverFromString
from twisted.web.resource import Resource
from twisted.web.server import Site

from minerva import ServerStream, StreamTracker, WebPort
from minerva.web import put_child


class EchoProtocol:
    def stream_started(self, stream: ServerStream) -> None:
        self.stream = stream

    def stream_reset(self, reason_string: str, application_level: bool) -> None:
        print("Stream reset:", reason_string)

    def string_received(self, s: str) -> None:
        self.stream.send_string(s)


class EchoFactory:
    def build_protocol(self) -> EchoProtocol:
        return EchoProtocol()


async def main(reactor) -> None:
    root = Resource()
    put_child(root, b"_minerva", WebPort(reactor, StreamTracker(reactor, EchoFactory())))
    await serverFromString(reactor, "tcp:8080").listen(Site(root))
    await Deferred()


task.react(main)
```

Minerva strings may contain only the characters `" "` to `"~"`; encode
anything else, for example as JSON.  For question/answer/notification-style
messages, see `minerva.QANProtocol` and `minerva.QANProtocolWrapper`.

The tutorials in [src/minerva/tutorial/](src/minerva/tutorial/) are small,
complete examples, each with a page that uses the standalone JavaScript
client.  Run one and open http://127.0.0.1:10001/:

```
uv run python -m minerva.tutorial.standalone_1_rstring
```

To also accept Flash socket connections, listen on TCP with a
`ServerTransportFactory` (it serves the Flash socket policy file too).


## The development server

`minerva-site` serves the JavaScript tests, the chat demo, and some testing
tools:

```
uv run minerva-site --http tcp:8111:interface=127.0.0.1 --minerva tcp:8112:interface=127.0.0.1
```

Then browse to http://127.0.0.1:8111/.  Follow the `chatapp/?mode=http` link
for a simple demo; you can load it in multiple browsers and chat amongst
each other.

Pages that use the uncompiled JavaScript need
[Closure Library](https://github.com/google/closure-library) and
[Coreweb](https://github.com/ludios/Coreweb)'s JavaScript; by default they are
expected next to this repository (`../closure-library`, `../Coreweb`), or pass
`--closure-library` and `--coreweb`.  Pass `--domain` to let browsers use
random subdomains.  See `uv run minerva-site --help`.


## Development

```
uv run pytest                    # server tests (and browser tests, if Chrome is installed)
uv run pytest -m 'not browser'   # skip the headless-Chrome end-to-end tests
uv run ruff format && uv run ruff check
uv run ty check
```

Client tests: start the development server, then browse to
http://127.0.0.1:8111/js_minerva_tests.html

Naming convention: everything Minerva owns is snake_case; methods that
implement a *Twisted* interface (`dataReceived`, `pauseProducing`,
`registerProducer`, ...) keep Twisted's camelCase names, since Twisted calls
them.  The allowed names are listed in `pyproject.toml`.


## Recompiling the compiled .js and .swf files

The compiled files in `src/minerva/compiled_client/` are checked in.  To
rebuild them, you need an old Closure Library and Closure Compiler (the
JavaScript uses APIs that have since been removed), Python 2 for Closure
Library's build tools, and [Haxe](https://haxe.org/) for the Flash connector.
These work:

- Closure Library r2192 (September 2012), commit
  [`7f2b29f`](https://github.com/google/closure-library/tree/7f2b29fea671702822e5667faaa80249856a1fc3),
  in `../closure-library`.  The development server and the JavaScript tests
  need this too.
- Closure Compiler 20120917, from
  [`compiler-20120917.zip`](https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/closure-compiler/compiler-20120917.zip),
  with its `compiler.jar` in `../closure-compiler/build/`.

Then run:

```
scripts/build_js.py
scripts/build_swfs.sh && scripts/build_autocachebreakers.py
```

See `scripts/build_js.py` for the environment variables it reads.
