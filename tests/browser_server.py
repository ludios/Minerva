"""
A server for `test_browser.py` and `test_flash.py`: pages that drive the
compiled JavaScript client against tutorial protocols, over HTTP long-polling
(`/strings`, `/qan`) or the Flash socket transport (`/flash/strings`,
`/flash/qan`).  Prints its (ephemeral) HTTP port, then serves.

Run with `python -m tests.browser_server`.
"""

import json

from twisted.internet import task
from twisted.internet.address import IPv4Address
from twisted.internet.defer import Deferred
from twisted.internet.endpoints import serverFromString
from twisted.internet.interfaces import IReactorCore
from twisted.web.resource import Resource
from twisted.web.server import Request, Site

from minerva import ServerTransportFactory, StreamTracker, WebPort
from minerva.site import policy_file
from minerva.tutorial import standalone_1_rstring, standalone_6_qan_deferred
from minerva.web import put_child

# Each page logs what happens into #output.  Loaded with ?run=ID, it also
# POSTs its whole log to /log/ID after every line, for browsers that tests
# can't remote-control.
PAGE = """<!doctype html>
<div id="minerva-elements"></div>
<pre id="output"></pre>
<script src="/_minerva/minerva-client.js"></script>
<script>
var log = function(m) {
    var output = document.getElementById('output');
    output.appendChild(document.createTextNode(m + "\\n"));
    var run = /[?&]run=(\\w+)/.exec(location.search);
    if (run) {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/log/" + run[1]);
        xhr.send(output.textContent);
    }
};
window.onerror = function(m) { log("ERROR " + m); };
var endpoint = @@ENDPOINT@@;
@@SCRIPT@@
</script>
"""

STRINGS_SCRIPT = """
var P = function() {};
var received = 0;
P.prototype.streamStarted = function(stream) { log("started"); };
P.prototype.streamReset = function(reason, appLevel) { log("reset: " + reason); };
P.prototype.stringReceived = function(s) {
    log("got: " + s);
    if (++received == 2) { stream.reset("done"); }
};
var stream = new Minerva.ClientStream(endpoint);
stream.bindToProtocol(new P());
stream.start();
stream.sendString("hello");
stream.sendString("~ restricted ~");
"""

QAN_SCRIPT = """
var P = function() {};
P.prototype.streamStarted = function(stream, qanHelper) {
    log("started");
    qanHelper.ask(Minerva.JSON.asciify(["listclients_in_1_sec"])).addCallback(
        function(answer) { log("answer: " + answer); stream.reset("done"); });
};
P.prototype.streamReset = function(reason, appLevel) { log("reset: " + reason); };
P.prototype.bodyReceived = function(body, isQuestion) { log("body: " + body); };
var stream = new Minerva.ClientStream(endpoint);
stream.bindToProtocol(new Minerva.QANProtocolWrapper(new P()));
stream.start();
"""


def http_endpoint(path: str) -> str:
    return f"new Minerva.HttpEndpoint({json.dumps(path)})"


def socket_endpoint(port: int) -> str:
    # FlashConnector.swf is loaded from /_minerva/.
    return f'new Minerva.SocketEndpoint("/_minerva/", "127.0.0.1", {port})'


class Page(Resource):
    isLeaf = True

    def __init__(self, endpoint: str, script: str) -> None:
        super().__init__()
        self._html = PAGE.replace("@@ENDPOINT@@", endpoint).replace(
            "@@SCRIPT@@", script
        )

    def render_GET(self, request: Request) -> bytes:
        return self._html.encode()


class Logs(Resource):
    """
    What pages loaded with ?run=ID logged: they POST to /log/ID, and tests
    GET it.
    """

    isLeaf = True

    def __init__(self) -> None:
        super().__init__()
        self._logs: dict[bytes, bytes] = {}

    def render_POST(self, request: Request) -> bytes:
        assert request.content is not None
        log = request.content.read()
        run = request.path
        # The POSTs may arrive out of order, but each has the whole log so far.
        if len(log) > len(self._logs.get(run, b"")):
            self._logs[run] = log
        return b""

    def render_GET(self, request: Request) -> bytes:
        request.setHeader(b"content-type", b"text/plain; charset=utf-8")
        return self._logs.get(request.path, b"")


async def main(reactor: IReactorCore) -> None:
    strings_tracker = StreamTracker(reactor, standalone_1_rstring.DemoFactory())
    qan_tracker = StreamTracker(reactor, standalone_6_qan_deferred.DemoFactory(reactor))

    # Flash Player asks the socket port itself for a policy file (after
    # trying port 843), so each listener serves one that allows them all.
    socket_factories = {
        "strings": ServerTransportFactory(reactor, strings_tracker),
        "qan": ServerTransportFactory(reactor, qan_tracker),
    }
    socket_ports = {}
    for name, factory in socket_factories.items():
        port = await serverFromString(reactor, "tcp:0:interface=127.0.0.1").listen(
            factory
        )
        host = port.getHost()
        assert isinstance(host, IPv4Address)
        socket_ports[name] = host.port
    for factory in socket_factories.values():
        factory.set_policy_string(policy_file(list(socket_ports.values())))

    root = Resource()
    put_child(
        root, b"strings", Page(http_endpoint("/_minerva_strings/"), STRINGS_SCRIPT)
    )
    put_child(root, b"qan", Page(http_endpoint("/_minerva_qan/"), QAN_SCRIPT))
    flash = Resource()
    put_child(root, b"flash", flash)
    put_child(
        flash,
        b"strings",
        Page(socket_endpoint(socket_ports["strings"]), STRINGS_SCRIPT),
    )
    put_child(flash, b"qan", Page(socket_endpoint(socket_ports["qan"]), QAN_SCRIPT))
    put_child(root, b"log", Logs())
    # All pages load the client (and Flash pages, FlashConnector.swf) from here.
    put_child(root, b"_minerva", WebPort(reactor, strings_tracker))
    put_child(root, b"_minerva_strings", WebPort(reactor, strings_tracker))
    put_child(root, b"_minerva_qan", WebPort(reactor, qan_tracker))

    port = await serverFromString(reactor, "tcp:0:interface=127.0.0.1").listen(
        Site(root)
    )
    host = port.getHost()
    assert isinstance(host, IPv4Address)
    print(host.port, flush=True)
    await Deferred()


if __name__ == "__main__":
    task.react(main)
