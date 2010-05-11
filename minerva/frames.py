"""
This file includes frame encoders and decoders for each frame type, so that
it is suitable for both both Minerva server, and a Python Minerva client (not
yet written).

TODO: add HelloFrame.encode
"""

from mypy.objops import ensureBool, ensureNonNegIntLimit, strToNonNegLimit
from mypy.constant import Constant, BC_VALUE
from mypy.strops import FS_STR, FS_POSITION, FS_SIZE
from minerva.decoders import strictDecoder

_postImportVars = vars().keys()


# Property key names for the hello frame.
Hello_transportNumber = 'n'
Hello_protocolVersion = 'v'
Hello_httpFormat = 't'
Hello_requestNewStream = 'w'
Hello_streamId = 'i'
Hello_credentialsData = 'c'
Hello_streamingResponse = 's'
Hello_needPaddingBytes = 'p'
Hello_maxReceiveBytes = 'r'
Hello_maxOpenTime = 'm'
Hello_useMyTcpAcks = 'a'
Hello_succeedsTransport = 'g'


FORMAT_XHR, FORMAT_HTMLFILE = 2, 3


class InvalidFrame(Exception):
	pass



class InvalidHello(InvalidFrame):
	pass



class HelloFrame(object):
	__slots__ = (
		'credentialsData', 'requestNewStream', 'transportNumber',
		'protocolVersion', 'streamId', 'wantsStrings', 'succeedsTransport',
		'httpFormat', 'streamingResponse', 'needPaddingBytes', 'maxReceiveBytes',
		'maxOpenTime')


	@classmethod
	def decode(cls, frameString, isHttp):
		"""
		C{frameString} is a L{StringFragment} that ends with "H".
		"""
		helloData, stoppedAt = strictDecoder.raw_decode(
			frameString[FS_STR], frameString[FS_POSITION])
		# `- 1` because we expect to stop before the trailing "H"
		if stoppedAt != frameString[FS_POSITION] + frameString[FS_SIZE] - 1:
			raise InvalidHello

		if not isinstance(helloData, dict):
			raise InvalidHello

		obj = cls()

		# credentialsData is always optional
		obj.credentialsData = helloData[Hello_credentialsData] if \
			Hello_credentialsData in helloData else {}

		if not isinstance(obj.credentialsData, dict):
			raise InvalidHello

		try:
			# Any line here can raise KeyError; additional exceptions marked with 'e:'

			# requestNewStream is always optional. If missing or False/0, transport
			# is intended to attach to an existing stream.
			obj.requestNewStream = ensureBool( # e: ValueError
				helloData[Hello_requestNewStream]) if \
				Hello_requestNewStream in helloData else False

			obj.transportNumber = ensureNonNegIntLimit( # e: ValueError, TypeError
				helloData[Hello_transportNumber], 2**64)

			obj.protocolVersion = helloData[Hello_protocolVersion]

			obj.streamingResponse = ensureBool( # e: ValueError
				helloData[Hello_streamingResponse])

			# Rules for streamId: must be 20-30 inclusive bytes, must not
			# contain codepoints > 127
			obj.streamId = helloData[Hello_streamId]
			# ,str is appropriate only because simplejson returns str when possible
			if not isinstance(obj.streamId, str) or not 20 <= len(obj.streamId) <= 30:
				raise InvalidHello
		except (KeyError, TypeError, ValueError):
			raise InvalidHello

		if obj.protocolVersion != 2:
			raise InvalidHello

		# succeedsTransport is always optional. If missing, the client does not
		# want to get S2C strings over this transport. If None, the client does,
		# but the transport does not succeed an existing primary transport. If a
		# number, the transport might succeed an existing primary transport.
		obj.wantsStrings = Hello_succeedsTransport in helloData
		if obj.wantsStrings:
			obj.succeedsTransport = helloData[Hello_succeedsTransport]
			if obj.succeedsTransport is not None:
				try:
					obj.succeedsTransport = ensureNonNegIntLimit(
						obj.succeedsTransport, 2**64)
				except (TypeError, ValueError):
					raise InvalidHello

		if isHttp:
			try:
				obj.httpFormat = helloData[Hello_httpFormat]
			except KeyError:
				raise InvalidHello
			if not obj.httpFormat in (FORMAT_XHR, FORMAT_HTMLFILE):
				raise InvalidHello

			# needPaddingBytes is always optional. If missing, 0.
			if Hello_needPaddingBytes in helloData:
				try:
					obj.needPaddingBytes = ensureNonNegIntLimit(
						helloData[Hello_needPaddingBytes], 16*1024) # e: ValueError, TypeError
				except (TypeError, ValueError):
					raise InvalidHello
			else:
				obj.needPaddingBytes = 0

			try:
				obj.maxReceiveBytes = ensureNonNegIntLimit(
					helloData[Hello_maxReceiveBytes], 2**64) # e: ValueError, TypeError
				obj.maxOpenTime = ensureNonNegIntLimit(
					helloData[Hello_maxOpenTime], 2**64) # e: ValueError, TypeError
			except (TypeError, ValueError):
				raise InvalidHello

		return obj



class StringFrame(object):
	__slots__ = ('string',)

	def __init__(self, string):
		"""
		C{string} is a L{StringFragment}.
		"""
		self.string = string


	@classmethod
	def decode(cls, frameString):
		"""
		C{frameString} is a L{StringFragment} that ends with "~".
		"""
		obj = cls()
		obj.string = frameString[:-1]
		return obj


	def encode(self):
		return str(self.string) + '~'



class SeqNumFrame(object):
	__slots__ = ('seqNum',)

	def __init__(self, seqNum):
		self.seqNum = seqNum


	@classmethod
	def decode(cls, frameString):
		"""
		C{frameString} is a L{StringFragment} that ends with "N".
		"""
		try:
			seqNum = strToNonNegLimit(frameString, 2**64)
		except ValueError:
			raise InvalidFrame
		return cls(seqNum)


	def encode(self):
		return '%dN' % self.seqNum



class SackFrame(object):
	__slots__ = ('ackNumber', 'sackList')

	def __init__(self, ackNumber, sackList):
		self.ackNumber = ackNumber
		self.sackList = sackList


	@classmethod
	def decode(cls, frameString):
		"""
		C{frameString} is a L{StringFragment} that ends with "A".
		"""
		joinedSackList, ackNumberStr = str(frameString[:-1]).split('|')
		sackListStrs = joinedSackList.split(',')
		try:
			sackList = list(strToNonNegLimit(s, 2**64) for s in sackListStrs)
			ackNumber = strToNonNegLimit(ackNumberStr)
		except ValueError:
			raise InvalidFrame
		return cls(ackNumber, sackList)


	def encode(self):
		return ','.join(self.sackList) + '|' + str(self.ackNumber) + 'A'



class YouCloseItFrame(object):
	__slots__ = ()

	@classmethod
	def decode(cls, frameString):
		"""
		C{frameString} is a L{StringFragment} that ends with "Y".
		"""
		if len(frameString) != 1:
			raise InvalidFrame
		return cls()


	def encode(self):
		return 'Y'



class WhoReset(object):
	server_minerva = 1
	server_app = 2
	client_minerva = 3
	client_app = 4



def isValidReasonString(reasonString):
	"""
	Return C{True} if C{reasonString} is a valid reset reason.
	C{reasonString} is assumed to be a C{str}; no other assumptions
	are made.
	"""
	if len(reasonString) > 255:
		return False
	for c in reasonString:
		if not ' ' <= c <= '~':
			return False
	return True


class ResetFrame(object):
	"""
	A reset frame indicates this side has given up on the Stream.
	A reset frame implies a transport kill as well.
	"""
	__slots__ = ()

	def __init__(self, reasonString, applicationLevel):
		"""
		@param reasonString: why the Stream reset.
			ASCII (0x20-0x7E)-only C{str}, max 255 bytes.
		"""
		self.reasonString = reasonString
		self.applicationLevel = applicationLevel


	@classmethod
	def decode(cls, frameString):
		"""
		C{frameString} is a L{StringFragment} that ends with "!".
		"""
		reasonString, applicationLevelStr = str(frameString[:-1]).split('|')
		try:
			applicationLevel = {'0': False, '1': True}[applicationLevelStr]
		except KeyError:
			raise InvalidFrame
		if not isValidReasonString(reasonString):
			raise InvalidFrame

		return cls(reasonString, applicationLevel)


	def encode(self):
		return self.reasonString + '|' + str(int(self.applicationLevel)) + '!'



class PaddingFrame(object):
	__slots__ = ()

	def __init__(self, numBytes):
		self.numBytes = numBytes


	@classmethod
	def decode(cls, frameString):
		"""
		C{frameString} is a L{StringFragment} that ends with "P".
		"""
		return cls(len(frameString) - 1)


	def encode(self):
		return (' ' * self.numBytes) + 'P'



class _TransportKillReason(Constant):
	__slots__ = ()



class TransportKillFrame(object):
	__slots__ = ()

	# Either because no such Stream, or bad credentialsData
	stream_attach_failure = _TransportKillReason("stream_attach_failure")

	# Peer acked strings that we never sent
	acked_unsent_strings = _TransportKillReason("acked_unsent_strings")

	# Peer sent frames that we don't understand
	invalid_frame_type_or_arguments = _TransportKillReason("invalid_frame_type_or_arguments")

	# Peer sent data that could not even be decoded to frames
	# (only applies to some decoders).
	frame_corruption = _TransportKillReason("frame_corruption")

	reasons = (
		stream_attach_failure, acked_unsent_strings,
		 invalid_frame_type_or_arguments, frame_corruption)

	stringToConstant = {}
	constantToString = {}
	for c in reasons:
		stringToConstant[c[BC_VALUE]] = c
		constantToString[c] = c[BC_VALUE]


	def __init__(self, reason):
		"""
		C{reason} is a L{_TransportKillReason}.
		"""
		self.reason = reason


	@classmethod
	def decode(cls, frameString):
		"""
		C{frameString} is a L{StringFragment} that ends with "K".
		"""
		string = str(frameString[:-1])
		try:
			reason = self.stringToConstant[string]
		except KeyError:
			raise InvalidFrame

		return cls(reason)


	def encode(self):
		return self.constantToString[self.reason] + 'K'


# Design note: for frames that carry text, use a non-[A-Za-z] character,
# to avoid accidentally forming words that proxies may block.


lastByteToFrameClass = {
	'~': StringFrame,
	'A': SackFrame,
	'N': SeqNumFrame,
	'H': HelloFrame,
	'!': ResetFrame,
	'P': PaddingFrame,
	'Y': YouCloseItFrame,
	'K': TransportKillFrame,
}

def frameStringToFrame(frameString, isHttp, allowedFrameClasses):
	"""
	C{frameString} is a L{StringFragment}.
	C{isHttp} must be truthy if C{frameString} was received over an HTTP transport.
	C{allowedFrameClasses} is a C{tuple} of allowed frame classes.
	"""
	# Must use slicing, not index, because of StringFragment implementation.
	lastByte = str(frameString[-1:]) # lastByte may be ""
	try:
		frameClass = lastByteToFrameClass[lastByte]
	except KeyError:
		return InvalidFrame("Unknown frame type or 0-length frame")
	if not frameClass in allowedFrameClasses:
		return InvalidFrame("Frame class %r not allowed" % (frameClass,))

	if frameClass == HelloFrame:
		return frameClass.decode(frameString, isHttp)
	else:
		return frameClass.decode(frameString)


# Frames TODO: timestamp, start timestamps, stop timestamps,
# "connect back in N seconds" frame


from pypycpyo import optimizer
optimizer.bind_all_many(vars(), _postImportVars)
