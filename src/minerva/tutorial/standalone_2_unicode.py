"""
Tutorial 2: send Unicode text, by encoding it as JSON.

Minerva strings are restricted to the characters " " to "~".  JSON (with its
default `ensure_ascii=True`) fits in that range, so it is an easy way to send
anything else.

Run it with `uv run python -m minerva.tutorial.standalone_2_unicode`, then open
http://127.0.0.1:10001/ in your browser.
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

    def stream_started(self, stream: ServerStream) -> None:
        self.stream = stream

    def stream_reset(self, reason_string: str, application_level: bool) -> None:
        print(f"Stream reset: {reason_string!r}")

    def string_received(self, s: str) -> None:
        text = json.loads(s)
        print(f"Received from client: {text!r}")
        first_word = text.split()[0] if text.split() else ""
        self.stream.send_string(
            json.dumps(
                f"Hey client, you sent me a string with {len(text)} characters; "
                f"first word was {first_word}"
            )
        )


# The factory can hold data and objects shared by the connected protocols.
class DemoFactory:
    def build_protocol(self) -> DemoProtocol:
        return DemoProtocol()


PAGE = r"""<!doctype html>
<div id="minerva-elements"></div> <!-- required container -->

Send Unicode string to server:
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
