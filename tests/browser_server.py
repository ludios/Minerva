"""
A server for `test_browser.py`: pages that drive the compiled JavaScript
client against tutorial protocols.  Prints its (ephemeral) port, then serves.

Run with `python -m tests.browser_server`.
"""

from twisted.internet import task
from twisted.internet.address import IPv4Address
from twisted.internet.defer import Deferred
from twisted.internet.endpoints import serverFromString
from twisted.internet.interfaces import IReactorCore
from twisted.web.resource import Resource
from twisted.web.server import Request, Site

from minerva import StreamTracker, WebPort
from minerva.site import WaitResource
from minerva.tutorial import standalone_1_rstring, standalone_6_qan_deferred
from minerva.web import put_child

# Each page logs what happens into #output.  The image delays the page's load
# event (and so headless Chrome's --dump-dom) by 3 seconds.
PAGE = """<!doctype html>
<div id="minerva-elements"></div>
<pre id="output"></pre>
<img src="/wait/?wait=3">
<script src="/_minerva/minerva-client.js"></script>
<script>
var log = function(m) {
    document.getElementById('output').appendChild(document.createTextNode(m + "\\n"));
};
window.onerror = function(m) { log("ERROR " + m); };
var endpoint = new Minerva.HttpEndpoint("/@@PORT@@/");
@@SCRIPT@@
</script>
"""

STRINGS_SCRIPT = """
var P = function() {};
P.prototype.streamStarted = function(stream) { log("started"); };
P.prototype.streamReset = function(reason, appLevel) { log("reset: " + reason); };
P.prototype.stringReceived = function(s) { log("got: " + s); };
var stream = new Minerva.ClientStream(endpoint);
stream.bindToProtocol(new P());
stream.start();
stream.sendString("hello");
stream.sendString("~ restricted ~");
setTimeout(function() { stream.reset("done"); }, 1500);
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


class Page(Resource):
    isLeaf = True

    def __init__(self, port_path: str, script: str) -> None:
        super().__init__()
        self._html = PAGE.replace("@@PORT@@", port_path).replace("@@SCRIPT@@", script)

    def render_GET(self, request: Request) -> bytes:
        return self._html.encode()


async def main(reactor: IReactorCore) -> None:
    strings_tracker = StreamTracker(reactor, standalone_1_rstring.DemoFactory())
    qan_tracker = StreamTracker(reactor, standalone_6_qan_deferred.DemoFactory(reactor))

    root = Resource()
    put_child(root, b"strings", Page("_minerva_strings", STRINGS_SCRIPT))
    put_child(root, b"qan", Page("_minerva_qan", QAN_SCRIPT))
    # Both pages load the client from here.
    put_child(root, b"_minerva", WebPort(reactor, strings_tracker))
    put_child(root, b"_minerva_strings", WebPort(reactor, strings_tracker))
    put_child(root, b"_minerva_qan", WebPort(reactor, qan_tracker))
    put_child(root, b"wait", WaitResource(reactor))

    port = await serverFromString(reactor, "tcp:0:interface=127.0.0.1").listen(
        Site(root)
    )
    host = port.getHost()
    assert isinstance(host, IPv4Address)
    print(host.port, flush=True)
    await Deferred()


if __name__ == "__main__":
    task.react(main)
