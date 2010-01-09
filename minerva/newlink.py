"""
You really want to read docs/Overview.rst to understand the code in this file.

See minerva/sample/demo.py for an idea of how to use the classes below.
"""

from minerva import abstract, decoders

import simplejson
import binascii
import traceback
from zope.interface import Interface, Attribute, implements
from twisted.python import log
from twisted.internet import protocol, defer
from twisted.internet.main import CONNECTION_LOST
from twisted.internet.interfaces import IPushProducer, IPullProducer, IProtocol, IProtocolFactory
from twisted.python.failure import Failure
from twisted.web import resource

_postImportVars = vars().keys()


# Copy/paste of twisted.internet.interfaces.IConsumer, with 'write' method removed
class ISimpleConsumer(Interface):
	"""
	A consumer consumes data from a producer.
	"""

	def registerProducer(producer, streaming):
		"""
		Register to receive data from a producer.

		This sets self to be a consumer for a producer.  When this object runs
		out of data (as when a send(2) call on a socket succeeds in moving the
		last data from a userspace buffer into a kernelspace buffer), it will
		ask the producer to resumeProducing().

		For L{IPullProducer} providers, C{resumeProducing} will be called once
		each time data is required.

		For L{IPushProducer} providers, C{pauseProducing} will be called
		whenever the write buffer fills up and C{resumeProducing} will only be
		called when it empties.

		@type producer: L{IProducer} provider

		@type streaming: C{bool}
		@param streaming: C{True} if C{producer} provides L{IPushProducer},
		C{False} if C{producer} provides L{IPullProducer}.

		@raise RuntimeError: If a producer is already registered.

		@return: C{None}
		"""


	def unregisterProducer():
		"""
		Stop consuming data from a producer, without disconnecting.
		"""



class BadFrame(Exception):
	pass



class Frame(object):
	"""
	I represent a frame. When instantiated, I will check that
	the frame type is valid, and that the number of arguments
	in the frame is correct. I will not actually check the arguments,
	though.

	I do not have a `toBytes' method or similar because
	different transports require different serializations.
	"""

	# Most-frequently-used types should be non-negative and single-digit.
	# num -> (name, minArgs, maxArgs)
	knownTypes = {
		0: ('boxes', 1, 1),
		1: ('box', 1, 1),
		2: ('seqnum', 1, 1),

		4: ('sack', 2, 2),
		5: ('hello', 1, 1),
		6: ('gimme_boxes', 1, 1),

		8: ('timestamp', 1, 1),
		10: ('reset', 2, 2), # reset really means "Stream is dead to me. Also, transport kill because stream is dead."

		11: ('you_close_it', 0, 0),
		12: ('start_timestamps', 3, 3),
		13: ('stop_timestamps', 1, 1),

		20: ('padding', 1, 1),

		601: ('tk_stream_attach_failure', 0, 0), # Either because no such Stream, or bad credentialsData
		602: ('tk_acked_unsent_boxes', 0, 0),
		603: ('tk_invalid_frame_type_or_arguments', 0, 0), # TODO: test that transportOffline is called when client causes this after transport attached to a Stream
		610: ('tk_frame_corruption', 0, 0),
		611: ('tk_intraframe_corruption', 0, 0),
		650: ('tk_brb', 1, 1), # Server is overloaded or shutting down, tells client to come back soon
	}

	class names:
		pass
	names = names()
	for num, (name, minArgs, maxArgs) in knownTypes.iteritems():
		setattr(names, name, num)

	__slots__ = ['contents', 'type']

	def __init__(self, contents):
		"""
		Convert C{list} C{contents} to a L{Frame}.

		@throws: L{BadFrame} if cannot convert
		"""
		try:
			self.type = contents[0]
		except (IndexError, KeyError, TypeError):
			raise BadFrame("Frame did not have a [0]th item")
		try:
			typeInfo = self.knownTypes[self.type]
		except (KeyError, TypeError):
			raise BadFrame("Frame(%r) has unknown frame type %r, or [0]th item was not hashable" % (contents, self.type))

		_, minArgs, maxArgs = typeInfo
		if not minArgs <= len(contents) - 1 <= maxArgs:
			raise BadFrame("Bad argument count for Frame type %r (%r); got %d args." % (self.type, self.getType(), len(contents) - 1))

		self.contents = contents


	def __repr__(self):
		return '<%s type %r, contents %r>' % (
			self.__class__.__name__, self.knownTypes[self.type][0], self.contents)


	def getType(self):
		return self.knownTypes[self.type][0]



Fn = Frame.names
# make globals that will be optimized away by pypycpyo.optimizer
Fn_boxes = Fn.boxes
Fn_box = Fn.box
Fn_seqnum = Fn.seqnum
Fn_sack = Fn.sack
Fn_hello = Fn.hello
Fn_gimme_boxes = Fn.gimme_boxes
Fn_reset = Fn.reset
Fn_you_close_it = Fn.you_close_it



class WhoReset(object):
	__slots__ = []
	server_minerva = 1
	server_app = 2
	client_minerva = 3
	client_app = 4



class IMinervaProtocol(Interface):
	"""
	An interface for frame-based communication that abstracts
	away the Comet logic and transports.

	I'm analogous to L{twisted.internet.interfaces.IProtocol}

	Note: if you call stream.reset, some (or all) of the boxes you
	have recently sent may be lost. If you need a proper close, use
	your own boxes to determine that it is safe to close, then call reset.

	Note: the stream never ends due to inactivity (there
	are no timeouts in Stream). If you want to end the stream,
	call stream.reset(u"reason why")

	The simplest way to end dead Streams is to use an application-level
	ping message that your client sends (say every 55 seconds), and
	end the Stream if no such message has been received for 2 minutes.

	TODO: expose a `primaryOnline` and `primaryOffline` or a similar
	scheme to know some information about whether the client is even
	connected to Minerva server.
	"""

	def streamStarted(stream):
		"""
		Called when this stream has just started.

		You'll want to keep the stream around with C{self.stream = stream}.

		You must *not* raise any exception. Wrap your code in try/except if necessary.

		@param stream: the L{Stream} that was started.
		@type stream: L{Stream}
		"""


	def streamReset(whoReset, reasonString):
		"""
		Call when this stream has reset, either internally by Minerva server's Stream, or
		a call to Stream.reset, or by a reset frame from the peer.

		You must *not* raise any exception. Wrap your code in try/except if necessary.

		@param whoReset: who reset the Stream. One of
		C{WhoReset.{server_minerva,server_app,client_minerva,client_app}}.
		@type whoReset: int

		@param reasonString: why the L{Stream} has reset.
		@type reasonString: C{unicode} or ASCII-only C{str}
		"""


	def boxesReceived(boxes):
		"""
		Called whenever box(es) are received.

		You must *not* raise any exception. Wrap your code in try/except if necessary.

		@type boxes: list
		@param boxes: a list of boxes
		"""



class BasicMinervaProtocol(object):
	"""
	A "base" implementation of L{IMinervaProtocol} that you don't
	have to subclass, but can.
	"""
	implements(IMinervaProtocol)

	def streamStarted(self, stream):
		self.stream = stream


	def streamReset(self, whoReset, reasonString):
		del self.stream


	def boxesReceived(self, boxes):
		pass



class IMinervaFactory(Interface):
	"""
	Interface for L{MinervaProtocol} factories.
	"""

	def buildProtocol():
		"""
		Called when a Stream has been established.

		Unlike the analogous Twisted L{twisted.internet.interfaces.IFactory},
		you cannot refuse a connection here.

		An implementation should
			construct an object providing I{MinervaProtocol},
			do C{obj.factory = self},
			and return C{obj},
		with optionally more steps in between.

		@return: an object providing L{IMinervaProtocol}.
		"""



class BasicMinervaFactory(object):
	"""
	A "base" implementation of L{IMinervaFactory} that you don't
	have to subclass, but can.

	Override the C{protocol} attribute.
	"""
	implements(IMinervaFactory)

	protocol = None

	def buildProtocol(self):
		obj = self.protocol()
		obj.factory = self
		return obj



class IStreamNotificationReceiver(Interface):
	"""
	Objects that implement this can get notified about new and dying Streams.

	The intention is for some L{ITransportFirewall}s to use this.
	"""
	def streamUp(stream):
		"""
		Stream L{stream} has appeared.

		@type stream: L{Stream}

		Do not raise exceptions in your implementation.
		Doing so will break the building of the stream (the problem will bubble all the
		way back to the peer). If any observer raises an exception, `streamDown' will
		never be called for L{stream}. Also, an arbitrary number of other observers will not
		receive the `streamUp' call in the first place.
		"""


	def streamDown(stream):
		"""
		Stream L{stream} is gone.

		@type stream: L{Stream}

		Do not raise exceptions in your implementation.
		Doing so will prevent an arbitrary number of other observers from receiving
		the notification.
		"""



# There is no factory for customizing the construction of L{Stream}s, just like
# there is no factory for customizing the construction of L{twisted.internet.tcp.Server}s in Twisted.
class Stream(object):
	"""
	I'm sort-of analogous to L{twisted.internet.tcp.Connection}

	The producer/consumer here is designed to deal with TCP bandwidth pressure
	(and "lack of any S2C transport" pressure). It does not help with any kind of
	application-level pressure. Applications that want high-volume
	streaming should implement an application-level producer/consumer system.
	"""

	implements(ISimpleConsumer) # Does not implement IPushProducer or IPullProducer because it does not expect stopProducing

	maxUndeliveredBoxes = 5000 # boxes
	maxUndeliveredBytes = 4 * 1024 * 1024 # bytes

	__slots__ = (
		'_clock,streamId,_streamProtocolFactory,_protocol,virgin,_primaryTransport,'
		'_notifications,_transports,disconnected,queue,_incoming,_pretendAcked,'
		'_producer,_streamingProducer,_primaryHasProducer,_primaryPaused').split(',')

	def __init__(self, clock, streamId, streamProtocolFactory):
		self._clock = clock
		self.streamId = streamId
		self._streamProtocolFactory = streamProtocolFactory
		self._protocol = self._primaryTransport = self._pretendAcked = self._producer = None
		self.disconnected = self._streamingProducer = self._primaryHasProducer = self._primaryPaused = False
		# _primaryPaused: Does the primary transport think it is paused? Or if no primary transport, False.

		self.virgin = True # no transports have ever attached to it
		self._notifications = []
		self._transports = set()

		self.queue = abstract.Queue()
		self._incoming = abstract.Incoming()


	def __repr__(self):
		return ('<%s streamId=%r, len(queue)=%d, disconnected=%r>'
			% (self.__class__.__name__, self.streamId, len(self.queue), self.disconnected))


	def _tryToSend(self):
		##print '_tryToSend', self, self._primaryTransport, self.queue
		if len(self.queue) == 0:
			return

		if self._primaryTransport:
			if self._pretendAcked is None:
				start = None
			else:
				# In this case, avoid calling writeBoxes when there aren't any new boxes.
				# Sample:
				# Wrote boxes 0, 1 over T#1; T#2 connects and makes _pretendAcked = 1
				# queue is still _seqNumAt0 == 0, len(self.queue) == 2
				# This function is called;
				# (not 0 + 2 > 1 + 1), so return
				##print self.queue._seqNumAt0 + len(self.queue), self._pretendAcked + 1
				if not self.queue._seqNumAt0 + len(self.queue) > self._pretendAcked + 1:
					return
				start = max(self._pretendAcked + 1, self.queue._seqNumAt0)
			self._primaryTransport.writeBoxes(self.queue, start=start)


	def _fireNotifications(self):
		for d in self._notifications:
			d.callback(None)
		self._notifications = None


	def sendBoxes(self, boxes):
		"""
		Send C{boxes} boxes to the peer.

		@param boxes: a sequence of boxes
		@type boxes: a sequence

		"""
		if self.disconnected:
			raise RuntimeError("Cannot sendBoxes on disconnected Stream %r" % (self,))

		if not boxes:
			return

		# We don't need to self._producer.pauseProducing() if queue is too big here,
		# because:
		#     1) active S2C transport are responsible for pausing if there is TCP pressure
		#     2) if there is no active S2C transport, we already paused it
		self.queue.extend(boxes)
		self._tryToSend()


	# Called by the application only. Internal Minerva code uses _internalReset.
	# This assumes _protocol has been instantiated.
	def reset(self, reasonString):
		"""
		Reset (disconnect) with reason C{reasonString}.
		"""
		if self.disconnected:
			raise RuntimeError("Cannot reset disconnected Stream %r" % (self,))
		self.disconnected = True
		# If no transports are connected, client will not get the reset frame. If client tries
		# to connect a transport to a dead stream, they will get a tk_stream_attach_failure.
		for t in self._transports.copy(): # Need to copy because size changes as transports call transportOffline
			t.writeReset(reasonString, applicationLevel=True)
		self._fireNotifications()
		# Call application code last, to mitigate disaster if it raises an exception.
		try:
			self._protocol.streamReset(WhoReset.server_app, reasonString)
		finally:
			del self._protocol


	# Called by transports.
	# This assumes _protocol has been instantiated.
	def resetFromClient(self, reasonString, applicationLevel):
		"""
		Private. Do not call this.

		Minerva transports call this when they get a reset frame from client.
		Transport still needs to call transportOffline after this.
		"""
		assert not self.disconnected
		self.disconnected = True
		for t in self._transports.copy(): # Need to copy because size changes as transports call transportOffline
			t.closeGently()
		self._fireNotifications()
		# Call application code last, to mitigate disaster if it raises an exception.
		try:
			self._protocol.streamReset(WhoReset.client_app if applicationLevel else WhoReset.client_minerva, reasonString)
		finally:
			del self._protocol


	# This assumes _protocol has been instantiated.
	def _internalReset(self, reasonString):
		assert not self.disconnected
		self.disconnected = True
		for t in self._transports.copy(): # Need to copy because size changes as transports call transportOffline
			t.writeReset(reasonString, applicationLevel=False)
		self._fireNotifications()
		# Call application code last, to mitigate disaster if it raises an exception.
		try:
			self._protocol.streamReset(WhoReset.server_minerva, reasonString)
		finally:
			del self._protocol


	def boxesReceived(self, transport, boxes, memorySizeOfBoxes):
		"""
		Private. Do not call this.

		Called by a transport to tell me that it has received boxes L{boxes}.
		"""
		self._incoming.give(boxes, memorySizeOfBoxes)
		items = self._incoming.getDeliverableItems()
		if items:
			self._protocol.boxesReceived(items)
		# We deliver the deliverable boxes before resetting the connection (if necessary),
		# just in case the client sent something useful.
		# Note: Underneath the boxesReceived call (above), someone may have reset the Stream!
		# This is why we check for `not self.disconnected`.
		if not self.disconnected and \
		(self._incoming.getUndeliveredCount() > self.maxUndeliveredBoxes or \
		self._incoming.getMaxConsumption() > self.maxUndeliveredBytes):
			self._internalReset(u'resources exhausted')


	def sackReceived(self, sackInfo):
		"""
		Private. Do not call this.
		
		Minerva transports call this when they get a sack frame from client.
		"""
		# No need to pretend any more, because we just got a likely-up-to-date sack from the client.
		# TODO: perhaps have a flag for the sack frame that lets client send a "outdated SACK"
		# that removes old frames in server's queue, but doesn't imply "I don't have anything else after this"
		wasPretending = self._pretendAcked
		self._pretendAcked = None

		self.queue.handleSACK(sackInfo)

		if wasPretending:
			# Try to send, because the SACK may have indicated that the client
			# lost boxes that were delivered to the older active S2C transport.
			self._tryToSend()


	def transportOnline(self, transport):
		"""
		Private. Do not call this.

		Called by faces to tell me that new transport C{transport} has connected.
		This is called even for very-short-term C2S HTTP transports.

		Caller is responsible for verifying that a transport should really be attached
		to this stream before calling L{transportOnline}. Usually this is done by
		authenticating based on data in the `hello' frame.
		"""
		self._transports.add(transport)
		self.virgin = False

		# This is done here, and not in _newPrimary, because client should be able
		# to upload boxes without ever having set up a primary transport.
		if not self._protocol:
			self._protocol = self._streamProtocolFactory.buildProtocol()
			self._protocol.streamStarted(self)
		# Remember streamStarted can do anything to us, including reset or sendBoxes.


	def transportOffline(self, transport):
		"""
		Private. Do not call this.

		Called by faces to tell me that new transport C{transport} has disconnected.
		"""
		try:
			self._transports.remove(transport)
		except KeyError:
			raise RuntimeError("Cannot take %r offline; it wasn't registered" % (transport,))
		if transport is self._primaryTransport:
			# Is this really needed? Why would a transport send signals after it is offline?
			self._unregisterProducerOnPrimary()
			self._primaryTransport = None

			# This line is not actually necessary, because even if _primaryPaused is left at True,
			# producers attached to Stream would be paused anyway when there is no primary
			# transport. We leave it in anyway for ease of debugging, and in case the code changes.
			self._primaryPaused = False

			if self._producer and self._streamingProducer:
				self._producer.pauseProducing()


	def _unregisterProducerOnPrimary(self):
		"""
		Keep in mind that this is called whenever you unregister a producer
		on Stream, too. self._primaryPaused does not change.
		"""
		if self._primaryHasProducer:
			self._primaryTransport.unregisterProducer()
			self._primaryHasProducer = False


	# Called when we have a new primary transport, or when a MinervaProtocol registers a producer with us (Stream)
	def _registerProducerOnPrimary(self):
		if not self._primaryHasProducer:
			self._primaryTransport.registerProducer(self, self._streamingProducer)
			self._primaryHasProducer = True


	def _newPrimary(self, transport):
		if self._primaryTransport: # If we already have a primary transport that hasn't detached
			self._unregisterProducerOnPrimary()
			# If old primary transport paused us, our producer was paused, and this pause state
			# is no longer relevant, so go back to resume.
			if self._primaryPaused and self._producer and self._streamingProducer:
				self._producer.resumeProducing()
			self._primaryPaused = False # TODO low-priority: can we make a test that fails if this is indented right once?
			self._primaryTransport.closeGently() # TODO: test that transport calls transportOffline right after this happens
		else:
			# There was no active S2C transport, so if we had a push
			# producer, it was paused, and we need to unpause it.
			if self._producer and self._streamingProducer:
				self._producer.resumeProducing()
			assert self._primaryPaused == False

		self._primaryTransport = transport
		if self._producer:
			self._registerProducerOnPrimary()


	def subscribeToBoxes(self, transport, succeedsTransport):
		"""
		Private. Do not call this.

		Transport C{transport} says it wants to start receiving boxes.

		If L{succeedsTransport} != None, temporarily assume that all boxes written to
		#<succeedsTransport> were SACKed.
		"""
		##print 'subscribeToBoxes', transport, succeedsTransport
		if \
		succeedsTransport is not None and \
		self._primaryTransport and \
		succeedsTransport == self._primaryTransport.transportNumber and \
		self._primaryTransport.lastBoxSent != -1:
			self._pretendAcked = self._primaryTransport.lastBoxSent
		self._newPrimary(transport)
		self._tryToSend()


	def getSACK(self):
		"""
		Private, but no side-effects.

		@return: the SACK information for C2S boxes.
		@rtype: list
		"""
		return self._incoming.getSACK()


	def serverShuttingDown(self):
		"""
		Private. Do not call this.

		Called by L{StreamTracker} to tell me that the server is shutting down.

		@return: a L{Deferred} that fires when it's okay to shut down,
			or a L{int}/L{float} that says in how many seconds it is okay to shut down.

		TODO: decide if serverShuttingDown should be both an application level
			and Minerva-level event? Should applications have to use their own
			serverShuttingDown?
		"""
		1/0


	# This API resembles L{twisted.web.server.Request.notifyFinish}
	def notifyFinish(self):
		"""
		Notify when finishing the request.

		@return: A deferred. The deferred's callback chain willl be fired when
		this Stream is finished -- always with a C{None} value.
		"""
		self._notifications.append(defer.Deferred())
		return self._notifications[-1]


	# This is a copy/paste from twisted.internet.interfaces.IConsumer with changes

	# called by MinervaProtocol instances or anyone else interested in the Stream

	# The only reason we have this is because not all MinervaProtocols will be L{IProducer}s
	# (some will be very simple). Why not just implement pause/resume/stopProducing
	# in BasicMinervaProtocol with ': pass' methods? Because the protocol wouldn't change
	# its behavior; this is bad, it is unholy to send data when you are paused.
	def registerProducer(self, producer, streaming):
		"""
		Register to receive data from a producer that creates S2C boxes.

		This sets this stream to be a consumer for producer C{producer}.
		When this stream runs out of data on a write() call, it will ask C{producer}
		to resumeProducing(). When the (active S2C transport)'s internal data buffer is
		filled, it will ask C{producer} to pauseProducing(). If the stream
		is ended, Stream calls C{producer}'s stopProducing() method.

		If C{streaming} is C{True}, C{producer} should provide the L{IPushProducer}
		interface. Otherwise, it is assumed that producer provides the
		L{IPullProducer} interface. In this case, C{producer} won't be asked
		to pauseProducing(), but it has to be careful to write() data only
		when its resumeProducing() method is called.
		"""
		if self._producer:
			raise RuntimeError("Cannot register producer %s, "
				"because producer %s was never unregistered." % (producer, self._producer))
		##if self.disconnected:
		##	producer.stopProducing()
		##	return

		self._producer = producer
		self._streamingProducer = streaming

		if self._streamingProducer and (self._primaryPaused or not self._primaryTransport):
			self._producer.pauseProducing()

		if self._primaryTransport:
			self._registerProducerOnPrimary()


	# called by MinervaProtocol instances or anyone else interested in the Stream
	def unregisterProducer(self):
		"""
		Stop consuming data from a producer, without disconnecting.
		"""
		self._producer = None
		if self._primaryTransport:
			self._unregisterProducerOnPrimary()


	# called ONLY by the primary transport in response to TCP pressure
	def pauseProducing(self):
		"""
		Private. Do not call this.

		We assume this is called only by the primary transport. Also, the pause
		status is no longer relevant after the primary transport detaches.
		"""
		self._primaryPaused = True
		if self._producer:
			self._producer.pauseProducing()


	# called ONLY by the primary transport in response to TCP pressure
	def resumeProducing(self):
		"""
		Private. Do not call this.

		We assume this is called only by the primary transport.
		"""
		self._primaryPaused = False
		if self._producer:
			self._producer.resumeProducing()



class NoSuchStream(Exception):
	pass



class StreamAlreadyExists(Exception):
	pass



class StreamTracker(object):
	"""
	I'm responsible for constructing and keeping track of L{Stream}s.

	You do not want to subclass this.
	"""
	stream = Stream

	__slots__  = '_reactor,_clock,_streamProtocolFactory,_streams,_observers,_preKey,_postKey'.split(',')

	def __init__(self, reactor, clock, streamProtocolFactory):
		self._reactor = reactor
		self._clock = clock
		self._streamProtocolFactory = streamProtocolFactory
		# We have to keep a map of streamId->Stream, otherwise there is no
		# way for a face to locate a Stream.
		self._streams = {}
		self._observers = set()
		self._reactor.addSystemEventTrigger('before', 'shutdown', self._disconnectAll)

		self._preKey = abstract.secureRandom(3)
		self._postKey = abstract.secureRandom(3)


	def _makeSafeKey(self, key):
		"""
		Because the client has full control of deciding the streamId, and StreamTracker's
		streamId -> Stream dictionary is persistent and impacts many users, an attacker
		could deny access to everyone by opening many Streams with streamIds that hash()
		to the same number. Our anti-ACA patch for Python does not help here.
		We use a key prefix and suffix that is unknown to the public to stop this attack.
		"""
		# TODO: maybe use salted md5 or salted sha1 to be safer
		return self._preKey + key + self._postKey


	def getStream(self, streamId):
		try:
			return self._streams[self._makeSafeKey(streamId)]
		except KeyError:
			raise NoSuchStream("I don't know about %r" % (streamId,))


	def buildStream(self, streamId):
		safeKey = self._makeSafeKey(streamId)
		if safeKey in self._streams:
			raise StreamAlreadyExists(
				"cannot make stream with id %r because it already exists" % (streamId,))

		s = self.stream(self._clock, streamId, self._streamProtocolFactory)
		# Do this first, in case an observer stupidly wants to use L{StreamTracker.getStream}.
		self._streams[safeKey] = s

		try:
			for o in self._observers.copy(): # copy() to avoid reentrant `unobserveStreams' disaster
				o.streamUp(s)
		except:
			# If an exception happened, at least we can clean up our part of the mess.
			del self._streams[safeKey]
			raise
		# If an exception happened in an observer, it bubbles up.
		# If an exception happened, we don't call streamDown(s) because we don't know which
		# observers really think the stream is "up" (the exception might have occurred "early")

		d = s.notifyFinish()
		d.addBoth(self._forgetStream, streamId)
		return s


	def _forgetStream(self, _ignoredNone, streamId):
		safeKey = self._makeSafeKey(streamId)
		stream = self._streams[safeKey]
		del self._streams[safeKey]

		# Do this after the `del' above in case some buggy observer raises an exception.
		for o in self._observers.copy(): # copy() to avoid reentrant `unobserveStreams' disaster
			o.streamDown(stream)

		# Last reference to the stream should be gone soon.


	def _disconnectAll(self):
		# TODO: block new connections - stop listening on the faces? reject their requests quickly?
		log.msg('in StreamTracker._disconnectAll; maybe you want to implement something')

#		while True:
#			try:
#				s = self._streams.pop()
#			except KeyError:
#				break
#
#			numOrD = s.serverShuttingDown()


	def observeStreams(self, obj):
		"""
		Notify L{obj} when any stream goes up or down. L{obj} continues
		receiving calls unless L{unobserveStreams} is called.

		@param obj: any object that implements L{IStreamNotificationReceiver}.

		@return: L{None}
		"""
		# poor man's zope.interface checker
		assert obj.streamUp.__call__, "obj needs a streamUp method"
		assert obj.streamDown.__call__, "obj needs a streamDown method"

		self._observers.add(obj)


	def unobserveStreams(self, obj):
		"""
		Stop notifying L{obj} when any stream goes up or down.

		@param obj: any object previously registered with L{observeStreams}.

		@raises: L{RuntimeError} if L{obj} was not registered.
		@return: L{None}
		"""
		try:
			self._observers.remove(obj)
		except KeyError:
			raise RuntimeError("%r was not observing" % (obj,))



# A MinervaTransport must have registerProducer and unregisterProducer because
# Stream calls those methods, but it doesn't actually need to be an IPushProducer/IPullProducer.
# It could, in theory, buffer all the information it gets without caring about TCP pressure at all.
class IMinervaTransport(ISimpleConsumer):

	lastBoxSent = Attribute(
		"Sequence number of the last box written to the socket/request, or -1 if no boxes ever written")


	def writeBoxes(queue, start):
		"""
		Write boxes in queue C{queue} to the peer.
		This never writes boxes that were already written to the peer.

		@param queue: an L{abstract.Queue}
		@param start: where to start in the queue, or C{None}
		@type start: L{int} or L{NoneType}
		"""


	def closeGently():
		"""
		Close this transport. Usually happens if the transport is no longer
		useful (due to HTTP limitations), or because a new active S2C
		transport has connected.
		"""


	def writeReset(reasonString, applicationLevel):
		"""
		Write out a reset frame on this transport, to indicate that server is
		resetting the Stream.

		@param reasonString: plain-English reason why the stream is resetting
		@type reasonString: unicode

		@param applicationLevel: is it an application-level reset?
		@type applicationLevel: bool

		The reset frame (incl. reasonString) are not guaranteed to arrive to the peer.
		reasonString is only sometimes useful for debugging.
		"""



def dumpToJson7Bit(data):
	return simplejson.dumps(data, separators=(',', ':'), allow_nan=False)




class InvalidHello(Exception):
	pass


##WAITING_FOR_AUTH, AUTHING, DYING, AUTH_OK = range(4)

# Acceptable protocol modes for SocketTransport to be in. Int32* are for Flash Socket.
UNKNOWN, POLICYFILE, INT32, INT32CRYPTO, WEBSOCKET, BENCODE, HTTP = range(7)

# TODO: We'll need to make sure it's impossible for an attacker to downgrade "int32+crypto"
# down to "int32"


class SocketTransport(protocol.Protocol):
	"""
	This is private. Use SocketFace, which will build this Protocol.

	This is a hybrid:
		Flash Socket
		Flash Socket policy server
	TODO: WebSocket, Flash Socket (encrypted), pass-through to HTTP
	"""
	implements(IMinervaTransport, IProtocol, IPushProducer, IPullProducer)

	request = None # no associated HTTP request

	MAX_LENGTH = 1024*1024
	noisy = True

	__slots__ = (
		'lastBoxSent,_lastStartParam,_mode,_initialBuffer,_gotHello,'
		'_terminating,_stream,_sackDirty,_paused,_producer,_streamingProducer').split(',')

	def __init__(self, reactor, clock, streamTracker, firewall, policyStringWithNull):
		self._reactor = reactor
		self._clock = clock
		self._streamTracker = streamTracker
		self._firewall = firewall
		self._policyStringWithNull = policyStringWithNull

		self.lastBoxSent = -1
		self._lastStartParam = 2**128
		self._mode = UNKNOWN
		self._initialBuffer = '' # To buffer data while determining the mode
		self._gotHello = self._terminating = self._sackDirty = self._paused = self._streamingProducer = False
		self._stream = self._producer = None


	def __repr__(self):
		return '<%s terminating=%r, stream=%r, paused=%r, lastBoxSent=%r>' % (
			self.__class__.__name__,
			self._terminating, self._stream, self._paused, self.lastBoxSent)


	def _encodeFrame(self, frameData):
		assert self._mode != UNKNOWN
		if self._mode in (BENCODE, INT32):
			return self._parser.encode(dumpToJson7Bit(frameData))
		elif self_mode == HTTP:
			return dumpToJson7Bit(frameData) + '\n'
		else:
			1/0


	def _goOffline(self):
		if self._stream:
			self._stream.transportOffline(self)
			self._stream = None


	def _closeWith(self, errorType, *args):
		assert not self._terminating
		# TODO: sack before closing
		invalidArgsFrameObj = [errorType]
		invalidArgsFrameObj.extend(args)
		toSend = ''
		toSend += self._encodeFrame(invalidArgsFrameObj)
		toSend += self._encodeFrame([Fn_you_close_it])
		self.transport.write(toSend)
		self._terminating = True
		self._goOffline()

		# TODO: set timer and close the connection ourselves in 5-10 seconds
		##self.transport.loseConnection()


	def writeBoxes(self, queue, start):
		"""
		@see L{IMinervaTransport.writeBoxes}
		"""
		##print;print;traceback.print_stack()

		# If the transport is terminating, it should have already called Stream.transportOffline(self) # TODO: actually make it so
		assert not self._terminating

		if not self._gotHello:
			# How did someone ask me to write boxes at this time? This should
			# never happen.
			raise RuntimeError("_gotHello=%r" % (self._gotHello,))

		# TODO: make sure tests explicitly test that pull producers work properly if a push producer
		# was registered, paused, and unregistered before.
		# TODO: decide if this check is really helping anyone
		if self._paused:
			if self.noisy:
				log.msg('I was asked to send another box from %r but I am paused right now.' % (queue,))
			return

		# See test_writeBoxesConnectionInterleavingSupport
		# Remember that None < any number
		if start < self._lastStartParam:
			self.lastBoxSent = -1
			self._lastStartParam = start

		# Even if there's a lot of stuff in the queue, try to write everything.
		if self._sackDirty: # re: _sackDirty, see comment at the end of _framesReceived
			self._sackDirty = False
			toSend = self._getSACKBytes()
		else:
			toSend = ''
		# we might want to send boxes frame instead of box sometimes? no?
		lastBox = self.lastBoxSent
		for seqNum, box in queue.iterItems(start=start):
			##print seqNum, box, lastBox
			if seqNum <= lastBox: # This might have to change to support SACK.
				continue
			if lastBox == -1 or lastBox + 1 != seqNum:
				toSend += self._encodeFrame([Fn_seqnum, seqNum])
			toSend += self._encodeFrame([Fn_box, box])
			lastBox = seqNum
		if len(toSend) > 1024 * 1024:
			log.msg('Caution: %r asked me to send a large amount of data (%d bytes)' % (self._stream, len(toSend)))

		self.transport.write(toSend)
		self.lastBoxSent = lastBox


	def _getSACKBytes(self):
		assert not self._terminating
		sackFrame = (Fn_sack,) + self._stream.getSACK()
		return self._encodeFrame(sackFrame)


	def _handleHelloFrame(self, frame):
		helloData = frame.contents[1]

		if not isinstance(helloData, dict):
			raise InvalidHello

		# credentialsData is always optional
		credentialsData = helloData['c'] if 'c' in helloData else {}

		if not isinstance(credentialsData, dict):
			raise InvalidHello

		# requestNewStream is always optional
		requestNewStream = helloData['w'] if 'w' in helloData else False

		if not isinstance(requestNewStream, bool):
			raise InvalidHello

		try:
			# any line below can raise KeyError; additional exceptions marked with 'e:'

			transportNumber = abstract.ensureNonNegIntLimit(helloData['n'], 2**64)
			protocolVersion = helloData['v']
			# -- no transportType
			# Rules for streamId: must be 20-30 inclusive bytes, must not contain characters > 127
			streamId = helloData['i']
			if not isinstance(streamId, str) or not 20 <= len(streamId) <= 30: # ,str is appropriate because of how simplejson returns str when possible
				raise InvalidHello
			# -- no numPaddingBytes
			maxReceiveBytes = abstract.ensureNonNegIntLimit(helloData['r'], 2**64) # e: ValueError, TypeError
			maxOpenTime = abstract.ensureNonNegIntLimit(helloData['m'], 2**64) # e: ValueError, TypeError
			# -- no readOnlyOnce
		except (KeyError, TypeError, ValueError):
			raise InvalidHello

		# Do not use protocolVersion < 2 ever because Python is very stupid about bool/int equivalence
		if protocolVersion != 2:
			raise InvalidHello

		self._protocolVersion = protocolVersion
		self.streamId = streamId
		self.credentialsData = credentialsData
		self.transportNumber = transportNumber
		self._maxReceiveBytes = maxReceiveBytes # TODO: actually implement. Or not?
		self._maxOpenTime = maxOpenTime # TODO: actually implement. Or not?

		# We get/build a Stream instance before the firewall checkTransport
		# because the firewall needs to know if we're working with a virgin
		# Stream or not. And there's no way to reliably know this before doing the buildStream/getStream stuff,
		# because 'requestNewStream=True' doesn't always imply that a new stream will
		# actually be created.

		if requestNewStream:
			try:
				stream = self._streamTracker.buildStream(streamId)
			except StreamAlreadyExists:
				stream = self._streamTracker.getStream(streamId)
		else:
			stream = self._streamTracker.getStream(streamId)

		d = self._firewall.checkTransport(self, stream)

		def cbAuthOkay(_):
			if self._terminating:
				return
			self._stream = stream # self._stream being set implies that were are authed, and that we called transportOnline
			self._stream.transportOnline(self)
			# Remember, a lot of stuff can happen underneath that transportOnline call
			# because it may construct a MinervaProtocol, which may even call reset.

		def cbAuthFailed(_):
			if self._terminating:
				return
			self._closeWith(Fn.tk_stream_attach_failure)

		d.addCallbacks(cbAuthOkay, cbAuthFailed)
		d.addErrback(log.err)


	def _framesReceived(self, frames):
		# TODO: don't call transport.write() more than once for a _framesReceived() call.
		# TODO: confirm that Twisted actually sends multiple TCP packets when .write() is called
		# under the same stack frame. exarkun says it doesn't.
		assert self._sackDirty is False
		for frameString in frames:
			assert isinstance(frameString, str)
			if self._terminating:
				break

			try:
				frameObj, position = decoders.strictDecoder.raw_decode(frameString)
				if position != len(frameString):
					return self._closeWith(Fn.tk_intraframe_corruption)
			except (simplejson.decoder.JSONDecodeError, decoders.ParseError):
				return self._closeWith(Fn.tk_intraframe_corruption)

			try:
				frame = Frame(frameObj)
			except BadFrame:
				return self._closeWith(Fn.tk_invalid_frame_type_or_arguments)

			# Below, we can assume that the frame has the minimum/maximum allowed number of
			# arguments for the frame type.

			frameType = frameObj[0]

			# We demand a 'hello' frame before any other type of frame
			if not self._gotHello and frameType != Fn_hello:
				return self._closeWith(Fn.tk_invalid_frame_type_or_arguments)


			if frameType == Fn_hello:
				# We only allow one 'hello' per connection
				if self._gotHello:
					return self._closeWith(Fn.tk_invalid_frame_type_or_arguments)
				self._gotHello = True
				try:
					self._handleHelloFrame(frame)
				except InvalidHello:
					return self._closeWith(Fn.tk_invalid_frame_type_or_arguments)
				except NoSuchStream:
					return self._closeWith(Fn.tk_stream_attach_failure)
			
			elif frameType == Fn_gimme_boxes:
				succeedsTransport = frameObj[1]
				if succeedsTransport is not None:
					try:
						succeedsTransport = abstract.ensureNonNegIntLimit(frameObj[1], 2**64)
					except (TypeError, ValueError):
						return self._closeWith(Fn.tk_invalid_frame_type_or_arguments)
				self._stream.subscribeToBoxes(self, succeedsTransport)

			elif frameType == Fn_you_close_it:
				# TODO: allow this for HTTP; finish the HTTP request
				return self._closeWith(Fn.tk_invalid_frame_type_or_arguments)

			elif frameType == Fn_boxes:
				seqNumStrToBoxDict = frameObj[1]
				memorySizeOfBoxes = len(frameString)
				boxes = []
				for seqNumStr, box in seqNumStrToBoxDict.iteritems():
					try:
					 	# This is probably enough to stop an ACA on 64-bit Python, but maybe worry about 32-bit Python too? 
						seqNum = abstract.ensureNonNegIntLimit(abstract.strToNonNeg(seqNumStr), 2**64)
					except ValueError:
						return self._closeWith(Fn.tk_invalid_frame_type_or_arguments)
					boxes.append((seqNum, box))
				self._sackDirty = True
				self._stream.boxesReceived(self, boxes, memorySizeOfBoxes)
				# Remember that a lot can happen underneath that boxesReceived call, including
				# a call to our own `reset` or `closeGently` or `writeBoxes`.

			elif frameType == Fn_box:
				1/0

			elif frameType == Fn_seqnum:
				1/0

			elif frameType == Fn_reset:
				reasonString, applicationLevel = frameObj[1:]
				if not isinstance(reasonString, basestring) or not isinstance(applicationLevel, bool):
					return self._closeWith(Fn.tk_invalid_frame_type_or_arguments)
				self._stream.resetFromClient(reasonString, applicationLevel)

			elif frameType == Fn_sack:
				ackNumber, sackList = frameObj[1:]
				try:
					abstract.ensureNonNegIntLimit(ackNumber, 2**64) # okay to ignore return value here
				except (TypeError, ValueError):
					return self._closeWith(Fn.tk_invalid_frame_type_or_arguments)

				if not isinstance(sackList, list):
					return self._closeWith(Fn.tk_invalid_frame_type_or_arguments)

				for obj in sackList:
					try:
						abstract.ensureNonNegIntLimit(obj, 2**64) # okay to ignore return value here
					except (TypeError, ValueError):
						return self._closeWith(Fn.tk_invalid_frame_type_or_arguments)

				try:
					self._stream.sackReceived((ackNumber, sackList))
				except abstract.InvalidSACK:
					return self._closeWith(Fn.tk_acked_unsent_boxes)

			elif frameType == Fn.start_timestamps:
				1/0

			elif frameType == Fn.stop_timestamps:
				1/0
				
			else:
				return self._closeWith(Fn.tk_invalid_frame_type_or_arguments)

		# The _sackDirty behavior in this class reduces the number of Fn.sack frames
		# that are written out, while making sure that Fn.sack frames are not "held up"
		# by boxes written out by the Stream. If Stream writes boxes during the
		# Stream.boxesReceived call, a SACK is sent before the box(es).
		if self._sackDirty and not self._terminating:
			self._sackDirty = False
			self.transport.write(self._getSACKBytes())


	def dataReceived(self, data):
		##print repr(data)
		if self._terminating:
			return

		# Before we can even speak "Minerva" and send frames, we need to determine
		# what mode the client wants us to speak in.
		if self._mode == UNKNOWN:
			self._initialBuffer += data

			if self._initialBuffer.startswith('<policy-file-request/>\x00'):
				self._mode = POLICYFILE
				del self._initialBuffer
				self.transport.write(self._policyStringWithNull)
				self._terminating = True

				# No need to loseConnection here, because Flash player will close it:
				# "The server must send a null byte to terminate a policy file and may then close
				#	the connection; if the server does not close the connection, the Flash Player will
				#	do so upon receiving the terminating null byte."
				#	http://www.adobe.com/devnet/flash/articles/fplayer_security_03.html

				# TODO: loseConnection in 5-10 seconds, if client doesn't

				return

			elif self._initialBuffer.startswith('<bencode/>\n'):
				self._mode = BENCODE
				frameData = self._initialBuffer[len('<bencode/>\n'):]
				del self._initialBuffer
				self._parser = decoders.BencodeStringDecoder()
				self._parser.MAX_LENGTH = self.MAX_LENGTH

			elif self._initialBuffer.startswith('<int32/>\n'):
				self._mode = INT32
				frameData = self._initialBuffer[len('<int32/>\n'):]
				del self._initialBuffer
				self._parser = decoders.Int32StringDecoder()
				self._parser.MAX_LENGTH = self.MAX_LENGTH

			# TODO: <int32-zlib/> with <x/> alias
			# TODO: if we support compression, make sure people can't zlib-bomb us with exploding strings:
			#	use the zlib Decompression Object and decompress(string[, max_length]), then check unconsumed_tail.
			#	Note: there's probably one excess memory-copy with the unconsumed_tail stuff, but that's okay.

			elif len(self._initialBuffer) >= 512: # TODO: increase or lower this, depending on how much we really need.
				# Terminating, but we can't even send any type of frame.
				self._terminating = True
				# RST them instead of FIN, because they don't look like a well-behaving client anyway.
				self.transport.abortConnection()
				return

			else:
				return
		else:
			frameData = data

		if self._mode in (BENCODE, INT32):
			out, code = self._parser.getNewFrames(frameData)
			if code == decoders.OK:
				self._framesReceived(out)
			elif code in (decoders.TOO_LONG, decoders.FRAME_CORRUPTION):
				self._closeWith(Fn.tk_frame_corruption)
			elif code == decoders.INTRAFRAME_CORRUPTION:
				self._closeWith(Fn.tk_intraframe_corruption)
			else:
				raise RuntimeError("Got unknown code from parser %r: %r" % (self._parser, code))
		else: # Don't need to handle HTTP here because HttpFace calls _framesReceived
			1/0


	def closeGently(self):
		"""
		@see L{IMinervaTransport.closeGently}
		"""
		assert not self._terminating

		if self._sackDirty:
			self._sackDirty = False
			toSend = self._getSACKBytes()
		else:
			toSend = ''

		toSend += self._encodeFrame([Fn_you_close_it])

		self.transport.write(toSend)
		self._terminating = True
		self._goOffline()


	def writeReset(self, reasonString, applicationLevel):
		"""
		@see L{IMinervaTransport.writeReset}
		"""
		assert not self._terminating

		if self._sackDirty:
			self._sackDirty = False
			toSend = self._getSACKBytes()
		else:
			toSend = ''

		toSend += self._encodeFrame([Fn_reset, reasonString, applicationLevel])
		toSend += self._encodeFrame([Fn_you_close_it])
		self.transport.write(toSend)
		self._terminating = True
		self._goOffline()


	# called by Stream instances
	def registerProducer(self, producer, streaming):
		if self._producer:
			raise RuntimeError("Cannot register producer %s, "
				"because producer %s was never unregistered." % (producer, self._producer))

		# no 'disconnected' check?

		self._producer = producer
		self._streamingProducer = streaming
		if streaming and self._paused: # We may have been paused before a producer was registered
			producer.pauseProducing()

		self.transport.registerProducer(self, streaming)


	# called by Stream instances
	def unregisterProducer(self):
		"""
		Stop consuming data from a producer.
		"""
		self._producer = None
		self.transport.unregisterProducer()


	# called by Twisted. We trust Twisted to only call this if we registered a push producer with self.transport
	def pauseProducing(self):
		self._paused = True
		if self._producer:
			self._producer.pauseProducing()


	# called by Twisted.
	def resumeProducing(self):
		self._paused = False
		if self._producer:
			self._producer.resumeProducing()


	# called by Twisted.
	def stopProducing(self):
		# Our connectionLost logic eventually deals with the producers,
		# so we don't need to do anything here.
		pass


	def connectionLost(self, reason):
		if self.noisy:
			log.msg('Connection lost for %r reason %r' % (self, reason))
		# It might already be terminating, but often not.
		self._terminating = True
		self._goOffline()


	def connectionMade(self):
		self.transport.setTcpNoDelay(True)
		if self.noisy:
			log.msg('Connection made for %r' % (self,))



class SocketFace(protocol.ServerFactory):
	implements(IProtocolFactory)

	protocol = SocketTransport

	def __init__(self, reactor, clock, streamTracker, firewall, policyString=None):
		"""
		@param reactor: must provide... TODO WHAT?
		@param clock: must provide L{IReactorTime}
		@param streamTracker: The StreamTracker that will know about all active Streams.
		@type streamTracker: L{StreamTracker}
		@param firewall: The transport firewall to use. Must provide L{website.ITransportFirewall}
		@param policyString: a Flash/Silverlight policy file as a string,
			sent in response to <policy-file-request/>C{NULL}.
		@type policyString: C{str} or C{NoneType}
		"""
		self._reactor = reactor
		self._clock = clock
		self._streamTracker = streamTracker
		self._firewall = firewall
		self.setPolicyString(policyString)


	def setPolicyString(self, policyString):
		"""
		Set the Flash/Silverlight socket policy to C{policyString}. Existing open connections
		will serve the old policy (though this is of little consequence).

		@param policyString: a Flash/Silverlight policy file as a string,
			sent in response to <policy-file-request/>C{NULL}.
		@type policyString: C{str} or C{NoneType}
		"""
		if policyString:
			if isinstance(policyString, unicode):
				raise TypeError("policyString cannot be a unicode object")
			if '\x00' in policyString:
				# because NULL is used to indicate end-of-policy file
				raise ValueError("policyString cannot contain NULL byte")
			self._policyStringWithNull = policyString + '\x00'
		else:
			# TODO: test that Flash Player actually closes connection when it sees just NULL
			self._policyStringWithNull = '\x00'


	def buildProtocol(self, addr):
		p = self.protocol(self._reactor, self._clock, self._streamTracker, self._firewall, self._policyStringWithNull)
		p.factory = self
		return p



class HttpFace(resource.Resource):
	isLeaf = True

	def __init__(self, clock, streamTracker, firewall):
		resource.Resource.__init__(self)
		self._clock = clock
		self._streamTracker = streamTracker
		self._firewall = firewall


	def render_GET(self, request):
		1/0


	def render_POST(self, request):
		result = []
		def callback(docs):
			result[0] = docs

		body = request.content.read()
		# Proxies *might* strip whitespace around the request body, so add a newline if necessary.
		if body and body[-1] != '\n':
			body += "\n"

		if '\r\n' in body:
			log.msg("Unusual: found a CRLF in POST body for %r from %r" % (request, request.client))

		decoder = decoders.BencodeStringDecoder()
		decoder.manyDataCallback = callback
		out, code = decoder.getNewFrames(body)
		if code == decoders.OK:
			queuedFrame = None
		elif code in (decoders.TOO_LONG, decoders.FRAME_CORRUPTION):
			queuedFrame = [Fn.tk_frame_corruption]
		elif code == decoders.INTRAFRAME_CORRUPTION:
			queuedFrame = [Fn.tk_intraframe_corruption]

		headers = request.responseHeaders._rawHeaders

		# Headers taken from the ones gmail sends
		headers['cache-control'] = ['no-cache, no-store, max-age=0, must-revalidate']
		headers['pragma'] = ['no-cache']
		headers['expires'] = ['Fri, 01 Jan 1990 00:00:00 GMT']

		# http://code.google.com/p/doctype/wiki/ArticleScriptInclusion
		request.write('for(;;);\n')


from pypycpyo import optimizer
optimizer.bind_all_many(vars(), _postImportVars)
