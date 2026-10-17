# Since we're not using twistd, we need to set up logging.
import sys
from twisted.python import log
log.startLogging(sys.stdout)

from twisted.web import resource, server
from twisted.internet import reactor, task
from twisted.names.client import getHostByName

from minerva.mserver import WebPort, StreamTracker, QANProtocolWrapper

try:
	import simplejson as json
except ImportError:
	import json


def notifyJsonTo(protocol, payload):
	protocol.qanHelper.notify(json.dumps(payload))

# This is the server-side protocol where you'll receive the client's questions and notifications.
class DemoProtocol(object):
	def __init__(self, clock):
		self._clock = clock

	def streamStarted(self, stream, qanHelper):
		self.stream = stream
		self.qanHelper = qanHelper
		self.id = self.factory.clientCounter
		self.factory.clients[self.id] = self

	def streamReset(self, reasonString, applicationLevel):
		log.msg("Stream reset: %r" % (reasonString,))
		del self.factory.clients[self.id]

	def bodyReceived(self, s, isQuestion):
		payload = json.loads(s)
		print "Received from client #%d: %r, isQuestion=%r" % (self.id, payload, isQuestion)

		action = payload[0]
		if action == u'broadcast':
			_, text = payload
			for protocol in self.factory.clients.itervalues():
				if protocol == self:
					notifyJsonTo(protocol, u"You told everyone: %s" % (text,))
				else:
					notifyJsonTo(protocol, u"Client #%d told everyone: %s" % (self.id, text))
		elif action == u'privmsg':
			_, recipient, text = payload
			try:
				protocol = self.factory.clients[recipient]
			except KeyError:
				notifyJsonTo(self, u"Sorry, #%d isn't connected." % (recipient,))
			else:
				notifyJsonTo(self, u"You told #%d: %s" % (recipient, text))
				notifyJsonTo(protocol, u"Client #%d told you: %s" % (self.id, text))
		elif action == u'listclients':
			return json.dumps(self.factory.clients.keys())
		elif action == u'listclients_in_1_sec':
			# This can of course be any function that returns a Deferred,
			# like t.web.client.getPage
			d = task.deferLater(self._clock, 1.0, lambda: None)
			def listClients(_):
				return json.dumps(self.factory.clients.keys())
			d.addCallback(listClients)
			return d


# The factory can be used to store data and instantiate objects
# shared by the connected protocols.
class DemoFactory(object):
	def __init__(self, clock):
		self._clock = clock
		self.clientCounter = 0
		self.clients = {}

	def buildProtocol(self):
		self.clientCounter += 1
		protocol = DemoProtocol(self._clock)
		protocol.factory = self
		return QANProtocolWrapper(protocol)


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
<br>

<input type="button" value="Get list of clients" onclick="getClients('listclients')">
<input type="button" value="Get list of clients after 1 sec" onclick="getClients('listclients_in_1_sec')">

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

var getClients = function(command) {
	// .ask returns a Minerva.Deferred (goog.async.Deferred) object
	var d = protocol.qanHelper.ask(Minerva.JSON.asciify([command]));
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


class Root(resource.Resource):
	def __init__(self, webPort):
		resource.Resource.__init__(self)
		self.putChild('', MyDemo())
		self.putChild('_minerva', webPort)


def makeSite():
	clock = reactor
	factory = DemoFactory(clock)
	tracker = StreamTracker(clock, factory)
	webPort = WebPort(clock, tracker)
	root = Root(webPort)
	# timeout= is twisted.web's keep-alive timeout that determines how long
	# before the server disconnects HTTP connections with no active requests.
	return server.Site(root, timeout=75)


reactor.listenTCP(10001, makeSite())
reactor.run()
