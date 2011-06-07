from zope.interface import implements

from twisted.internet import defer

from strfrag import StringFragment

from minerva.window import SACK, Queue, Incoming
from minerva.newlink import (
	NoSuchStream, IMinervaProtocol, IMinervaFactory, StreamAlreadyExists)
from minerva.decoders import OK
from minerva.frames import decodeFrameFromServer

from webmagic.fakes import GetNewMixin, DummyTCPTransport



def strictGetNewFrames(parser, data):
	"""
	Wrapper function for L{parser.getNewFrames} that checks the code
	and throws an error if C{code != OK}.
	"""
	out, code = parser.getNewFrames(data)
	if code != OK:
		raise RuntimeError("Parse error; code was %r" % (code,))
	return out, code



class FrameDecodingTcpTransport(DummyTCPTransport, GetNewMixin):
	"""
	A TCP transport that first decodes bytes with a parser,
	then decodes the Minerva frames with decodeFrameFromServer.
	"""
	def __init__(self, parser):
		self.parser = parser
		self.log = []


	def write(self, data):
		frames, code = strictGetNewFrames(self.parser, data)
		self.log.extend(decodeFrameFromServer(
			StringFragment(f, 0, len(f)) if isinstance(f, str) else f) for f in frames)



class MockStream(GetNewMixin):
	streamId = "a stream id of unusual length"

	def __init__(self, clock=None, streamId=None, streamProtocolFactory=None):
		## if streamId is None: # make a random one?
		self.virgin = True
		self._notifications = []
		self.streamId = streamId
		self.streamProtocolFactory = streamProtocolFactory
		self.log = []
		self._incoming = Incoming()
		self.queue = Queue()
		self._transports = set()
		self.allSeenTransports = []
		self.lastSackSeenByServer = SACK(-1, ())


	def sendStrings(self, strings):
		self.log.append(['sendStrings', strings])


	def reset(self, reasonString):
		self.log.append(['reset', reasonString])


	def resetFromPeer(self, reasonString, applicationLevel):
		self.log.append(['resetFromPeer', reasonString, applicationLevel])
		for t in self._transports.copy():
			t.closeGently()


	def stringsReceived(self, transport, strings):
		self.log.append(['stringsReceived', transport, strings])
		self._incoming.give(strings)


	def sackReceived(self, sack):
		"""
		Returns C{True} if SACK was bad, C{False} otherwise.
		"""
		self.log.append(['sackReceived', sack])
		self.lastSackSeenByServer = sack
		return self.queue.handleSACK(sack)


	def transportOnline(self, transport, wantsStrings, succeedsTransport):
		self.allSeenTransports.append(transport)
		self.virgin = False
		self.log.append(['transportOnline', transport, wantsStrings, succeedsTransport])
		assert transport not in self._transports
		self._transports.add(transport)


	def transportOffline(self, transport):
		self.log.append(['transportOffline', transport])
		self._transports.remove(transport)


	def serverShuttingDown(self, transport):
		self.log.append(['serverShuttingDown', transport])


	def pauseProducing(self):
		self.log.append(['pauseProducing'])


	def resumeProducing(self):
		self.log.append(['resumeProducing'])


	def stopProducing(self):
		self.log.append(['stopProducing'])


	def getSACK(self):
		self.log.append(['getSACK'])
		return self._incoming.getSACK()


	def notifyFinish(self):
		"""
		Notify when finishing the request

		@return: A deferred. The deferred will be triggered when the
		stream is finished -- always with a C{None} value.
		"""
		self.log.append(['notifyFinish'])
		self._notifications.append(defer.Deferred())
		return self._notifications[-1]


	def _pretendFinish(self):
		for d in self._notifications:
			d.callback(None)
		self._notifications = None



class _MockMinervaProtocol(GetNewMixin):
	implements(IMinervaProtocol)

	def __init__(self, callFrom=(), callWhat=()):
		self._callFrom = callFrom
		self._callWhat = callWhat


	def _callStuff(self):
		if 'sendStrings' in self._callWhat:
			self.stream.sendStrings(["s2cbox0", "s2cbox1"])
			self.stream.sendStrings(["s2cbox2"])
		if 'reset' in self._callWhat:
			self.stream.reset('reset forced by mock protocol')


	def streamStarted(self, stream):
		self.factory.instances.add(self)
		self.log = []
		self.log.append(['streamStarted', stream])
		self.stream = stream
		if 'streamStarted' in self._callFrom:
			self._callStuff()


	def streamReset(self, reasonString, applicationLevel):
		self.log.append(['streamReset', reasonString, applicationLevel])



class MockMinervaStringsProtocol(_MockMinervaProtocol):

	def stringsReceived(self, strings):
		self.log.append(['stringsReceived', strings])
		if 'stringsReceived' in self._callFrom:
			self._callStuff()



class MockMinervaStringProtocol(_MockMinervaProtocol):

	def stringReceived(self, s):
		self.log.append(['stringReceived', s])
		if 'stringReceived' in self._callFrom:
			self._callStuff()



class MockMinervaStringsProtocolFactory(object):
	implements(IMinervaFactory)

	protocol = MockMinervaStringsProtocol

	def __init__(self):
		self.instances = set()


	def buildProtocol(self):
		obj = self.protocol()
		obj.factory = self
		return obj



class MockMinervaStringProtocolFactory(object):
	implements(IMinervaFactory)

	protocol = MockMinervaStringProtocol

	def __init__(self):
		self.instances = set()


	def buildProtocol(self):
		obj = self.protocol()
		obj.factory = self
		return obj



class DummySocketLikeTransport(GetNewMixin):
	request = None
	globalCounter = [-1]
	ourSeqNum = -1
	_paused = False

	def __init__(self, request=None):
		self.log = []
		self.pretendGotHello()
		if request:
			self.writable = request
			self._isHttp = True
		else:
			self._isHttp = False


	def isHttp(self):
		return self._isHttp


	def pretendGotHello(self):
		self.globalCounter[0] += 1
		self.transportNumber = self.globalCounter[0]


	def closeGently(self):
		self.log.append(['closeGently'])


	def causedRwinOverflow(self):
		self.log.append(['causedRwinOverflow'])


	def writeReset(self, reasonString, applicationLevel):
		self.log.append(['writeReset', reasonString, applicationLevel])


	def writeStrings(self, queue, start):
		self.log.append(['writeStrings', queue, start])

		lastBox = self.ourSeqNum
		for seqNum, string in queue.iterItems(start=start):
			if lastBox == -1 or lastBox + 1 != seqNum:
				pass
				##toSend += self._encodeFrame(SeqNumFrame(seqNum))
			##toSend += self._encodeFrame(StringFrame(string))
			lastBox = seqNum
		self.ourSeqNum = lastBox


	def registerProducer(self, producer, streaming):
		self.log.append(['registerProducer', producer, streaming])


	def unregisterProducer(self):
		self.log.append(['unregisterProducer'])


	def pauseProducing(self):
		self._paused = True



class DummyStreamTracker(object):

	stream = MockStream

	def __init__(self, clock, streamProtocolFactory, _streams):
		self._clock = clock
		self._streamProtocolFactory = streamProtocolFactory
		self._streams = _streams


	def getStream(self, streamId):
		try:
			return self._streams[streamId]
		except KeyError:
			raise NoSuchStream("I don't know about %r" % (streamId,))


	def buildStream(self, streamId):
		"""
		This is missing a lot of features that are in the real L{StreamTracker}.
		"""
		if streamId in self._streams:
			raise StreamAlreadyExists()

		s = self.stream(self._clock, streamId, self._streamProtocolFactory)
		self._streams[streamId] = s

		d = s.notifyFinish()
		d.addBoth(self._forgetStream, streamId)
		return s


	def _forgetStream(self, _ignoredNone, streamId):
		del self._streams[streamId]


	def countStreams(self):
		return len(self._streams)
