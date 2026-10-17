"""
Tutorial 3: broadcast what each client says to every client.

Run it with `uv run python -m minerva.tutorial.standalone_3_json`, then open
http://127.0.0.1:10001/ in a few browser tabs.
"""

import json

from twisted.internet import task
from twisted.internet.defer import Deferred
from twisted.internet.endpoints import serverFromString
from twisted.internet.interfaces import IReactorCore
from twisted.web.resource import Resource
from twisted.web.server import Request, Site

from minerva import ServerStream, StreamTracker, WebPort
from minerva.web import put_child


# The server-side protocol, where you receive the client's strings.
class DemoProtocol:
    stream: ServerStream

    def __init__(self, factory: DemoFactory, id: int) -> None:
        self.factory = factory
        self.id = id

    def stream_started(self, stream: ServerStream) -> None:
        self.stream = stream
        self.factory.clients.add(self)

    def stream_reset(self, reason_string: str, application_level: bool) -> None:
        print(f"Stream reset: {reason_string!r}")
        self.factory.clients.remove(self)

    def string_received(self, s: str) -> None:
        text = json.loads(s)
        print(f"Received from client #{self.id}: {text!r}")
        for protocol in self.factory.clients:
            if protocol is self:
                protocol.stream.send_string(json.dumps(f"You said: {text}"))
            else:
                protocol.stream.send_string(
                    json.dumps(f"Client #{self.id} said: {text}")
                )


# The factory can hold data and objects shared by the connected protocols.
class DemoFactory:
    def __init__(self) -> None:
        self.client_counter = 0
        self.clients: set[DemoProtocol] = set()

    def build_protocol(self) -> DemoProtocol:
        self.client_counter += 1
        return DemoProtocol(self, self.client_counter)


PAGE = r"""<!doctype html>
<div id="minerva-elements"></div> <!-- required container -->

Send Unicode string to everyone:
<input type="text" id="textinput">
<input type="button" value="Send" onclick="sendString(byId('textinput').value)">

<p>If it's not working, look at your browser's Console
(Chrome: <kbd>F12</kbd> -> Console tab; Firefox: <kbd>ctrl-shift-k</kbd>)</p>

<pre id="output"></pre>

<script src="/_minerva/minerva-client.js"></script>
<script>
var byId = function(id) { return document.getElementById(id); };
var logMessage = function(msg) {
	byId('output').appendChild(document.createTextNode(msg + "\n"));
	if(window.console && console.log) { console.log(msg); }
};
window.onerror = logMessage;

var DemoProtocol = function() {};
DemoProtocol.prototype.streamStarted = function(stream) {
	this.stream = stream;
};
DemoProtocol.prototype.streamReset = function(reasonString, applicationLevel) {
	logMessage("Stream reset: " + reasonString);
	logMessage("Reload the page to reconnect.");
};
DemoProtocol.prototype.stringReceived = function(s) {
	logMessage("Received from server: " + Minerva.JSON.parse(s));
};

var sendString = function(s) {
	stream.sendString(Minerva.JSON.asciify(s));
};

var protocol = new DemoProtocol();
var stream = new Minerva.ClientStream(new Minerva.HttpEndpoint("/_minerva/"));
stream.bindToProtocol(protocol);
stream.start();
</script>
"""


class DemoPage(Resource):
    isLeaf = True

    def render_GET(self, request: Request) -> bytes:
        return PAGE.encode()


async def main(reactor: IReactorCore) -> None:
    tracker = StreamTracker(reactor, DemoFactory())
    root = Resource()
    put_child(root, b"", DemoPage())
    put_child(root, b"_minerva", WebPort(reactor, tracker))
    # `timeout` is how long an HTTP connection without requests stays open.
    site = Site(root, timeout=75)
    await serverFromString(reactor, "tcp:10001:interface=127.0.0.1").listen(site)
    print("Open http://127.0.0.1:10001/ in your browser.")
    await Deferred()  # Serve until interrupted.


if __name__ == "__main__":
    task.react(main)
