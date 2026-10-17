import struct

from twisted.trial import unittest

from strfrag import StringFragment
from minerva import decoders



def diceString(toSend, packetSize):
	assert isinstance(toSend, str), type(toSend)
	assert isinstance(packetSize, (int, long)), type(packetSize)
	pieces = []
	for i in range(len(toSend)/packetSize + 1):
		s = toSend[i*packetSize:(i+1)*packetSize]
		if s != '':
			pieces.append(s)
	return pieces


assert diceString("hello", 1) == list("hello")
assert diceString("hello", 2) == ["he", "ll", "o"]
assert diceString("hello", 3) == ["hel", "lo"]
assert diceString("hello", 4) == ["hell", "o"]
assert diceString("hello", 5) == ["hello"]
assert diceString("hello", 6) == ["hello"]


class _BaseRecording(object):

	def __init__(self):
		super(_BaseRecording, self).__init__()
		self.got = []


	def manyDataCallback(self, data):
		self.got.extend(data)



def fragmentsToStr(various):
	"""
	Convert all StringFragment to str if necessary.
	"""
	newList = []
	for s in various:
		if isinstance(s, StringFragment):
			newList.append(str(s))
		else:
			newList.append(s)
	return newList


def fstValueToStrs(tup):
	fst, snd = tup
	fst = fragmentsToStr(fst)
	return (fst, snd)


class CommonTests(object):

	def test_buffer(self):
		"""
		Test that when strings are received in chunks of different lengths,
		they are still parsed correctly.
		"""
		toSend = ''
		for s in self.strings:
			toSend += self.receiver.encode(s)

		for packetSize in range(1, 20):
			##print "packetSize", packetSize
			a = self.receiver(maxLength=699)
			got = []

			for s in diceString(toSend, packetSize):
				##print 'sending', repr(s)
				out, code = a.getNewFrames(s)
				self.assertEqual(decoders.OK, code)
				got.extend(out)

			got = fragmentsToStr(got)
			self.assertEqual(self.strings, got)


	def test_illegalWithPacketSizes(self):
		"""
		Assert that illegal strings return the correct error code
		even when they arrive in variable packet sizes.
		"""
		def sendData(a, sequence, packetSize):
			got = []
			for s in diceString(sequence, packetSize):
				##print repr(s)
				out, code = a.getNewFrames(s)
				got.extend(out)
				if code != decoders.OK:
					return got, code
			return got, code

		for sequences, expectedCode in (
			(self.tooLongSequences, decoders.TOO_LONG),
		):
			##print sequences
			for sequence in sequences:
				##print sexpectedCode
				for packetSize in range(1, 20):
					a = self.receiver(maxLength=50)

					##print 'Sending in pieces', repr(sequence), 'packetSize=', packetSize
					out, code = sendData(a, sequence, packetSize)
					self.assertEqual(expectedCode, code)



class DelimitedStringDecoderTests(CommonTests, unittest.TestCase):
	receiver = decoders.DelimitedStringDecoder

	# For maxLength == 50
	tooLongSequences = [
		'%s\n' % ("x" * 51),
	]

	strings = ['', 'hello', 'world', 'how', 'are', 'you123']

	def test_encode(self):
		self.assertEqual('\n', self.receiver.encode(""))
		self.assertEqual('h\n', self.receiver.encode("h"))
		self.assertEqual('a longer string\n', self.receiver.encode("a longer string"))
		# It does not check if string-to-send contains the delimiter;
		# it assumes it is safe.
		self.assertEqual('\n\n', self.receiver.encode("\n"))


	def test_bufferSizeLimit(self):
		"""
		If 200 bytes of data are delivered, and maxLength is 9, and data
		has delimiter at every 10th byte, the strings are extracted without
		a TOO_LONG error code.
		"""
		strings = []
		for i in xrange(20):
			strings.append(chr(65+i) * 7)

		toSend = ''
		for s in strings:
			toSend += '%s\n' % s

		a = self.receiver(maxLength=10)
		got, code = a.getNewFrames(toSend)
		got = fragmentsToStr(got)
		self.assertEqual((strings, decoders.OK), (got, code))


	def test_someDocumentsParsedButRemainingBufferTooLong(self):
		"""
		If some lines can be extracted but the remaining buffer is too long,
		the parser returns those lines and returns TOO_LONG.
		"""
		toSend = 'hello\nthere\n8chars'
		a = self.receiver(maxLength=5)
		strings = ['hello', 'there']
		got, code = a.getNewFrames(toSend)
		got = fragmentsToStr(got)
		self.assertEqual((strings, decoders.TOO_LONG), (got, code))



class Int32StringDecoderTests(CommonTests, unittest.TestCase):

	receiver = decoders.Int32StringDecoder
	strings = ["", "a", "b" * 16, "c" * 17, "d" * 255, "e" * 256]
	partialStrings = ["\x00\x00\x00\xffhello there"]
	tooLongSequences = ["\xff\x00\x00\x00XX", "\xff\xff\xff\xffXX"]

	def test_receive(self):
		"""
		Test receiving data find the same data send.
		"""
		r = self.receiver(maxLength=20*1024*1024)
		got = []
		for s in self.strings:
			for c in struct.pack(r.structFormat, len(s)) + s:
				out, code = fstValueToStrs(r.getNewFrames(c))
				self.assertEqual(decoders.OK, code)
				got.extend(out)
		self.assertEqual(self.strings, got)


	def test_zeroLengthString(self):
		"""
		0-length strings are okay and should be delivered when the
		fourth byte of the prefix arrives.
		"""
		r = self.receiver(maxLength=0)
		self.assertEqual(([], decoders.OK), r.getNewFrames('\x00'))
		self.assertEqual(([], decoders.OK), r.getNewFrames('\x00'))
		self.assertEqual(([], decoders.OK), r.getNewFrames('\x00'))
		self.assertEqual(([''], decoders.OK), fstValueToStrs(r.getNewFrames('\x00')))


	def test_partial(self):
		"""
		Send partial data, nothing should be definitely received.
		"""
		for s in self.partialStrings:
			##print repr(s)
			r = self.receiver(maxLength=20*1024*1024)
			got = []
			for c in s:
				##print repr(s), repr(c)
				out, code = r.getNewFrames(c)
				self.assertEqual(decoders.OK, code)
			self.assertEqual([], got)


	def test_encode(self):
		value = decoders.Int32StringDecoder.encode("b" * 16)
		self.assertEqual(value, struct.pack(decoders.Int32StringDecoder.structFormat, 16) + "b" * 16)


	def test_encode32(self):
		"""
		Test specific behavior of the 32-bits length.
		"""
		value = decoders.Int32StringDecoder.encode("foo")
		self.assertEqual(value, "\x00\x00\x00\x03foo")


	def test_decode32(self):
		r = self.receiver(maxLength=10)
		got, code = fstValueToStrs(r.getNewFrames("\x00\x00\x00\x04ubar"))
		self.assertEqual(decoders.OK, code)
		self.assertEqual(["ubar"], got)


	def test_encodeTooLong(self):
		"""
		We can't test Int32StringDecoder's StringTooLongError
		with a 32-bit Python, because returning 2**31 + 1 from a __len__
		in 32-bit Python results in an OverflowError, as it cannot convert the long.
		"""
		class Int16StringDecoder(decoders.IntNStringDecoder):
			__slots__ = ()

			structFormat = "!H"
			prefixLength = struct.calcsize(structFormat)
			maxPossibleLength = 2 ** (8 * prefixLength)

			assert maxPossibleLength == 65536

		s = 'x' * (65536 + 1)

		self.assertRaises(decoders.StringTooLongError, lambda: Int16StringDecoder.encode(s))

	
	def test_lengthLimitExceeded(self):
		r = self.receiver(maxLength=10)
		out, code = r.getNewFrames(struct.pack(r.structFormat, 11))
		self.assertEqual([], out)
		self.assertEqual(decoders.TOO_LONG, code)
	
	
	def test_longStringNotDelivered(self):
		"""
		If a length prefix for a string longer than C{maxLength} is delivered
		to C{getNewFrames} at the same time as the entire string, the string is
		not passed to C{manyDataCallback}.
		"""
		r = self.receiver(maxLength=10)
		out, code = r.getNewFrames(struct.pack(r.structFormat, 11) + 'x' * 11)
		self.assertEqual([], out)
		self.assertEqual(decoders.TOO_LONG, code)


	def test_lengthCheckedAtFourthByte(self):
		r = self.receiver(maxLength=10)
		self.assertEqual(([], decoders.OK), r.getNewFrames('\xff')) # although this indicates a really long string, the length isn't looked at until 4 bytes arrive.
		self.assertEqual(([], decoders.OK), r.getNewFrames('\x00'))
		self.assertEqual(([], decoders.OK), r.getNewFrames('\x00'))
		self.assertEqual(([], decoders.TOO_LONG), r.getNewFrames('\x00'))
