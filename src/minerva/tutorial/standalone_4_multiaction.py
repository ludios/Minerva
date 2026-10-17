# Since we're not using twistd, we need to set up logging.
import sys
from twisted.python import log
log.startLogging(sys.stdout)

from twisted.web import resource, server
from twisted.internet import reactor

from minerva.mserver import WebPort, StreamTracker

try:
	import simplejson as json
except ImportError:
	import json


def sendJsonTo(protocol, payload):
	protocol.stream.sendString(json.dumps(payload))

# This is the server-side protocol where you'll receive the client's strings.
class DemoProtocol(object):
	def streamStarted(self, stream):
		self.stream = stream
		self.id = self.factory.clientCounter
		self.factory.clients[self.id] = self

	def streamReset(self, reasonString, applicationLevel):
		log.msg("Stream reset: %r" % (reasonString,))
		del self.factory.clients[self.id]

	def stringReceived(self, s):
		payload = json.loads(s)
		print "Received from client #%d: %r" % (self.id, payload)

		action = payload[0]
		if action == u'broadcast':
			_, text = payload
			for protocol in self.factory.clients.itervalues():
				if protocol == self:
					sendJsonTo(protocol, u"You told everyone: %s" % (text,))
				else:
					sendJsonTo(protocol, u"Client #%d told everyone: %s" % (self.id, text))
		elif action == u'privmsg':
			_, recipient, text = payload
			try:
				protocol = self.factory.clients[recipient]
			except KeyError:
				sendJsonTo(self, u"Sorry, #%d isn't connected." % (recipient,))
			else:
				sendJsonTo(self, u"You told #%d: %s" % (recipient, text))
				sendJsonTo(protocol, u"Client #%d told you: %s" % (self.id, text))


# The factory can be used to store data and instantiate objects
# shared by the connected protocols.
class DemoFactory(object):
	def __init__(self):
		self.clientCounter = 0
		self.clients = {}

	def buildProtocol(self):
		self.clientCounter += 1
		protocol = DemoProtocol()
		protocol.factory = self
		return protocol


class MyDemo(resource.Resource):
	def render_GET(self, request):
		return r"""<!doctype html>
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


class Root(resource.Resource):
	def __init__(self, webPort):
		resource.Resource.__init__(self)
		self.putChild('', MyDemo())
		self.putChild('_minerva', webPort)


def makeSite():
	clock = reactor
	factory = DemoFactory()
	tracker = StreamTracker(clock, factory)
	webPort = WebPort(clock, tracker)
	root = Root(webPort)
	# timeout= is twisted.web's keep-alive timeout that determines how long
	# before the server disconnects HTTP connections with no active requests.
	return server.Site(root, timeout=75)


reactor.listenTCP(10001, makeSite())
reactor.run()
