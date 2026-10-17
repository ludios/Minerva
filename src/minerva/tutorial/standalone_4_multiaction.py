"""
Tutorial 4: several kinds of messages, dispatched with `match`.

Clients send JSON arrays like `["broadcast", text]` or
`["privmsg", recipient, text]`.

Run it with `uv run python -m minerva.tutorial.standalone_4_multiaction`, then
open http://127.0.0.1:10001/ in a few browser tabs.
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

    def send_json(self, payload: object) -> None:
        self.stream.send_string(json.dumps(payload))

    def stream_started(self, stream: ServerStream) -> None:
        self.stream = stream
        self.factory.clients[self.id] = self

    def stream_reset(self, reason_string: str, application_level: bool) -> None:
        print(f"Stream reset: {reason_string!r}")
        del self.factory.clients[self.id]

    def string_received(self, s: str) -> None:
        payload = json.loads(s)
        print(f"Received from client #{self.id}: {payload!r}")

        match payload:
            case ["broadcast", str(text)]:
                for protocol in self.factory.clients.values():
                    if protocol is self:
                        protocol.send_json(f"You told everyone: {text}")
                    else:
                        protocol.send_json(f"Client #{self.id} told everyone: {text}")
            case ["privmsg", int(recipient), str(text)]:
                if (protocol := self.factory.clients.get(recipient)) is None:
                    self.send_json(f"Sorry, #{recipient} isn't connected.")
                else:
                    self.send_json(f"You told #{recipient}: {text}")
                    protocol.send_json(f"Client #{self.id} told you: {text}")
            case _:
                self.send_json(f"Sorry, I don't understand {payload!r}")


# The factory can hold data and objects shared by the connected protocols.
class DemoFactory:
    def __init__(self) -> None:
        self.client_counter = 0
        self.clients: dict[int, DemoProtocol] = {}

    def build_protocol(self) -> DemoProtocol:
        self.client_counter += 1
        return DemoProtocol(self, self.client_counter)


PAGE = r"""<!doctype html>
<div id="minerva-elements"></div> <!-- required container -->

Send Unicode string to everyone:
<input type="text" id="textinput_broadcast">
<input type="button" value="Send" onclick="broadcastString(byId('textinput_broadcast').value)">
<br>

Send Unicode string to client #<input type="text" id="recipient" size=2>:
<input type="text" id="textinput_privmsg">
<input type="button" value="Send" onclick="privmsgString(parseInt(byId('recipient').value), byId('textinput_privmsg').value)">

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

var broadcastString = function(s) {
	stream.sendString(Minerva.JSON.asciify(['broadcast', s]));
};

var privmsgString = function(id, s) {
	stream.sendString(Minerva.JSON.asciify(['privmsg', id, s]));
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
