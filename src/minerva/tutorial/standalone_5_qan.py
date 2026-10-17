"""
Tutorial 5: questions, answers, and notifications (QAN).

Instead of raw strings, the client and server *notify* each other, or *ask*
questions that get answers (or error-answers).  Your protocol implements
`minerva.QANProtocol`, wrapped in a `minerva.QANProtocolWrapper`.

Run it with `uv run python -m minerva.tutorial.standalone_5_qan`, then open
http://127.0.0.1:10001/ in a few browser tabs.
"""

import json

from twisted.internet import task
from twisted.internet.defer import Deferred
from twisted.internet.endpoints import serverFromString
from twisted.internet.interfaces import IReactorCore
from twisted.web.resource import Resource
from twisted.web.server import Request, Site

from minerva import QANHelper, QANProtocolWrapper, ServerStream, StreamTracker, WebPort
from minerva.web import put_child


# The server-side protocol, where you receive the client's questions and
# notifications.
class DemoProtocol:
    stream: ServerStream
    qan_helper: QANHelper

    def __init__(self, factory: DemoFactory, id: int) -> None:
        self.factory = factory
        self.id = id

    def notify_json(self, payload: object) -> None:
        self.qan_helper.notify(json.dumps(payload))

    def stream_started(self, stream: ServerStream, qan_helper: QANHelper) -> None:
        self.stream = stream
        self.qan_helper = qan_helper
        self.factory.clients[self.id] = self

    def stream_reset(self, reason_string: str, application_level: bool) -> None:
        print(f"Stream reset: {reason_string!r}")
        del self.factory.clients[self.id]

    def body_received(self, body: str, is_question: bool) -> str | None:
        """
        Return the answer to a question.  (For notifications, the return
        value is ignored.)
        """
        payload = json.loads(body)
        print(f"Received from client #{self.id}: {payload!r}, {is_question=}")

        match payload:
            case ["broadcast", str(text)]:
                for protocol in self.factory.clients.values():
                    if protocol is self:
                        protocol.notify_json(f"You told everyone: {text}")
                    else:
                        protocol.notify_json(f"Client #{self.id} told everyone: {text}")
            case ["privmsg", int(recipient), str(text)]:
                if (protocol := self.factory.clients.get(recipient)) is None:
                    self.notify_json(f"Sorry, #{recipient} isn't connected.")
                else:
                    self.notify_json(f"You told #{recipient}: {text}")
                    protocol.notify_json(f"Client #{self.id} told you: {text}")
            case ["listclients"]:
                return json.dumps(sorted(self.factory.clients))
            case _:
                self.notify_json(f"Sorry, I don't understand {payload!r}")
        return None


# The factory can hold data and objects shared by the connected protocols.
class DemoFactory:
    def __init__(self) -> None:
        self.client_counter = 0
        self.clients: dict[int, DemoProtocol] = {}

    def build_protocol(self) -> QANProtocolWrapper:
        self.client_counter += 1
        return QANProtocolWrapper(DemoProtocol(self, self.client_counter))


PAGE = r"""<!doctype html>
<div id="minerva-elements"></div> <!-- required container -->

Send Unicode string to everyone:
<input type="text" id="textinput_broadcast">
<input type="button" value="Send" onclick="broadcastString(byId('textinput_broadcast').value)">
<br>

Send Unicode string to client #<input type="text" id="recipient" size=2>:
<input type="text" id="textinput_privmsg">
<input type="button" value="Send" onclick="privmsgString(parseInt(byId('recipient').value), byId('textinput_privmsg').value)">
<br>

<input type="button" value="Get list of clients" onclick="getClients()">

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
DemoProtocol.prototype.streamStarted = function(stream, qanHelper) {
	this.stream = stream;
	this.qanHelper = qanHelper;
};
DemoProtocol.prototype.streamReset = function(reasonString, applicationLevel) {
	logMessage("Stream reset: " + reasonString);
	logMessage("Reload the page to reconnect.");
};
DemoProtocol.prototype.bodyReceived = function(s, isQuestion) {
	logMessage("Received " + (isQuestion ? "question" : "notification") +
		" from server: " + Minerva.JSON.parse(s));
};

var broadcastString = function(s) {
	protocol.qanHelper.notify(Minerva.JSON.asciify(['broadcast', s]));
};

var privmsgString = function(id, s) {
	protocol.qanHelper.notify(Minerva.JSON.asciify(['privmsg', id, s]));
};

var getClients = function() {
	// .ask returns a Minerva.Deferred (goog.async.Deferred) object
	var d = protocol.qanHelper.ask(Minerva.JSON.asciify(['listclients']));
	d.addCallback(function(json) {
		var clients = Minerva.JSON.parse(json);
		logMessage("Connected clients: " + clients.join(", "));
	});
	d.addErrback(function(e) {
		logMessage("Ask error: " + e);
	});
};

var protocol = new DemoProtocol();
var stream = new Minerva.ClientStream(new Minerva.HttpEndpoint("/_minerva/"));
var wrapper = new Minerva.QANProtocolWrapper(protocol);
stream.bindToProtocol(wrapper);
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
