from collections import deque
import simplejson as json

from twisted.python import log
from twisted.protocols import policies
from twisted.web import resource
from twisted.internet import protocol
from zope.interface import Interface

"""
   C2STransport \
   S2CTransport -\
   S2CTransport <-> Stream -\
(both)Transport <-> Stream <-> UA <-> User
(both)Transport <-> Stream <-> UA -/

A Stream can have more than one S2CTransport:

	Client-side Minerva might be in the middle of upgrading or downgrading
	to a different type of S2CTransport. (for example, from XHR stream to
	Flash, or from XHR stream to long-poll)

	Client-side Minerva may establish a second S2CTransport before first
	S2CTransport is "done", to reduce the small time gap caused by
	request/connection re-establishment.

A UA (held together by a cookie) can have more than Stream:

	With Chrome, we might have the same cookie,
	yet not be able to share data between tabs.

	Some minor or future browsers may make it too difficult (like Chrome)
	to share a stream across tabs/windows, yet still have the same
	session cookie.

User can have more than one UA:

	User might be connecting from multiple browsers.

	User might be connecting from multiple IPs.

	Many browsers provide an "incognito" mode where cookies are not shared
	with the non-incognito mode. This is sort of like having a second browser.

Clients will spend most of their time dealing with a Stream by receiving
and sending boxes over it. Clients upload boxes to the Stream, not the
UA.

A FlashSocketTransport would just give the box to the Stream.  The
other C2S transport (XHR calls) is not represented by an instance of
some kind of Transport The twisted.web Resource just gives the box to
the Stream.

Ideas for Transport types:
	XHRTransport (s2c)
		both "stream" and 1-shot mode.
	ScriptTransport (s2c)
		both htmlfile and Firefox/Safari mode.
	SSETransport (s2c)
		Server-sent events (Opera)
	FlashSocketTransport (s2c,c2s)


Client-side notes:

Client should know how to get establish a downstream and upstream transport
in one step (using just the information on the generated HTML page). There
should be no additional negotiation, unless absolutely necessary.

The server will generate a "base Stream ID" (128 bits), and the client will
add a "-<number>" suffix where <number> is incremented for each stream
created with the same "base Stream ID". Client will always upload the Stream ID
for both S2C and C2S (both HTTP), and for Flash socket.

We actually don't need the client to send the session ID (though they'll do it
anyway over HTTP), because server already knows which stream IDs belong to
a session ID.
"""


def nonnegint(value):
	"""
	Everybody forgets to check that an integer is non-negative.
	So use nonnegint() instead of int() where possible.

	This can still return either a L{TypeError} or a L{ValueError}.
	"""
	out = int(value)
	if out < 0:
		raise ValueError("value %r was negative" % (value,))
	return out


class GenericTimeoutMixin(object):
	"""
	Mixin for any instance that has a L{_reactor} attribute and wants a timeout.

	This is mostly a copy/paste of twisted.protocols.policies.TimeoutMixin

	@cvar timeOut: The number of seconds after which to timeout the connection.
	"""
	timeOut = None

	__timeoutCall = None

	def resetTimeout(self):
		"""
		Reset the timeout count down.
		"""
		if self.__timeoutCall is not None and self.timeOut is not None:
			self.__timeoutCall.reset(self.timeOut)


	def setTimeout(self, period):
		"""
		Change the timeout period

		@type period: C{int} or C{NoneType}
		@param period: The period, in seconds, to change the timeout to, or
		C{None} to disable the timeout.
		"""
		prev = self.timeOut
		self.timeOut = period

		if self.__timeoutCall is not None:
			if period is None:
				self.__timeoutCall.cancel()
				self.__timeoutCall = None
			else:
				self.__timeoutCall.reset(period)
		elif period is not None:
			self.__timeoutCall = self._reactor.callLater(period, self.__timedOut)

		return prev


	def __timedOut(self):
		self.__timeoutCall = None
		self.timedOut()


	def 	timedOut(self):
		"""
		The timeout has been triggered. Override this.
		"""


class StreamEndedReasonTimeout(object):
	"""
	The client failed to establish a [transport that has S2C] in time.
	"""


# TODO: actually decide what the "close connection" box looks like.
class StreamEndedReasonClosed(object):
	"""
	The client closed the stream explicitly.
	"""


class ClientSentTooHighAck(Exception):
	"""
	Client sent a bogus S2C ACK number.
	"""


class Queue(object):

	def __init__(self):
		# The sequence number of the 0th item in the queue
		self.seqNumAt0 = 0
		self._items = deque()


	def append(self, item):
		return self._items.append(item)


	def __len__(self):
		return len(self._items)


	def removeUpTo(self, seqNum):
		"""
		Remove items up to sequence number L{seqNum}.
		"""
		assert seqNum >= 0, seqNum

		for i in xrange(seqNum - self.seqNumAt0):
			self._items.popleft()

		self.seqNumAt0 += seqNum



class Stream(object, GenericTimeoutMixin):
	"""
	I am Stream. Transports attach to me. I can send and receive over
	a new transport, or a completely different transport, without restarting
	the Stream.

	I know my StreamFactory, L{self.factory}
	"""

	noisy = True

	def __init__(self, streamId):
		# TODO: a better queue that one can manipulate (remove
		# now-obsolete messages)
		self._queue = Queue()
		self._transports = set()

		self._seqC2S = 0 # TODO: use it
		self.id = streamId
		

	def __repr__(self):
		return '<Stream %r (%d,%d) with transports %r and %d items in queue>' % (
			self.id, self._queue.seqNumAt0, self._seqC2S, self._transports, len(self._queue))


	def streamBegun(self):
		"""
		The stream has begun. Override this if necessary.
		"""


	def streamEnded(self, reason):
		"""
		(Override this to do something with the UA, or
		clear circular references if necessary.)

		Stream L{stream} no longer appears to be online. This method
		can help determine when "a user is no longer online", but keep
		in mind that they are only "offline" when *all* streams for a UA
		are gone.

		Most likely reasons are:
			they closed the page
			they shut down computer
			JavaScript execution has stopped for any reason
		"""


	def boxReceived(self, box):
		"""
		Received box L{box}. Override this.
		"""
		log.msg('Received box:', box)


	def sendBox(self, box):
		"""
		Enqueue box L{box} for sending soon.
		"""
		log.msg('Queuing box for sending:', box)
		self._queue.append(box)


	def clientReceivedUpTo(self, seqNum):
		"""
		The client claims to have received S2C messages up to sequence
		number L{seqNum}, so now it is okay to clear the messages from
		the queue.
		"""
		assert seqNum >= 0, seqNum

		if seqNum > (len(self._queue) + self._queue.seqNumAt0):
			raise ClientSentTooHighAck(
				"seqNum = %d, len(self._queue) = %d, self._queue.seqNumAt0 = %d"
				% (seqNum, len(self._queue), self._queue.seqNumAt0))

		if seqNum - self._queue.seqNumAt0 < 0:
			if self.noisy:
				log.msg("Client sent a strangely low S2C ACK; not removing anything from the queue.")
			return

		self._queue.removeUpTo(seqNum)


	def _selectS2CTransport(self):
		if len(self._transports) == 0:
			return None

		if len(self._transports) > 1:
			# Select the transport with the highest connectionNumber.
			# TODO: should there be any other criteria?
			transport = sorted(self._transports, key=lambda t: t.connectionNumber, reverse=True)
			if self.noisy:
				log.msg("Multiple S2C transports: %r, so I picked the newest: %r" % (
					self._transports, transport,))

		transport = self._transports[0]

		return transport


	def _sendBoxes(self):
		"""
		Try to send boxes.
		"""
		transport = self._selectS2CTransport()
		if not transport:
			if self.noisy:
				log.msg("Don't have any S2C transports; can't send.")
			return
		transport.handle(self._queue)


	def transportOnline(self, transport):
		"""
		For internal use.
		"""
		self.setTimeout(None)
		log.msg('New transport has come online:', transport)
		self._transports.add(transport)
		self._sendBoxes()


	def transportOffline(self, transport):
		"""
		For internal use.
		"""
		log.msg('Transport has left:', transport)
		# This will raise an exception if it's not there
		self._transports.remove(transport)

		if len(self._transports) == 0:
			# Start the timer. If no transports come in 30 seconds,
			# the stream has ended.
			self.setTimeout(30)


	def timedOut(self):
		self.streamEnded(StreamEndedReasonTimeout())



class StreamFactory(object):
	"""
	I make Stream instances.

	I can locate a Stream by Stream ID. This is important
	because we want to send messages to other Streams.
	"""

	stream = Stream

	def __init__(self, reactor):
		self._reactor = reactor
		self._streams = {}


	def buildStream(self, streamId):
		s = self.stream(streamId)
		s.factory = self
		s._reactor = self._reactor
		s.streamBegun()
		return s


	def locateStream(self, streamId):
		"""
		Returns the Stream instance for L{streamId}, or L{None} if not found.
		"""
		return self._streams.get(streamId)


	def locateOrBuild(self, streamId):
		s = self.locateStream(streamId)
		if s is None:
			s = self.buildStream(streamId)
		return s



class _BaseHTTPTransport(object):
	"""
	frags (fragments) are any object, including metadata needed for connection management.
	boxes are something that was actually in a queue.
	"""

	maxKB = None

	def __init__(self, request, connectionNumber):
		"""
		I need a L{twisted.web.http.Request}.
		
		L{connectionNumber} is incremented by the client as they
			open S2C transports.
		"""
		self._request = request
		# TODO: set tcp no delay
		self.connectionNumber = connectionNumber
		self._sentFirstFrag = False
		self._fragsSent = 0
		self._bytesSent = 0

		# TCP nodelay is good and increases server performance, as
		# long as we don't accidentally send small packets.
		request.channel.transport.setTcpNoDelay(True)


	def getHeader(self):
		return ''


	def getFooter(self):
		return ''


	def handle(self, queue):
		"""
		Write as many messages from the queue as possible.
		"""
		toSend = ''
		fragCount = 0
		byteCount = 0

		if not self._sentFirstFrag:
			self._sentFirstFrag = True

			# the header is not a frag, so only increment byteCount
			header = self.getHeader()
			byteCount += len(header)

			seqString = self._stringOne(['`^a', queue.seqNumAt0])
			toSend += seqString
			fragCount += 1
			byteCount += len(seqString)

		for n, box in enumerate(queue):
			boxString = self._stringOne(box)
			toSend += boxString
			fragCount += 1
			byteCount += len(boxString)
			if byteCount > self.maxKB:
				break

		if byteCount > self.maxKB:
			footer = self.getFooter()

			# the footer is not a frag, so only increment byteCount
			byteCount += len(footer)

		self._request.write(toSend)
		self._bytesSent += byteCount
		self._fragsSent += fragCount


	# writeBox is very bad:
	#	- uses a TCP packet per write()
	#	- ScriptTransport may need a header and footer
	def writeBox(self, seqNumber, box):
		"""
		Write box L{box} to the HTTP response.

		Return True if this transport could write another box,
		False otherwise.
		"""
		if not self._sentFirstFrag:
			self._sentFirstFrag = True
			# Streaming transports write an sequence number
			# only before the first box. The client knows that
			# each box increments the S2C sequence number by 1.
			self._reallyWriteBox(['`^a', seqNumber])

		self._reallyWriteBox(box)
		if self._bytesSent > self.maxKB:
			# Can't send any more.
			self._request = None
			return False
		else:
			return True



class XHRTransport(_BaseHTTPTransport):

	# TODO: long-polling mode

	# TODO: need to send the 256/512/2KB/4KB prefix
	# to bypass content detection (which blocks the stream in many browsers)

	maxKB = 300

	def __repr__(self):
		return '<XHRTransport at %s attached to %r with %d frags sent>' % (
			hex(id(self)), self._request, self._fragsSent)


	def _stringOne(self, box):
		"""
		Return a serialized string for one box.
		"""
		# TODO: For some browsers (without the native JSON object),
		# dump more compact "JSON" without the single quotes around properties

		s = json.dumps(box, separators=(',', ':'))
		return str(len(s)) + ',' + s



class ScriptTransport(_BaseHTTPTransport):
	"""
	I'm a transport that writes <script> tags to a forever-frame
	(both the IE htmlfile and the Firefox iframe variants)
	"""

	maxKB = 300

	def __repr__(self):
		return '<ScriptTransport at %s attached to %r with %d frags sent>' % (
			hex(id(self)), self._request, self._fragsSent)


	# TODO: maybe this header should be written earlier, even before the first attempt
	# to send to queue?
	def getHeader(self):
		# CWNet = CW.Net
		# 'fr' = "frame"
		# 'o' = object
		return '''<!doctype html><head><script>function f(o){parent.__CWNet_fr(o)}</script></head><body>'''


	def getFooter(self):
		return '</body></html>'


	def _stringOne(self, box):
		"""
		Return a serialized string for one box.
		"""
		# TODO: dump more compact "JSON" without the single quotes around properties
		s = json.dumps(box, separators=(',', ':'))
		# TODO: find out if there's a way to close a script tag in IE or FF/Safari
		# without sending an entire </script>
		return '<script>f(%s)</script>' % (s,)



# TODO
class SSETransport(_BaseHTTPTransport):

	maxKB = 1024 # Does this even need a limit?

	def __repr__(self):
		return '<SSETransport at %s attached to %r with %d frags sent>' % (
			hex(id(self)), self._request, self._fragsSent)




class SocketTransport(protocol.Protocol):
	# XXX Should this be both a Protocol and a Minerva transport?
	# That would be kind of strange?
	"""
	Right now, this is only used for the Flash socket.
	"""

	def connectionMade(self):
		pass


	def dataReceived(self, data):
		"""
		Client needs to send server the stream ID, because server
		doesn't know anything about the client yet.
		"""


	def connectionLost(self, reason):
		"""
		The socket connection has been lost, so notify the stream.
		"""



class EncryptedSocketTransport(protocol.Protocol):
	pass
	# TODO: need to port Scrypto to non-ctypes



class InvalidArgumentsError(Exception):
	pass



class HTTPS2C(resource.Resource):
	isLeaf = True

	def __init__(self, streamFactory):
		self._streamFactory = streamFactory


	def render_GET(self, request):
		# TODO: verify that the stream belongs to the UA,
		# to make it slightly harder to hijack a stream over HTTP.

		def _fail():
			raise InvalidArgumentsError("request.args = " + repr(request.args))

		try:
			streamId = request.args['i'][0].decode('hex') # "(i)d"

			# Incremented each time the client makes a HTTP request for S2C
			# TODO: disconnect the old S2C transport if a newer transport has arrived
			# (with higher connectionNumber)
			connectionNumber = nonnegint(request.args['n'][0]) # "(n)umber"

			# Last box that the client received
			ackS2C = nonnegint(request.args['s'][0]) # "(s)eq"

			# The type of S2C transport requested.
			transportString = request.args['t'][0] # "(t)ype"
		except (KeyError, IndexError, ValueError, TypeError):
			_fail()

		if transportString == 's':
			transport = ScriptTransport(request, connectionNumber)
		elif transportString == 'x':
			transport = XHRTransport(request, connectionNumber)
		elif transportString == 'o':
			transport = SSETransport(request, connectionNumber)
		else:
			_fail()

		s = self._streamFactory.locateOrBuild(streamId)
		s.clientReceivedUpTo(ackS2C)

		s.transportOnline(transport)

		d = request.notifyFinish()
		d.addCallback(s.transportOffline, transport)
		
		return 'GET S2C'


	def render_POST(self, request):
		return 'POST S2C TODO IMPLEMENT'



class HTTPC2S(resource.Resource):
	isLeaf = True

	def render_GET(self, request):
		return 'GET C2S'


	def render_POST(self, request):
		return 'POST C2S'



#class QueueFinder(object):
#
#	def __init__(self):
#		self.registry = {}
#
#
#	def find(self, qID):
#		return self.registry[qID]
#
#
#	def register(self, sendQueue):
#		self.registry[sendQueue.qID] = sendQueue
#
#
#
#class EmptyQueueError(Exception):
#	pass
#
#
#class SendQueue(object):
#
#	def __init__(self, qID):
#		self.qID = qID
#		self.queue = deque()
#
#
#	def add(self, obj):
#		self.queue.append(obj)
#
#
#	def getOne(self):
#		try:
#			return self.queue.popleft()
#		except IndexError:
#			raise EmptyQueueError()
#
