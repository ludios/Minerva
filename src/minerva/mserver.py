"""
The core of Minerva server.

See minerva.minerva_site for an idea of how to use the classes below,
especially `makeMinervaAndHttp` and `DemoProtocol`.

See minerva.test_mserver for the tests.
"""

import sys
import re
import time
import operator
from functools import partial

from zope.interface import Attribute, implements

from twisted.python import log
from twisted.python.filepath import FilePath
from twisted.internet import protocol, defer
from twisted.internet.interfaces import (
	IPushProducer, IPullProducer, IProtocol, IProtocolFactory)
from twisted.internet.task import LoopingCall
from twisted.web.server import NOT_DONE_YET

from strfrag import StringFragment
from securetypes import securedict

from webmagic.untwist import BetterResource, BetterFile, setNoCacheNoStoreHeaders
from webmagic.pathmanip import getCacheBrokenHref
from webmagic.filecache import FileCache

from minerva import decoders
from minerva.objcheck import strToNonNegLimit
from minerva.window import SACK, Queue, Incoming
from minerva.qan import QANHelper, qanFrameToString, stringToQANFrame
from minerva.mutils import htmldumps
from minerva.interfaces import IConsumerWithoutWrite, IStringProtocol, IStringFactory
from minerva.frames import (
	HelloFrame, StringFrame, SeqNumFrame, SackFrame, StreamStatusFrame,
	StreamCreatedFrame, YouCloseItFrame, ResetFrame, CommentFrame,
	TransportKillFrame, InvalidFrame, decodeFrameFromClient,
	isRestrictedString)

try:
	from brequire import requireFile, requireFiles
except ImportError:
	requireFile = requireFiles = lambda _: None

# Make globals that refbinder can optimize away
tk_stream_attach_failure = TransportKillFrame.stream_attach_failure
tk_acked_unsent_strings = TransportKillFrame.acked_unsent_strings
tk_invalid_frame_type_or_arguments = TransportKillFrame.invalid_frame_type_or_arguments
tk_frame_corruption = TransportKillFrame.frame_corruption
tk_rwin_overflow = TransportKillFrame.rwin_overflow

_postImportVars = vars().keys()


def _callStringsOrStringReceived(proto, strings):
	stringsReceived = getattr(proto, 'stringsReceived', None)
	if stringsReceived and callable(stringsReceived):
		stringsReceived(strings)
	else:
		for s in strings:
			proto.stringReceived(str(s))


def _cancelDc(obj, attr):
	dc = getattr(obj, attr)
	if dc is not None:
		if dc.active():
			dc.cancel()
		setattr(obj, attr, None)


class UnknownSubprotocol(Exception):
	pass



class SubprotocolProtocol(object):
	"""
	An implementation of L{IStringProtocol} that creates and proxies
	strings to a subprotocol after a "subprotocol:..." string is received.
	"""
	implements(IStringProtocol)
	__slots__ = ('stream', 'factory', '_clock', '_reset', '_childProtocol',
		'_stringsReceived')

	def __init__(self, clock):
		self._clock = clock
		self._reset = False
		self._childProtocol = None
		self.stream = None
		self._stringsReceived = 0


	def _createSubprotocol(self, name):
		subfactory = self.factory.getSubfactory(name)
		if subfactory is None:
			raise UnknownSubprotocol("%r" % (name,))
		self._childProtocol = subfactory.buildProtocol()
		self._childProtocol.streamStarted(self.stream)


	def streamStarted(self, stream):
		self.stream = stream


	def stringsReceived(self, strings):
		##print "stringsReceived", strings

		if self._childProtocol is not None:
			self._stringsReceived += len(strings)
			_callStringsOrStringReceived(self._childProtocol, strings)
			return

		for s in strings:
			s = str(s) # StringFragment -> str
			received = self._stringsReceived
			self._stringsReceived += 1
			if received == 0 and s.startswith('subprotocol:'):
				_, subprotocolName = s.split(':', 1)
				try:
					self._createSubprotocol(subprotocolName)
				except UnknownSubprotocol:
					self.stream.reset("unknown subprotocol")
			elif self._childProtocol is not None:
				_callStringsOrStringReceived(self._childProtocol, [s])
			else:
				self.stream.reset(
					"no subprotocol; send a subprotocol:... string first")


	def streamReset(self, reasonString, applicationLevel):
		self._reset = True
		del self.stream
		log.msg("Stream reset: %r, %r" % (reasonString, applicationLevel))
		if self._childProtocol:
			self._childProtocol.streamReset(reasonString, applicationLevel)



class SubprotocolFactory(object):
	"""
	An implementation of L{IStringFactory} that creates a protocol that
	proxies strings to a subprotocol after a "subprotocol:..." string is received.
	"""
	implements(IStringFactory)
	__slots__ = ('_clock', '_subfactories')

	protocol = SubprotocolProtocol

	def __init__(self, clock, subfactories):
		"""
		C{clock} is an L{IReactorTime} provider.
		C{subfactories} is a dict of subprotocol name (str) ->
			an L{IStringFactory} provider.
		"""
		self._clock = clock
		self._subfactories = subfactories


	def getSubfactory(self, name):
		return self._subfactories.get(name, None)


	def buildProtocol(self):
		stream = self.protocol(self._clock)
		stream.factory = self
		return stream



class QANProtocolWrapper(object):
	"""
	This is an L{IStringProtocol} that makes your L{IQANProtocol} work.
	See L{IQANProtocol}.
	"""
	implements(IStringProtocol)

	def __init__(self, qanProtocol, validateBodies=True):
		"""
		@param qanProtocol: An object that implements L{IQANProtocol}.
		@param validateBodies: Validate locally-created bodies of questions
			and answers?  Default C{True}.  Set to C{False} if you're
			sure your application works correctly.
		"""
		self.qanProtocol = qanProtocol
		self._validateBodies = validateBodies


	def _logError(self, message, failure):
		log.msg(message)
		log.err(failure)


	def _sendQANFrame(self, qanFrame):
		self.stream.sendString(qanFrameToString(qanFrame), self._validateBodies)


	def _fatalError(self, reason):
		self.stream.reset("QANHelper said: %s" % (reason,))


	def streamStarted(self, stream):
		self.stream = stream
		self.qanHelper = QANHelper(
			self.qanProtocol.bodyReceived,
			self._logError,
			self._sendQANFrame,
			self._fatalError)
		self.qanProtocol.streamStarted(self.stream, self.qanHelper)


	def streamReset(self, reasonString, applicationLevel):
		self.qanHelper.failAll("Stream reset "
			"applicationLevel=%r, reason: %s" % (applicationLevel, reasonString))
		self.qanProtocol.streamReset(reasonString, applicationLevel)


	def stringReceived(self, s):
		try:
			qanFrame = stringToQANFrame(s)
		except InvalidQANFrame:
			self.stream.reset("Bad QAN frame.  Did peer send a non-QAN string?")
		else:
			self.qanHelper.handleQANFrame(qanFrame)



# server attrs: transportNumber, isPrimary, streamingFromPeer, streamingToPeer, host, requestHeaders
# client attrs: transportNumber, isPrimary, streamingFromPeer, streamingToPeer

class TransportInfo(tuple):
	"""
	Contains information about the transport.  Passed to user's C{transportCreated}
	and C{transportDestroyed} methods.

	Do not index or slice this object (its tuple-ness is an implementation detail);
	use the named properties only.
	"""
	__slots__ = ()
	_MARKER = object()

	transportNumber = property(operator.itemgetter(1))
	isPrimary = property(operator.itemgetter(2))
	streamingFromPeer = property(operator.itemgetter(3))
	streamingToPeer = property(operator.itemgetter(4))
	host = property(operator.itemgetter(5))
	requestHeaders = property(operator.itemgetter(6))

	def __new__(cls, transportNumber, isPrimary, streamingFromPeer, streamingToPeer, host, requestHeaders):
		return tuple.__new__(cls, (cls._MARKER,
			transportNumber, isPrimary, streamingFromPeer, streamingToPeer, host, requestHeaders))


	def __repr__(self):
		return ('%s(transportNumber=%r, isPrimary=%r, streamingFromPeer=%r, streamingToPeer='
			  '%r, host=%r, requestHeaders=%r)') % (
		self.__class__.__name__, self[1], self[2], self[3], self[4], self[5], self[6])



# Note: there is no factory for customizing the construction of
# L{ServerStream}s, just like there is no factory for customizing the
# construction of L{twisted.internet.tcp.Server}s in Twisted.
class ServerStream(object):
	"""
	The server-side representation of a Minerva stream.

	ServerStream is sort-of analogous to L{twisted.internet.tcp.Connection}.
	ServerStream can span many TCP connections/HTTP requests.

	The (incomplete) producer/consumer code here is designed to deal with
	TCP bandwidth pressure (and "lack of any S2C transport" pressure).
	It does not help with any kind of application-level pressure.
	Applications that want high-volume streaming should implement an
	application-level producer/consumer system.
	"""
	# Don't implement IPushProducer or IPullProducer because we don't
	# expect stopProducing.
	implements(IConsumerWithoutWrite)

	maxUndeliveredStrings = 50 # strings
	maxUndeliveredBytes = 1 * 1024 * 1024 # bytes

	__slots__ = (
		'_clock', 'streamId', '_streamProtocolFactory', '_protocol',
		'_primaryTransport', '_notifications', '_transports', '_sendSoonDc',
		'disconnected', 'queue', '_incoming', '_pretendAcked', '_producer',
		'_streamingProducer', '_primaryHasProducer', '_primaryPaused',
		'lastSackSeenByServer', 'lastReceived', 'maxIdleTime')

	def __init__(self, clock, streamId, streamProtocolFactory):
		self._clock = clock
		self.streamId = streamId
		self._streamProtocolFactory = streamProtocolFactory

		self._protocol = None
		self._primaryTransport = None
		self._pretendAcked = None
		self._producer = None

		self.disconnected = False
		self._streamingProducer = False
		self._primaryHasProducer = False
		self._primaryPaused = False
		# _primaryPaused: Does the primary transport think it is paused?
		# Or if no primary transport, False.

		self._notifications = []
		self._transports = set()

		self.queue = Queue()
		self._incoming = Incoming()
		self.lastSackSeenByServer = SACK(-1, ())
		self.lastReceived = clock.seconds()
		self._sendSoonDc = None
		# If no transports and nothing received in this many seconds,
		# reset the stream.
		# This value needs to be somewhat forgiving, to allow for bad
		# connections.  You can change this; just make your protocol
		# set this attribute to a higher number.  Consider being even more
		# forgiving if you have high probability of getting some type of
		# disconnect string on page unload.
		self.maxIdleTime = 120 # seconds


	def __repr__(self):
		return ('<%s streamId=%r, queue.getQueuedCount()=%d, disconnected=%r>' % (
			self.__class__.__name__,
			self.streamId, self.queue.getQueuedCount(), self.disconnected))


	def _tryToSend(self):
		_cancelDc(self, '_sendSoonDc')

		##print '_tryToSend', self, self._primaryTransport, self.queue
		if self.queue.getQueuedCount() == 0:
			return

		if self._primaryTransport:
			start = None if self._pretendAcked is None else self._pretendAcked + 1
			# Note: writeStrings may be called even if there's nothing
			# in the queue to write.  See Minerva git history before 2010-05-23
			# if you're interested in the crazy logic that was here before, to
			# avoid calling writeStrings when not necessary.
			self._primaryTransport.writeStrings(self.queue, start)


	def _tryToSendSoon(self):
		if self._sendSoonDc is None:
			self._sendSoonDc = self._clock.callLater(
				0.001, self._tryToSend)


	def _fireNotifications(self):
		for d in self._notifications:
			d.callback(None)
		self._notifications = None


	def sendString(self, string, validate=True):
		"""
		Send string C{string} to the peer.  String MUST contain only
		bytes in inclusive range 0x20 (SPACE) - 0x7E (~).  String is always
		queued for sending "very soon", so multiple calls will not lead to
		redundant network activity.  (This is especially important for
		long-polling transports, which close right after sending.)

		@param string: a restricted string
		@type string: C{str}

		@param validate: Raise C{TypeError} or C{ValueError} if string is
			not a C{str} and restricted string?  Default C{True}.  Set
			this to C{False} for a slight speedup.
		@type validate: C{bool}
		"""
		if validate:
			if not isinstance(string, str):
				raise TypeError("not a str: %r" % (string,))
			if not isRestrictedString(string):
				raise ValueError("String %r contains illegal characters.  "
					"Only 0x20 (SPACE) - 0x7E (~) is allowed.  "
					"Consider using JSON or Base64 encoding." % (string,))

		if self.disconnected:
			raise RuntimeError("Cannot sendString on disconnected %r" % (self,))

		# We don't need to self._producer.pauseProducing() if queue is too
		# big here, because:
		# 1)	Active S2C transport are responsible for pausing if there
		# 		is TCP pressure.
		# 2)	If there is no active S2C transport, we already paused it.
		# TODO: actually implement flow control if Queue is too big, since
		# clients can resource-exhaust by never sending Minerva ACKs.
		self.queue.append(string)
		self._tryToSendSoon()


	def _finishReset(self, reasonString, applicationLevel):
		self._fireNotifications()
		try:
			self._protocol.streamReset(reasonString, applicationLevel)
		except Exception:
			log.msg("streamReset raised uncaught exception")
			log.err()
		finally:
			del self._protocol


	# Called by the application only.  Internal Minerva code uses _internalReset.
	# This assumes _protocol has been instantiated.
	def reset(self, reasonString):
		"""
		Reset (disconnect) the stream with reason C{reasonString}.
		Any strings queued for sending will never be sent.

		Implementation details: This writes a reset frame once over all open
		transports, and because there might be no transport, the client may
		never actually receive a ResetFrame.  If this happens, the client may
		soon try to connect to a nonexistent ServerStream, at which point
		Minerva server will send a C{tk_stream_attach_failure}.
		"""
		if self.disconnected:
			raise RuntimeError("Cannot reset disconnected ServerStream %r" % (self,))
		_cancelDc(self, '_sendSoonDc')
		self.disconnected = True
		# .copy() because _transports shrinks as transports call
		# ServerStream.transportOffline
		for t in self._transports.copy():
			t.writeReset(reasonString, applicationLevel=True)
		self._finishReset(reasonString, True)


	# Called by transports.
	# This assumes _protocol has been instantiated.
	def resetFromPeer(self, reasonString, applicationLevel):
		"""
		Private.  Do not call this.

		ServerTransport calls this when it gets a reset frame from client.
		ServerTransport still needs to call transportOffline after this.
		"""
		if self.disconnected:
			return
		_cancelDc(self, '_sendSoonDc')
		self.disconnected = True
		# .copy() because _transports shrinks as transports call
		# ServerStream.transportOffline
		for t in self._transports.copy():
			t.closeGently()
		self._finishReset(reasonString, applicationLevel)


	# This assumes _protocol has been instantiated.
	def _internalReset(self, reasonString):
		"""
		Called by ServerStream if it has given up on the stream.  This sends
		ResetFrame to any open transports.
		"""
		if self.disconnected:
			return
		_cancelDc(self, '_sendSoonDc')
		self.disconnected = True
		# .copy() because _transports shrinks as transports call
		# ServerStream.transportOffline
		for t in self._transports.copy():
			t.writeReset(reasonString, False)
		self._finishReset(reasonString, False)


	def timedOut(self):
		self._internalReset("no activity from peer")


	def stringsReceived(self, transport, pairs):
		"""
		Private.  Do not call this.

		Called by a transport to tell me that it has received *already sorted*
		(seqNum, string) L{pairs}.
		"""
		assert transport in self._transports, self._transports

		if self.disconnected:
			return

		items, hitLimit = self._incoming.give(
			pairs, self.maxUndeliveredStrings, self.maxUndeliveredBytes)
		if items:
			try:
				_callStringsOrStringReceived(self._protocol, items)
			except Exception:
				log.msg("stringReceived raised uncaught exception")
				log.err()
		# We deliver the deliverable strings even if the receive window is overflowing,
		# just in case the peer sent something useful.
		# Note: Underneath the stringsReceived call (above), someone may have
		# reset the ServerStream!  This is why we check for `not self.disconnected`.
		if hitLimit and not self.disconnected:
			# Minerva used to do an _internalReset here, but now it kills the transport.
			transport.causedRwinOverflow()


	def sackReceived(self, sack):
		"""
		Private.  Do not call this.

		Minerva transports call this when they get a HelloFrame.sack
		or SackFrame from client.  C{sack} is a L{window.SACK}.

		Returns C{True} if SACK was bad, C{False} otherwise.
		"""
		# No need to pretend any more, because we just got a
		# likely-up-to-date SACK from the client.
		wasPretending = self._pretendAcked
		self._pretendAcked = None

		self.lastSackSeenByServer = sack

		if self.queue.handleSACK(sack):
			return True

		if wasPretending is not None:
			# Try to send, because the SACK may have indicated that the client
			# lost strings that were delivered to the older active S2C transport.
			self._tryToSend()

		return False


	def transportOnline(self, transport, wantsStrings, succeedsTransport):
		"""
		Private.  Do not call this.

		Called by L{ServerTransport} to tell me that new transport
		C{transport} has connected.  This is called even for very-short-term
		C2S HTTP transports.

		If L{wantsStrings} is truthy, this transport wants to receive strings.

		If L{succeedsTransport} != None, temporarily assume that all strings
		written to #<succeedsTransport> were SACKed.
		"""
		self._transports.add(transport)

		# This is done here, and not in _newPrimary, because client should be able
		# to upload strings without ever having set up a primary transport.
		if not self._protocol:
			self._protocol = self._streamProtocolFactory.buildProtocol()
			try:
				self._protocol.streamStarted(self)
				# Remember: streamStarted can do anything to us,
				# including reset or sendString.
			except Exception:
				log.msg("streamStarted raised uncaught exception; resetting stream")
				log.err()
				self._internalReset("streamStarted raised uncaught exception")
				return
		if self.disconnected:
			return

		# streamStarted is called before transportCreated, despite the fact that
		# the transport led to stream creation, for two reasons:
		# 1) to present a nicer abstraction to the user, where streamStarted is always
		# called first.
		# 2) to match the behavior on the client side, where streamStarted is always
		# called first, due to .start() leading directly to streamStarted.

		transportCreated = getattr(self._protocol, 'transportCreated', None)
		if transportCreated is not None:
			try:
				self._protocol.transportCreated(transport.getInfo())
				# Remember: transportCreated can do anything to us,
				# including reset or sendString.
			except Exception:
				log.msg("transportCreated raised uncaught exception")
				log.err()
		if self.disconnected:
			return

		# TODO: do we really need _primaryTransport to still be connected?
		# Can't we just remember what its transportNumber and ourSeqNum were?
		# That way, a transport can succeed the older even if it was disconnected
		# in the meantime.
		if wantsStrings:
			if \
			succeedsTransport is not None and \
			self._primaryTransport and \
			succeedsTransport == self._primaryTransport.transportNumber and \
			self._primaryTransport.ourSeqNum != -1:
				self._pretendAcked = self._primaryTransport.ourSeqNum
			self._newPrimary(transport)
			self._tryToSend()


	def transportOffline(self, transport):
		"""
		Private.  Do not call this.

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

			# This line is not actually necessary, because even if
			# _primaryPaused is left at True, producers attached to
			# ServerStream would be paused anyway when there is no primary
			# transport.  We leave it in anyway for ease of debugging,
			# and in case the code changes.
			self._primaryPaused = False

			if self._producer and self._streamingProducer:
				self._producer.pauseProducing()

		# Note: protocol may not receive a `transportDestroyed` event for transports
		# connected during the stream reset.
		if not self.disconnected:
			transportDestroyed = getattr(self._protocol, 'transportDestroyed', None)
			if transportDestroyed is not None:
				try:
					self._protocol.transportDestroyed(transport.getInfo())
				# Remember: transportDestroyed can do anything to us,
				# including reset or sendString.
				except Exception:
					log.msg("transportDestroyed raised uncaught exception")
					log.err()


	def _unregisterProducerOnPrimary(self):
		"""
		Keep in mind that this is called whenever you unregister a producer
		on ServerStream, too.  self._primaryPaused does not change.
		"""
		if self._primaryHasProducer:
			self._primaryTransport.unregisterProducer()
			self._primaryHasProducer = False


	# Called when we have a new primary transport, or when a
	# IStringProtocol registers a producer with us (ServerStream).
	def _registerProducerOnPrimary(self):
		if not self._primaryHasProducer:
			self._primaryTransport.registerProducer(self, self._streamingProducer)
			self._primaryHasProducer = True


	def _newPrimary(self, transport):
		# If we already have a primary transport that hasn't detached:
		if self._primaryTransport:
			self._unregisterProducerOnPrimary()
			# If old primary transport paused us, our producer was paused, and this pause state
			# is no longer relevant, so go back to resume.
			if self._primaryPaused and self._producer and self._streamingProducer:
				self._producer.resumeProducing()
			self._primaryPaused = False
			# TODO: test that transport calls transportOffline right after this happens.
			self._primaryTransport.closeGently()
		else:
			# There was no active S2C transport, so if we had a push
			# producer, it was paused, and we need to unpause it.
			if self._producer and self._streamingProducer:
				self._producer.resumeProducing()
			assert self._primaryPaused == False

		self._primaryTransport = transport
		if self._producer:
			self._registerProducerOnPrimary()


	def getSACK(self):
		"""
		Private.  Do not call this.

		@return: the SACK information for C2S strings.
		@rtype: list
		"""
		return self._incoming.getSACK()


	# This API resembles L{twisted.web.server.Request.notifyFinish}
	def notifyFinish(self):
		"""
		Notify when finishing the request.

		@return: A deferred.  The deferred's callback chain will be fired when
		this ServerStream is finished -- always with a C{None} value.
		"""
		self._notifications.append(defer.Deferred())
		return self._notifications[-1]


	# This is a copy/paste from twisted.internet.interfaces.IConsumer with changes.

	# Called by IStringProtocol instances or anyone else interested in the
	# ServerStream.

	# The only reason we have this is because not all MinervaProtocols will
	# be L{IProducer}s (some will be very simple).
	def registerProducer(self, producer, streaming):
		"""
		Register to receive data from a producer that creates S2C strings.

		This sets this stream to be a consumer for producer C{producer}.
		When this stream runs out of data on a write() call, it will ask
		C{producer} to resumeProducing().  When the (active S2C transport)'s
		internal data buffer is filled, it will ask C{producer} to
		pauseProducing().  If the stream is ended, ServerStream calls
		C{producer}'s stopProducing() method.

		If C{streaming} is C{True}, C{producer} should provide the
		L{IPushProducer} interface.  Otherwise, it is assumed that producer
		provides the L{IPullProducer} interface.  In this case, C{producer}
		won't be asked to pauseProducing(), but it has to be careful to
		write() data only when its resumeProducing() method is called.
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


	# called by IStringProtocol instances or anyone else interested in the
	# ServerStream
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
		Private.  Do not call this.

		We assume this is called only by the primary transport.  Also, the pause
		status is no longer relevant after the primary transport detaches.
		"""
		self._primaryPaused = True
		if self._producer:
			self._producer.pauseProducing()


	# called ONLY by the primary transport in response to TCP pressure
	def resumeProducing(self):
		"""
		Private.  Do not call this.

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
	L{StreamTracker} constructs and keeps track of L{ServerStream}s.
	This is needed to get a reference to the right L{ServerStream} based on
	the stream ID sent by the client.

	L{StreamTracker} also disconnects inactive streams.

	You do not want to subclass this.
	"""
	__slots__  = (
		'_clock', '_streamProtocolFactory', '_inactiveCheckInterval',
		'_streams', '_idleKiller')

	stream = ServerStream

	def __init__(self, clock, streamProtocolFactory, inactiveCheckInterval=60):
		"""
		C{clock} is an L{IReactorTime} provider.
		C{streamProtocolFactory} is an L{IStringFactory} provider.
		C{inactiveCheckInterval} is how many seconds between a check that
			disconnect inactive Streams, or None, or no check is desired.  (With
			no check, you'll need to call C{.disconnectInactive()} yourself.)
		"""
		self._clock = clock
		self._streamProtocolFactory = streamProtocolFactory
		self._inactiveCheckInterval = inactiveCheckInterval
		# A dict mapping streamId->ServerStream
		self._streams = securedict()

		if self._inactiveCheckInterval is not None:
			self._idleKiller = LoopingCall(self.disconnectInactive)
			self._idleKiller.clock = self._clock
			# `now=True` to exercise the code early.
			self._idleKiller.start(self._inactiveCheckInterval, now=True)


	def getStream(self, streamId):
		try:
			return self._streams[streamId]
		except KeyError:
			raise NoSuchStream("I don't know about %r" % (streamId,))


	def buildStream(self, streamId):
		if streamId in self._streams:
			raise StreamAlreadyExists(
				"cannot make stream with id %r because it already exists" % (streamId,))

		s = self.stream(self._clock, streamId, self._streamProtocolFactory)
		self._streams[streamId] = s

		d = s.notifyFinish()
		d.addBoth(self._forgetStream, streamId)
		return s


	def _forgetStream(self, _ignoredNone, streamId):
		del self._streams[streamId]


	def disconnectInactive(self):
		"""
		Disconnect L{ServerStream}s that the client appears to have abandoned.
		By default, this is called automatically every 60 seconds, so you do
		not need to call it.
		"""
		# Make a "copy" with .values() because s.timedOut() below calls our
		# self._forgetStream, which mutates self._streams.
		for s in self._streams.values():
			if not s._transports and (
			s.lastReceived + s.maxIdleTime <= self._clock.seconds()):
				s.timedOut()



# A ServerTransport must have registerProducer and unregisterProducer
# because ServerStream calls those methods, but it doesn't actually need to be
# an IPushProducer/IPullProducer.  It could, in theory, buffer all the
# information it gets without caring about TCP pressure at all.
class IServerTransport(IConsumerWithoutWrite):

	ourSeqNum = Attribute(
		"Sequence number of the last string written to the socket/request, "
		"or -1 if no strings ever written")


	def writeStrings(queue, start):
		"""
		Write strings in queue C{queue} to the peer.
		This usually does not write strings that were already written to
		the peer over this transport.  The exception is when `start` is
		now lower (or None) compared to the previous `start`.

		@param queue: an L{abstract.Queue}
		@param start: Minimum string seqNum to consider sending, or C{None}
			to not skip any.
		@type start: L{int} or L{long} or L{NoneType}
		"""


	def closeGently():
		"""
		Close this transport.  Usually happens if the transport is no longer
		useful (due to HTTP limitations), or because a new active S2C
		transport has connected.

		Only transports with a _stream can be closed gently.
		"""


	def causedRwinOverflow():
		"""
		Close this transport because it has caused our receive window to
		overflow.  This provides a strong hint to the client that they should
		connect a new transport and send deliverable strings.
		"""


	def writeReset(reasonString, applicationLevel):
		"""
		Write out a reset frame on this transport, to indicate that server is
		resetting the stream.

		@param reasonString: plain-English reason why the stream is resetting
		@type reasonString: unicode

		@param applicationLevel: is it an application-level reset?
		@type applicationLevel: bool

		The reset frame (incl. reasonString) are not guaranteed to arrive
		to the peer, so it is only useful for aggregate logging and debugging.
		"""


	def isHttp():
		"""
		@return: Whether this transport is using HTTP.
		@rtype: bool

		@raise: L{RuntimeError} if we don't know yet.
		"""


	def isStreamingFromPeer():
		"""
		@return: Whether the peer can send us data more than once over this
			transport.
		@rtype: bool
		"""


	def isStreamingToPeer():
		"""
		@return: Whether we can send the peer data more than once over this
			transport.
		@rtype: bool
		"""


	def getHost():
		"""
		Get the host of the peer.

		@return: An L{IAddress} provider.
		"""


	def getInfo():
		"""
		@return: A L{TransportInfo} object with information about this
			transport.
		@rtype: L{TransportInfo}
		"""



def _sanitizeHelloFrame(helloFrame, isHttp):
	"""
	Mutate a L{HelloFrame} to sanitize it: disable some options for
	non-HTTP transports (because clients should not be using them anyway).

	C{isHttp} must be truthy if C{helloFrame} was received over an HTTP
	transport.
	"""
	if not isHttp:
		# For non-HTTP transports, don't allow clients to use these options.
		helloFrame.streamingResponse = True
		helloFrame.maxReceiveBytes = 2**53
		helloFrame.maxOpenTime = None



# Acceptable protocol modes for ServerTransport to be in.
# POLICYFILE and INT32 are for Flash Socket.
UNKNOWN, POLICYFILE, INT32, HTTP = \
	("UNKNOWN",), ("POLICYFILE",), ("INT32",), ("HTTP",)

# HTTP_RESPONSE_PREAMBLE is sent as the first frame over HTTP transports.
HTTP_RESPONSE_PREAMBLE = CommentFrame(";)]}")


DontWriteSack = ("DontWriteSack",)


class ServerTransport(object):
	"""
	Private.  Use ServerTransportFactory or WebPort, which will build this
	object (it is a a Protocol, among other things).

	One ServerTransport is instantiated for every HTTP request we receive
	(for HTTP endpoints), or for every TCP connection we receive (for
	Flash Socket endpoints).
	"""
	implements(IServerTransport, IPushProducer, IPullProducer, IProtocol)

	__slots__ = (
		'ourSeqNum', '_lastStartParam', '_mode', '_peerSeqNum',
		'_initialBuffer', '_toSend', 'writable', 'receivedCounter',
		'_terminating', '_paused', '_stream', '_producer', '_parser',
		'streamId', 'transportNumber', 'factory', '_sackDirty',
		'transport', '_maxReceiveBytes', '_maxOpenTime', '_callingStream',
		'_lastSackSeenByClient', '_streamingResponse', '_needPaddingBytes',
		'_wantsStrings', '_clock', '_maxOpenDc', '_maxInactivity', '_heartbeatDc')

	maxLength = 1024*1024
	noisy = True

	def __init__(self, clock):
		self._clock = clock

		self._stream = None
		self.writable = None

		# _initialBuffer buffers data while determining the mode
		self._initialBuffer = ''
		self._toSend = ''
		self._sackDirty = False
		self._terminating = False
		self._callingStream = False
		self._mode = UNKNOWN
		self.receivedCounter = -1
		self._lastStartParam = 2**64

		self.ourSeqNum = -1
		self._peerSeqNum = -1

		self._maxInactivity = None
		# _streamingResponse is False by default because client may fail
		# to send a proper Hello frame in their HTTP request, and we don't
		# want the request to get "stuck".
		self._streamingResponse = False

		self._producer = None
		self._paused = False

		self._maxOpenDc = None
		self._heartbeatDc = None


	def __repr__(self):
		return '<%s 0x%x terminating=%r, stream=%r, paused=%r, ourSeqNum=%r>' % (
			self.__class__.__name__, id(self),
			self._terminating, self._stream, self._paused, self.ourSeqNum)


	def isAttached(self):
		"""
		Is this ServerTransport currently attached to a L{ServerStream}?
		This is always C{False} after L{ServerStream.transportOffline}.
		"""
		return self._stream is not None


	def _maybeWriteToPeer(self):
		"""
		Writes bytes in C{self._toSend} to the peer, and terminates the
		transport if C{self._terminating} is truthy.
		"""
		if self._callingStream:
			return

		# If it's not a streaming response, we may have to write
		# termination headers and terminate.
		if self._toSend and not self._streamingResponse and not self._terminating:
			self._writeTerminationFrames()
			# Just in case we ever have a non-HTTP non-streamingResponse...
			if self._mode != HTTP:
				self._toSend += self._encodeFrame(YouCloseItFrame())
			self._terminating = True

		toSend = self._toSend
		if toSend:
			self._toSend = ''
			# Heartbeats are only sent when there's no S2C activity;
			# Because we're sending something, reset the heartbeat DelayedCall.
			self._resetHeartbeat()

			if self._mode == HTTP and not self.writable.startedWriting:
				encodedPreamble = self._encodeFrame(HTTP_RESPONSE_PREAMBLE)
				if self._terminating:
					headers = self.writable.responseHeaders
					headers.setRawHeaders('content-length',
						[str(len(encodedPreamble) + len(toSend))])
				self.writable.write(encodedPreamble)

			self.writable.write(toSend)

		if self._terminating:
			_cancelDc(self, '_maxOpenDc')
			_cancelDc(self, '_heartbeatDc')

			# Tell ServerStream this transport is offline.  Whether we
			# still have a TCP connection open to the peer is irrelevant.
			if self._stream:
				self._stream.transportOffline(self)
				self._stream = None

			if self._mode == HTTP:
				# _disconnected is in Twisted >= 9.0
				isDisconnected = getattr(self.writable, '_disconnected', False)
				if not isDisconnected and not self.writable.finished:
					self.writable.finish()

			# TODO: for non-HTTP, set timer and close the connection ourselves
			# in 5-10 seconds
			##self.transport.loseWriteConnection(), maybe followed by loseConnection later


	def _encodeFrame(self, frame):
		return self._parser.encode(frame.encode())


	def _writeTerminationFrames(self):
		if self._stream is not None: # isAttached?
			# Always write a SackFrame to avoid a complicated scenario where
			# client creates a useless primary transport that is closed quickly.
			# It can happen like this:
			# 1) Client has a long-poll primary open; client app sends a string.
			# 2) Client creates a secondary transport; server reacts to received string.
			# 3) Server sends a string over primary and closes primary.
			# 4) Client receives string/close over primary before receiving
			#     SackFrame/close over secondary.
			# 5) Client creates a new primary with a lastSackSeenByClient that does
			#     not include the SackFrame that server sent over secondary.
			# 6) Server thinks client needs a SackFrame because
			#     lastSackSeenByClient is older than expected.  Server writes
			#     SackFrame/close to the primary; client soon creates a
			#     new primary with an up-to-date lastSackSeenByClient.
			self._appendSack()

			self._toSend += self._encodeFrame(StreamStatusFrame(
				self._stream.lastSackSeenByServer))


	def _closeWith(self, reason):
		assert not self._terminating, self

		self._writeTerminationFrames()
		self._toSend += self._encodeFrame(TransportKillFrame(reason))
		if self._mode != HTTP:
			self._toSend += self._encodeFrame(YouCloseItFrame())
		self._terminating = True
		self._maybeWriteToPeer()


	def closeGently(self):
		"""
		@see L{IServerTransport.closeGently}
		"""
		assert not self._terminating, self

		self._writeTerminationFrames()
		if self._mode != HTTP:
			self._toSend += self._encodeFrame(YouCloseItFrame())
		self._terminating = True
		self._maybeWriteToPeer()


	def causedRwinOverflow(self):
		"""
		@see L{IServerTransport.causedRwinOverflow}
		"""
		self._closeWith(tk_rwin_overflow)
		self._maybeWriteToPeer()


	def writeReset(self, reasonString, applicationLevel):
		"""
		@see L{IServerTransport.writeReset}
		"""
		assert not self._terminating, self

		if self._sackDirty:
			self._appendSack()

		# Because it's a reset, there's no need to send a StreamStatusFrame
		self._toSend += self._encodeFrame(ResetFrame(reasonString, applicationLevel))
		if self._mode != HTTP:
			self._toSend += self._encodeFrame(YouCloseItFrame())
		self._terminating = True
		self._maybeWriteToPeer()


	def writeStrings(self, queue, start):
		"""
		@see L{IServerTransport.writeStrings}
		"""
		# If the transport is terminating, it should have already called
		# ServerStream.transportOffline(self)
		assert not self._terminating, self

		if self._sackDirty:
			self._appendSack()

		# Something went wrong if we're writing strings before
		# we received the hello frame.
		assert self.receivedCounter > -1, self.receivedCounter

		# See test_writeStringsConnectionInterleavingSupport
		# Remember that None < any number
		if start < self._lastStartParam:
			self.ourSeqNum = -1
			self._lastStartParam = start

		queueStart = max(start, self.ourSeqNum + 1)
		# Even if there's a lot of stuff in the queue, write everything.
		for seqNum, string in queue.iterItems(queueStart):
			##print seqNum, string, self.ourSeqNum
			if self.ourSeqNum == -1 or self.ourSeqNum + 1 != seqNum:
				self._toSend += self._encodeFrame(SeqNumFrame(seqNum))
			self._toSend += self._encodeFrame(StringFrame(string))
			self.ourSeqNum = seqNum
		self._maybeWriteToPeer()


	def _exceededMaxOpenTime(self):
		if self._stream is not None: # isAttached?
			self.closeGently()


	def _appendHeartbeat(self):
		self._toSend += self._encodeFrame(CommentFrame('beat'))


	def _writeHeartbeat(self):
		self._appendHeartbeat()
		self._maybeWriteToPeer()
		# Because _toSend non-empty, _maybeWriteToPeer calls _resetHeartbeat


	def _resetHeartbeat(self):
		_cancelDc(self, '_heartbeatDc')

		# Could be None if no HelloFrame, or 0 if HelloFrame received.
		if self._maxInactivity:
			self._heartbeatDc = self._clock.callLater(
				self._maxInactivity, self._writeHeartbeat)


	def _writeInitialFrames(self, stream, requestNewStream):
		assert not self._terminating, self

		if requestNewStream:
			# If we send StreamCreatedFrame, it *must* be the first frame
			# we send.  If we send something else like a SackFrame first, and
			# transport abruptly disconnects after that frame, client may get
			# into an inconsistent state.
			self._toSend += self._encodeFrame(StreamCreatedFrame())

		# Write the initial SACK if we have not already written a SACK,
		# but only if the client has an out-of-date impression of the SACK.
		# We can't always send the SACK because long-poll transports
		# require closing after sending anything.
		if self._lastSackSeenByClient is not DontWriteSack:
			currentSack = stream.getSACK()
			if currentSack != self._lastSackSeenByClient:
				self._toSend += self._encodeFrame(SackFrame(currentSack))


	def _handleHelloFrame(self, hello, moreFrames):
		"""
		C{hello} is a L{HelloFrame}.  If a stream with the streamId in the
		HelloFrame does not exist (and requestNewStream is falsy), raises
		L{NoSuchStream}.
		"""
		_sanitizeHelloFrame(hello, self._mode == HTTP)

		# self._protocolVersion = protocolVersion # Not needed at the moment
		self.streamId = hello.streamId
		self.transportNumber = hello.transportNumber
		self._streamingResponse = hello.streamingResponse
		self._maxInactivity = hello.maxInactivity
		self._lastSackSeenByClient = hello.lastSackSeenByClient
		self._wantsStrings = hello.wantsStrings()

		if self._mode == HTTP:
			self._needPaddingBytes = hello.needPaddingBytes
			self._maxReceiveBytes = hello.maxReceiveBytes
			self._maxOpenTime = hello.maxOpenTime
			if self._maxOpenTime is not None:
				self._maxOpenDc = self._clock.callLater(
					self._maxOpenTime, self._exceededMaxOpenTime)

		# Note that requestNewStream=True doesn't always imply that a
		# new stream will actually be created.
		if hello.requestNewStream:
			try:
				stream = self.factory.streamTracker.buildStream(self.streamId)
			except StreamAlreadyExists:
				stream = self.factory.streamTracker.getStream(self.streamId)
		else:
			stream = self.factory.streamTracker.getStream(self.streamId)
		# Above .getStream(...) calls may raise NoSuchStream, which is
		# caught by our caller.

		self._writeInitialFrames(stream, hello.requestNewStream)
		if hello.sack is not None:
			# Call sackReceived before transportOnline:
			# * If hello.sack is a bad SACK, we never tell ServerStream
			# 	about the transport.
			# * If this transport is succeeding another transport, the
			# 	hello.sack removes strings from server's Queue but keeps
			# 	this new transport in _pretendAcked mode.
			if stream.sackReceived(hello.sack):
				# It was a bad SACK, so close.
				self._closeWith(tk_acked_unsent_strings)
				return

		# Note: self._stream being non-None implies that we are attached to
		# the ServerStream (i.e. have called transportOnline, or are
		# calling it right now).
		self._stream = stream
		self._callingStream = True
		succeedsTransport = hello.succeedsTransport if self._wantsStrings else None
		self._stream.transportOnline(self, self._wantsStrings, succeedsTransport)
		self._callingStream = False
		# Remember that a lot can happen underneath that
		# transportOnline call, because it may construct a
		# IStringProtocol, which may even call reset.
		if self._terminating:
			return

		self._framesReceived(moreFrames)
		# Remember that a lot can happen underneath that
		# _framesReceived call, including a reset.
		if self._terminating:
			return

		if self._mode == HTTP and not self._wantsStrings:
			self.closeGently()

		if self._terminating:
			return

		if self._maxInactivity:
			self._appendHeartbeat()
		self._resetHeartbeat()

		self._maybeWriteToPeer()


	def _appendSack(self):
		"""
		Append a SackFrame to the internal send buffer.
		"""
		self._toSend += self._encodeFrame(SackFrame(self._stream.getSACK()))
		self._sackDirty = False
		# We no longer need to write the "initial SACK" to client
		self._lastSackSeenByClient = DontWriteSack


	def _framesReceived(self, frames):
		nonlocal = dict(bunchedStrings=[])
		def handleStrings():
			# bunchedStrings is already sorted 99.99%+ of the time, so this
			# sort is particularly fast with Timsort.
			nonlocal['bunchedStrings'].sort()

			# The _sackDirty behavior in this class reduces the number
			# of SackFrames that are written out, while making sure that
			# SackFrames are not "held up" by StringFrames written out by
			# ServerStream.  If ServerStream writes strings during the
			# ServerStream.stringsReceived call below, a SackFrame is
			# sent before the StringFrames.
			assert not self._sackDirty, self
			self._sackDirty = True
			self._callingStream = True
			try:
				self._stream.stringsReceived(self, nonlocal['bunchedStrings'])
			finally:
				self._callingStream = False
			# Remember that a lot can happen underneath that stringsReceived call,
			# including a call to our own `reset` or `closeGently` or `writeStrings`.

			nonlocal['bunchedStrings'] = []

			if not self._terminating and self._sackDirty:
				self._appendSack()

		for frameString in frames:
			if self._terminating:
				return
			self.receivedCounter += 1

			if isinstance(frameString, str):
				frameString = StringFragment(frameString, 0, len(frameString))

			try:
				frame = decodeFrameFromClient(frameString)
			except InvalidFrame:
				##log.err()
				self._closeWith(tk_invalid_frame_type_or_arguments)
				break

			frameType = frame.__class__

			# First frame must be hello frame; must not receive the hello
			# frame twice.
			if self.receivedCounter == 0:
				if frameType == HelloFrame:
					try:
						self._handleHelloFrame(frame, frames[1:])
					except NoSuchStream:
						self._closeWith(tk_stream_attach_failure)
						break
					# break because self._framesReceived(frames[1:])
					# processes the remaining frames.
					break
				else:
					self._closeWith(tk_invalid_frame_type_or_arguments)
					break

			elif frameType == StringFrame:
				# Make sure the string only contains bytes in the restricted
				# string range.  In the future, we could support dynamic
				# switching to strings that allow a wider byte/char range.
				if not isRestrictedString(frame.string.as_buffer()):
					self._closeWith(tk_invalid_frame_type_or_arguments)
					break

				self._peerSeqNum += 1
				# Because we may have received multiple Minerva strings,
				# collect them into a list and then deliver them all at
				# once to ServerStream.  This does not add any latency;
				# it just reduces the number of funcalls.
				nonlocal['bunchedStrings'].append((self._peerSeqNum, frame.string))

			elif frameType == SackFrame:
				self._callingStream = True
				badSack = self._stream.sackReceived(frame.sack)
				self._callingStream = False
				if badSack:
					# It was a bad SACK, so close.
					self._closeWith(tk_acked_unsent_strings)
					break

			elif frameType == SeqNumFrame:
				self._peerSeqNum = frame.seqNum - 1

			else:
				# Deliver the strings before processing client's reset frame.  This
				# is an implementation detail that may change.
				if nonlocal['bunchedStrings']:
					handleStrings()

				if frameType == ResetFrame:
					self._callingStream = True
					self._stream.resetFromPeer(
						frame.reasonString, frame.applicationLevel)
					self._callingStream = False
					break # No need to process any frames after the reset frame

				else:
					self._closeWith(tk_invalid_frame_type_or_arguments)
					break

		# TODO: add test to ensure that we successfully process bunchedStrings
		# before transport-killing due to a bad frame.

		if nonlocal['bunchedStrings']:
			handleStrings()
		self._maybeWriteToPeer()


	def dataReceived(self, data):
		##print repr(data)
		if self._terminating:
			# Ignore data received if we are terminating.
			return

		# Before we can even speak "Minerva" and send frames, we need to
		# determine what mode the client wants us to speak in.
		if self._mode == UNKNOWN:
			self._initialBuffer += data

			if self._initialBuffer.startswith('<policy-file-request/>\x00'):
				self._mode = POLICYFILE
				del self._initialBuffer
				self.writable.write(self.factory.policyStringWithNull)
				self._terminating = True

				# No need to loseConnection here, because Flash player
				# (hopefully) will close it: "The server must send a null
				# byte to terminate a policy file and may then close
				# the connection; if the server does not close the
				# connection, the Flash Player will do so upon receiving
				# the terminating null byte." http://goo.gl/op7yg

				# TODO: loseConnection in 5-10 seconds, if client doesn't.
				# Don't use loseWriteConnection because the client doesn't
				# send anything else over this connection anyway.
				return

			elif self._initialBuffer.startswith('<int32/>\n'):
				self._mode = INT32
				frameData = self._initialBuffer[len('<int32/>\n'):]
				del self._initialBuffer
				self._parser = decoders.Int32StringDecoder(
					maxLength=self.maxLength)
			# TODO: implement <int32-zlib/> but beware of zlib bombs

			# We need far less than 512, but stay on the safe side.
			elif len(self._initialBuffer) >= 512:
				# Terminating, but we can't even send any type of frame.
				self._terminating = True
				# RST them instead of FIN, because they don't look
				# like a well-behaving client anyway.
				if hasattr(self.writable, 'abortConnection'):
					# We know that writable is an ITCPTransport here,
					# not a Request.
					self.writable.abortConnection()
				else:
					# abortConnection not yet in Twisted trunk; see
					# http://twistedmatrix.com/trac/ticket/78
					self.writable.loseConnection()
				return

			else:
				return
		else:
			frameData = data

		out, code = self._parser.getNewFrames(frameData)
		if code == decoders.OK:
			##print out
			self._framesReceived(out)
		else:
			self._closeWith(tk_frame_corruption)

		if self._stream:
			self._stream.lastReceived = self._clock.seconds()

		self._maybeWriteToPeer()


	# called by ServerStream
	def registerProducer(self, producer, streaming):
		if self._producer:
			raise RuntimeError("Cannot register producer %s, "
				"because producer %s was never unregistered." % (
					producer, self._producer))

		# no 'disconnected' check?

		self._producer = producer
		##self._streamingProducer = streaming # No need to keep this info around, apparently

		# twisted.web.http.Request will pause a push producer if the
		# request is queued, so we must not pause it ourselves.
		doNotPause = self._mode == HTTP and self.writable.queued and streaming

		if streaming and self._paused and not doNotPause:
			producer.pauseProducing()

		self.writable.registerProducer(self, streaming)
		self._maybeWriteToPeer()


	# called by ServerStream
	def unregisterProducer(self):
		"""
		Stop consuming data from a producer.
		"""
		self._producer = None
		self.writable.unregisterProducer()


	# called by Twisted.  We trust Twisted to only call this if we registered
	# a push producer with self.writable
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

		if self._stream:
			# We need to update lastReceived to give the client some time
			# to connect a new transport (otherwise, disconnectInactive
			# would reset streams that just happened to have no
			# transports at that instant).
			self._stream.lastReceived = self._clock.seconds()

		# It might already be terminating, but often not.
		self._terminating = True
		self._maybeWriteToPeer()


	def _handleRequestBody(self):
		request = self.writable

		if __debug__:
			pos = request.content.tell()
			assert pos == 0, pos

		body = request.content.read()
		# Proxies *might* strip whitespace around the request body, so add
		# a newline if necessary.
		if body and body[-1] != '\n':
			log.msg("Unusual: POST body did not end in newline for "
				"%r from %r" % (request, request.client))

		if '\r\n' in body:
			body = body.replace('\r\n', '\n')
			log.msg("Unusual: found a CRLF in POST body for "
				"%r from %r" % (request, request.client))

		setNoCacheNoStoreHeaders(request)

		setRawHeaders = request.responseHeaders.setRawHeaders

		# "For Webkit browsers, it's critical to specify a Content-Type of
		# "text/plain" or "application/x-javascript" when returning script
		# content to an XHR for progressive handling."
		# - http://www.kylescholz.com/blog/2010/01/progressive_xmlhttprequest_1.html
		setRawHeaders('content-type', ['text/plain'])

		self.dataReceived(body)


	# Called by _HttpIo
	def requestStarted(self, request):
		assert self._mode == UNKNOWN, self._mode
		self._mode = HTTP
		self._parser = decoders.DelimitedStringDecoder(maxLength=self.maxLength)
		self.writable = request
		self._handleRequestBody()


	# Called by twisted.web if client closes connection before the request is finished
	def requestAborted(self, reason):
		if self.noisy:
			log.msg('Peer aborted request %r on %r' % (self.writable, self))
		# It might already be terminating, but often not.
		self._terminating = True
		self._maybeWriteToPeer()


	def connectionMade(self):
		# Note for HTTP transports: we don't setTcpNoDelay on HTTP
		# transports, because that requires digging into private state and
		# can affect non-Minerva requests on the same HTTP connection.
		# Applications that demand low latency should use
		# L{webmagic.untwist.BetterSite}, which calls setTcpNoDelay.
		self.writable.setTcpNoDelay(True)
		if self.noisy:
			log.msg('Connection made for %r' % (self,))


	# Called by Twisted when a TCP connection is made
	def makeConnection(self, transport):
		self.writable = transport
		self.connectionMade()


	def isHttp(self):
		"""
		@see L{IServerTransport.isHttp}
		"""
		if self.writable is None:
			raise RuntimeError("Don't yet know whether this is an HTTP transport")
		return self._mode == HTTP


	def isStreamingFromPeer(self):
		"""
		@see L{IServerTransport.isStreamingFromPeer}
		"""
		return not self.isHttp()


	def isStreamingToPeer(self):
		"""
		@see L{IServerTransport.isStreamingToPeer}
		"""
		return self._streamingResponse


	def getHost(self):
		"""
		@see L{IServerTransport.getHost}
		"""
		return self.writable.getHost()


	def getInfo(self):
		"""
		@see L{IServerTransport.getInfo}
		"""
		return TransportInfo(
			transportNumber=self.transportNumber,
			isPrimary=self._wantsStrings,
			streamingFromPeer=self.isStreamingFromPeer(),
			streamingToPeer=self.isStreamingToPeer(),
			host=self.getHost(),
			requestHeaders=\
				self.writable.requestHeaders if self.isHttp() else None)



requireFile(FilePath(__file__).sibling('compiled_client').child('FlashConnector.swf').path)
requireFile(FilePath(__file__).sibling('compiled_client').child('expressInstall.swf').path)

class ServerTransportFactory(protocol.ServerFactory):
	"""
	You must listenTCP with this factory if you want Minerva clients to be
	able to connect to your Minerva server using Flash sockets.
	"""
	implements(IProtocolFactory)
	__slots__ = ('_clock', 'streamTracker', 'policyStringWithNull')

	protocol = ServerTransport

	def __init__(self, clock, streamTracker, policyString=None):
		"""
		@param clock: an L{IReactorTime} provider.

		@param streamTracker: The L{StreamTracker} that will know about all
			active L{ServerStream}s.
		@type streamTracker: L{StreamTracker}

		@param policyString: a Flash/Silverlight policy file as a string,
			sent in response to <policy-file-request/>C{NULL}.
		@type policyString: C{str} or C{NoneType}
		"""
		self._clock = clock
		self.streamTracker = streamTracker
		self.setPolicyString(policyString)


	def setPolicyString(self, policyString):
		"""
		Set the Flash/Silverlight socket policy to C{policyString}.  Existing
		open connections will serve the old policy (though this is of little
		consequence).

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
			self.policyStringWithNull = policyString + '\x00'
		else:
			# TODO: verify that Flash Player actually closes connection
			# when it sees just NULL
			self.policyStringWithNull = '\x00'


	def buildProtocol(self, addr):
		p = self.protocol(self._clock)
		p.factory = self
		return p



def _contentToTemplate(content):
	import jinja2
	return jinja2.Environment().from_string(content.decode('utf-8'))


requireFiles([
	FilePath(__file__).sibling('xdrframe.html').path,
	FilePath(__file__).sibling('compiled_client').child('xdrframe.js').path])

class XDRFrame(BetterResource):
	"""
	A page suitable for loading into an iframe.  It sets a document.domain
	so that it can communicate with the parent page (which must also set
	document.domain).  It is capable of making XHR requests.
	"""
	isLeaf = True
	_templateVars = {'dev_mode': False}
	_templateFile = FilePath(__file__).sibling('xdrframe.html')

	def __init__(self, allowedDomains, fileCache):
		self._allowedDomains = allowedDomains
		self._fileCache = fileCache


	def render_GET(self, request):
		frameIdStr = request.args['id'][0]
		domain = request.args['domain'][0]
		if not re.match('^([A-Za-z0-9]*)$', frameIdStr):
			raise ValueError("frameIdStr contained bad characters: %r" % (frameIdStr,))
		if len(frameIdStr) > 50:
			raise ValueError("frameIdStr too long: %r" % (frameIdStr,))
		if not domain in self._allowedDomains:
			raise ValueError("Domain %r not in allowed domains %r" % (
				domain, self._allowedDomains))

		template, _ = self._fileCache.getContent(
			self._templateFile.path, transform=_contentToTemplate)
		rendered = template.render(dict(
			htmldumps=htmldumps,
			cacheBreakLink=partial(
				getCacheBrokenHref, self._fileCache, request),
			domain=domain,
			frameIdStr=frameIdStr,
			**self._templateVars))
		return rendered.encode('utf-8')



class XDRFrameDev(XDRFrame):
	"""
	Like XDRFrame, except load the uncompiled JavaScript code, instead of
	the compiled xdrframe.js.
	"""
	_templateVars = {'dev_mode': True}



class _HttpIo(BetterResource):
	isLeaf = True
	protocol = ServerTransport

	def __init__(self, clock, streamTracker):
		BetterResource.__init__(self)
		self._clock = clock
		self.streamTracker = streamTracker


	def render_POST(self, request):
		t = self.protocol(self._clock)
		t.factory = self
		d = request.notifyFinish()
		d.addErrback(t.requestAborted)
		t.requestStarted(request)
		return NOT_DONE_YET



requireFiles([
	FilePath(__file__).sibling('compiled_client').child('FlashConnector.swf').path])

_defaultFileCache = FileCache(time.time, 0.1)

class WebPort(BetterResource):
	"""
	L{WebPort} serves multiple resources that allow for browser<->Minerva
	server communication:

	-	io: used by Minerva client's HTTP transports to send and receive Minerva frames.

	-	xdrframe: cross-subdomain communication helper; compiled JS.

	-	xdrframe_dev: cross-subdomain communication helper; uncompiled JS.

	-	FlashConnector.swf: resource required by Minerva client's Flash transport.

	-	minerva-client.js: standalone Minerva client, available here for convenience.

	You must put this resource into your L{Site}'s resource tree so that Minerva
	clients can connect to your Minerva server.
	"""
	def __init__(self, clock, streamTracker, allowedDomains=None, fileCache=_defaultFileCache):
		BetterResource.__init__(self)

		if allowedDomains is None:
			allowedDomains = []

		self.putChild('io', _HttpIo(clock, streamTracker))
		self.putChild('xdrframe', XDRFrame(allowedDomains, fileCache))
		self.putChild('xdrframe_dev', XDRFrameDev(allowedDomains, fileCache))

		flashConnector = FilePath(__file__).\
			sibling('compiled_client').child('FlashConnector.swf')
		self.putChild('FlashConnector.swf', BetterFile(flashConnector.path))

		# User can load minerva-client.js from anywhere, but provide it
		# in _minerva/ for convenience.  (Or if user is using Closure
		# Library for their application, they will load their own JS instead
		# the standalone minerva-client.js.)
		minervaClient = FilePath(__file__).\
			sibling('compiled_client').child('minerva-client.js')
		self.putChild('minerva-client.js', BetterFile(minervaClient.path))



try: from refbinder.api import bindRecursive
except ImportError: pass
else: bindRecursive(sys.modules[__name__], _postImportVars)
