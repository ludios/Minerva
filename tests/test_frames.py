import simplejson

from twisted.trial import unittest

from strfrag import StringFragment

from minerva.frames import (
	HelloFrame, StreamCreatedFrame, StringFrame, SeqNumFrame,
	SackFrame, StreamStatusFrame, YouCloseItFrame, ResetFrame, CommentFrame,
	TransportKillFrame, InvalidFrame, InvalidHello, CannotEncode,
	decodeFrameFromClient, decodeFrameFromServer)

from minerva.frames import (
	FORMAT_XHR, FORMAT_HTMLFILE,
)

from minerva.window import SACK
from minerva.test_mserver import _makeHelloFrame, sf


class ReallyEqualMixin(object):
	"""
	A mixin for your L{unittest.TestCase}s to better test object equality
	and inequality.  Details at:

	http://ludios.org/ivank/2010/10/testing-your-eq-ne-cmp/
	"""
	def assertReallyEqual(self, a, b):
		# assertEqual first, because it will have a good message if the
		# assertion fails.
		self.assertEqual(a, b)
		self.assertEqual(b, a)
		self.assertTrue(a == b)
		self.assertTrue(b == a)
		self.assertFalse(a != b)
		self.assertFalse(b != a)
		self.assertEqual(0, cmp(a, b))
		self.assertEqual(0, cmp(b, a))


	def assertReallyNotEqual(self, a, b):
		# assertNotEqual first, because it will have a good message if the
		# assertion fails.
		self.assertNotEqual(a, b)
		self.assertNotEqual(b, a)
		self.assertFalse(a == b)
		self.assertFalse(b == a)
		self.assertTrue(a != b)
		self.assertTrue(b != a)
		self.assertNotEqual(0, cmp(a, b))
		self.assertNotEqual(0, cmp(b, a))



DeleteProperty = ("DeleteProperty",)


def dumpToJson7Bit(data):
	return simplejson.dumps(data, separators=(',', ':'), allow_nan=False)


class HelloFrameTests(unittest.TestCase, ReallyEqualMixin):
	disableSpeedups = False

	def setUp(self):
		if self.disableSpeedups:
			simplejson._toggle_speedups(False)
			assert isinstance(simplejson.loads('"x"'), unicode)


	def tearDown(self):
		if self.disableSpeedups:
			simplejson._toggle_speedups(True)


	def test_eq(self):
		for a, b in [
			(HelloFrame({"a": 1}), HelloFrame({"a": 1})),
		]:
			self.assertReallyEqual(a, b)

		for a, b in [
			(HelloFrame({"a": 1}), HelloFrame({"a": 2})),
			(HelloFrame({"a": 1}), HelloFrame({"a": 1, "b": 1})),
			(HelloFrame({"a": 1}), None),
		]:
			self.assertReallyNotEqual(a, b)


	def test_publicAttr(self):
		self.assertEqual("goes", HelloFrame({"anything": "goes"}).anything)


	def test_repr(self):
		self.assertEqual("HelloFrame({'a': 1})", repr(HelloFrame({'a': 1})))


	def test_wantsStrings(self):
		s = _makeHelloFrame()
		self.assertEqual(False, s.wantsStrings())
		s.succeedsTransport = None
		self.assertEqual(True, s.wantsStrings())
		s.succeedsTransport = 3
		self.assertEqual(True, s.wantsStrings())
		del s.succeedsTransport
		self.assertEqual(False, s.wantsStrings())


	def test_decode(self):
		s = _makeHelloFrame().encode()
		self.assertEqual(
			HelloFrame(dict(
				transportNumber=0,
				requestNewStream=True,
				protocolVersion=2,
				streamId='x'*26,
				streamingResponse=True,
				maxReceiveBytes=2**30,
				maxOpenTime=2**30,
				maxInactivity=0,
				needPaddingBytes=0,
				httpFormat=None,
				sack=None,
				lastSackSeenByClient=SACK(-1, ()))),
			HelloFrame.decode(sf(s)))


	def test_decodeFailedBadEedsArgument(self):
		"""
		A too-low or too-high transport number (or a wrong type) for the 'eeds'
		argument causes L{InvalidHello} to be raised.
		In this case, the stream is never registered with the streamTracker.
		"""
		for succeedsTransport in [-1, -2**32, -0.5, 2**53+1, "4", True, False, [], {}]:
			s = _makeHelloFrame(dict(
				succeedsTransport=succeedsTransport)).encode()

			self.assertRaises(InvalidHello, lambda: HelloFrame.decode(sf(s)))


	def test_decodeFailedTooMuchNestingObject(self):
		"""
		If the L{HelloFrame} has too much nesting of objects,
		L{InvalidHello} is raised.
		"""
		level = 20000
		s = '{"":' * level + '1' + '}' * level
		self.assertRaises(InvalidHello, lambda: HelloFrame.decode(sf(s)))


	def test_decodeFailedTooMuchNestingArray(self):
		"""
		If the L{HelloFrame} has too much nesting of arrays,
		L{InvalidHello} is raised.
		"""
		level = 20000
		s = '[' * level + '1' + ']' * level
		self.assertRaises(InvalidHello, lambda: HelloFrame.decode(sf(s)))


	def test_decodeFailedTrailingGarbage(self):
		"""
		If L{HelloFrame} has trailing garbage 'x' after the JSON,
		L{InvalidHello} is raised.
		"""
		s = _makeHelloFrame().encode()[:-1] + 'x' + 'H'
		self.assertRaises(InvalidHello, lambda: HelloFrame.decode(sf(s)))


	def test_decodeFailed_nan_inf_neginf(self):
		"""
		If L{HelloFrame} contains NaN, Infinity, or -Infinity,
		L{InvalidHello} is raised.
		"""
		for bad in (float('nan'), float('inf'), float('-inf')):
			hello = _makeHelloFrame(dict(transportNumber=bad))
			s = simplejson.dumps(dict(hello._yieldMapping()))
			self.assertRaises(InvalidHello, lambda: HelloFrame.decode(sf(s)))


	def test_decodeFailedInvalidValues(self):
		"""
		If L{HelloFrame} contains invalid values for various properties,
		L{InvalidHello} is raised.
		"""
		def listWithout(oldList, without):
			arr = oldList[:]
			for w in without:
				arr.remove(w)
			return arr

		genericBad = [
			-2**65, -1, -0.5, 0.5, 2**53+1, "", [], ["something"],
			{}, True, False, None]

		badMutations = dict(
			transportNumber=[DeleteProperty] + genericBad,
			protocolVersion=[DeleteProperty, 0, 1, "1", 1.001] + genericBad,
			streamId=[
				DeleteProperty, '', '\x00', 'x'*1, u'\ucccc'*25, u'\ucccc'*8,
				u'\x80'*25, 'x'*19, 'x'*31, 'x'*3000] + genericBad, # 19 is below limit, 31 is over limit
			httpFormat=[4, 1, 0] + genericBad,
			streamingResponse=[2, 3] + listWithout(genericBad, [True, False]),
			maxReceiveBytes=genericBad,
			maxOpenTime=genericBad,
			maxInactivity=[None, 0.5, 1.5, 601],
			# We can pass either a string or a SACK
			sack=['', '|', SACK(-2, ()), SACK(-1, (-2,))],
			lastSackSeenByClient=[DeleteProperty, '', '|', SACK(-2, ()), SACK(-1, (-2,))],
		)
		##print badMutations

		ran = 0

		for mutateProperty, mutateValues in badMutations.iteritems():
			for value in mutateValues:
				badHello = _makeHelloFrame()
				if value is not DeleteProperty:
					setattr(badHello, mutateProperty, value)
				else:
					try:
						delattr(badHello, mutateProperty)
					except AttributeError:
						 # It wasn't there in the first place.
						pass

				##print badHello
				s = badHello.encode()
				self.assertRaises(InvalidHello, lambda: HelloFrame.decode(sf(s)))

				ran += 1

		# sanity check; make sure we actually tested things
		assert ran == 116, "Ran %d times; change this assert as needed" % (ran,)


	def test_encode(self):
		hello = HelloFrame(dict(transportNumber=0))
		self.assertEqual('{"tnum":0}' + 'H', hello.encode())


	def test_encodeDecodeEquality(self):
		# Need to make some options explicit for equality to work
		hello = _makeHelloFrame(dict(
			httpFormat=FORMAT_XHR,
			# for equality in JS, need boolean instead of number.  Do the
			# same here for consistency.
			requestNewStream=True,
			streamingResponse=True,
			needPaddingBytes=0,
			maxInactivity=1,
			sack=SACK(-1, ())))
		encodedDecodedHello = HelloFrame.decode(sf(hello.encode()))
		self.assertEqual(hello, encodedDecodedHello)


	def test_encodeFailed(self):
		hello = HelloFrame(dict(aMadeUpKey=0))
		self.assertRaises(CannotEncode, lambda: hello.encode())



class HelloFrameTestsNoSpeedups(HelloFrameTests):
	disableSpeedups = True



class StringFrameTests(unittest.TestCase):

	def test_eq(self):
		self.assertEqual(StringFrame("Hello"), StringFrame("Hello"))
		self.assertNotEqual(StringFrame("Hello"), StringFrame("Hello2"))
		self.assertEqual(StringFrame(StringFragment("Hello", 0, 5)), StringFrame("Hello"))


	def test_publicAttr(self):
		self.assertEqual(StringFragment("Hello", 0, 5), StringFrame("Hello").string)


	def test_repr(self):
		self.assertEqual("StringFrame('Hello')", repr(StringFrame("Hello")))


	def test_decode(self):
		s = '\x00unchecked\xfftext' + ' '
		self.assertEqual(
			StringFrame(StringFragment(s, 0, len(s) - 1)),
			StringFrame.decode(sf(s)))


	def test_encode(self):
		s = '\x00unchecked\xfftext'
		self.assertEqual(s + ' ', StringFrame(sf(s)).encode())



class CommentFrameTests(unittest.TestCase):

	def test_eq(self):
		self.assertEqual(CommentFrame("Hello"), CommentFrame("Hello"))
		self.assertNotEqual(CommentFrame("Hello"), CommentFrame("Hello2"))


	def test_publicAttr(self):
		self.assertEqual("Hello", CommentFrame("Hello").comment)


	def test_repr(self):
		self.assertEqual("CommentFrame('Hello')", repr(CommentFrame("Hello")))


	def test_decode(self):
		s = '\x00unchecked\xfftext' + '^'
		self.assertEqual(
			CommentFrame(s[:-1]),
			CommentFrame.decode(sf(s)))


	def test_encode(self):
		s = '\x00unchecked\xfftext'
		self.assertEqual(s + '^', CommentFrame(sf(s)).encode())



class SeqNumFrameTests(unittest.TestCase):

	def test_eq(self):
		self.assertEqual(SeqNumFrame(2), SeqNumFrame(2))
		self.assertNotEqual(SeqNumFrame(2), SeqNumFrame(3))


	def test_publicAttr(self):
		self.assertEqual(2, SeqNumFrame(2).seqNum)


	def test_repr(self):
		self.assertEqual("SeqNumFrame(2)", repr(SeqNumFrame(2)))
		self.assertEqual("SeqNumFrame(%d)" % 2**53, repr(SeqNumFrame(2**53)))


	def test_decode(self):
		for seqNum in (0, 1, 2**32, 2**53):
			s = str(seqNum) + 'N'
			self.assertEqual(
				SeqNumFrame(seqNum),
				SeqNumFrame.decode(sf(s)))


	def test_decodeFailed(self):
		for s in (str(-1) + 'N', str(-2**53) + 'N', str(2**53 + 1) + 'N', ' ', '00' + 'N', '0' * 1024):
			self.assertRaises(
				InvalidFrame,
				lambda: SeqNumFrame.decode(sf(s)))


	def test_encode(self):
		self.assertEqual('2N', SeqNumFrame(2).encode())
		self.assertEqual('0N', SeqNumFrame(0).encode())
		self.assertEqual('%dN' % 2**53, SeqNumFrame(2**53).encode())



class SackFrameTests(unittest.TestCase):

	def test_eq(self):
		self.assertEqual(SackFrame(SACK(2, ())), SackFrame(SACK(2, ())))
		self.assertNotEqual(SackFrame(SACK(2, (1,))), SackFrame(SACK(3, (2,))))
		self.assertNotEqual(SackFrame(SACK(2, ())), SackFrame(SACK(3, ())))


	def test_publicAttr(self):
		self.assertEqual(SACK(2, (4, 5)), SackFrame(SACK(2, (4, 5))).sack)
		self.assertEqual(2, SackFrame(SACK(2, (4, 5))).sack.ackNumber)
		self.assertEqual((4, 5), SackFrame(SACK(2, (4, 5))).sack.sackList)


	def test_repr(self):
		self.assertEqual("SackFrame(SACK(2, (1, 4)))", repr(SackFrame(SACK(2, (1, 4)))))


	def test_decode(self):
		for ackNum in (-1, 0, 1, 2**53):
			s = '1,4|%sA' % (ackNum,)
			self.assertEqual(
				SackFrame(SACK(ackNum, (1, 4))),
				SackFrame.decode(sf(s)))


	def test_decodeNoSackNumbers(self):
		s = '|%sA' % (2**53,)
		self.assertEqual(
			SackFrame(SACK(2**53, ())),
			SackFrame.decode(sf(s)))


	def test_decodeFailedAckNumberInvalid(self):
		for badNum in (2**53+1, -2, -1.01, 0.5, 1.5):
			s = '1,4|%sA' % (badNum,)
			self.assertRaises(
				InvalidFrame,
				lambda: SackFrame.decode(sf(s)))


	def test_decodeFailedOneSackNumberInvalid(self):
		for badNum in (2**53+1, -1, 0.5, 1.5):
			s = '1,%s|4A' % (badNum,)
			self.assertRaises(
				InvalidFrame,
				lambda: SackFrame.decode(sf(s)))


	def test_decodeFailedAtSplit(self):
		for s in ('||4A', '', ' ', '|'):
			self.assertRaises(
				InvalidFrame,
				lambda: SackFrame.decode(sf(s)))


	def test_encode(self):
		self.assertEqual('1,4|2A', SackFrame(SACK(2, (1, 4))).encode())
		self.assertEqual('4|2A', SackFrame(SACK(2, (4,))).encode())
		self.assertEqual('|2A', SackFrame(SACK(2, ())).encode())



class StreamStatusFrameTests(unittest.TestCase):
	"""
	StreamStatusFrame is roughly equivalent to SackFrame, so we omit
	many of the tests.
	"""
	def test_eq(self):
		self.assertEqual(StreamStatusFrame(SACK(2, ())), StreamStatusFrame(SACK(2, ())))
		self.assertNotEqual(StreamStatusFrame(SACK(2, ())), StreamStatusFrame(SACK(3, ())))


	def test_publicAttr(self):
		self.assertEqual(SACK(2, (4, 5)), StreamStatusFrame(SACK(2, (4, 5))).lastSackSeen)


	def test_repr(self):
		self.assertEqual("StreamStatusFrame(SACK(2, (1, 4)))", repr(StreamStatusFrame(SACK(2, (1, 4)))))


	def test_decode(self):
		for ackNum in (-1, 0, 1, 2**53):
			s = '1,4|%sT' % (ackNum,)
			self.assertEqual(
				StreamStatusFrame(SACK(ackNum, (1, 4))),
				StreamStatusFrame.decode(sf(s)))


	def test_encode(self):
		self.assertEqual('1,4|2T', StreamStatusFrame(SACK(2, (1, 4))).encode())



class StreamCreatedFrameTests(unittest.TestCase):

	def test_eq(self):
		self.assertEqual(StreamCreatedFrame(), StreamCreatedFrame())
		self.assertNotEqual(StreamCreatedFrame(), ())


	def test_repr(self):
		self.assertEqual("StreamCreatedFrame()", repr(StreamCreatedFrame()))


	def test_decode(self):
		s = 'C'
		self.assertEqual(
			StreamCreatedFrame(),
			StreamCreatedFrame.decode(sf(s)))


	def test_decodeFailed(self):
		s = 'extra stuff' + 'C'
		self.assertRaises(
			InvalidFrame,
			lambda: StreamCreatedFrame.decode(sf(s)))


	def test_encode(self):
		self.assertEqual('C', StreamCreatedFrame().encode())



class YouCloseItFrameTests(unittest.TestCase):

	def test_eq(self):
		self.assertEqual(YouCloseItFrame(), YouCloseItFrame())
		self.assertNotEqual(YouCloseItFrame(), ())


	def test_repr(self):
		self.assertEqual("YouCloseItFrame()", repr(YouCloseItFrame()))


	def test_decode(self):
		s = 'Y'
		self.assertEqual(
			YouCloseItFrame(),
			YouCloseItFrame.decode(sf(s)))


	def test_decodeFailed(self):
		s = 'extra stuff' + 'Y'
		self.assertRaises(
			InvalidFrame,
			lambda: YouCloseItFrame.decode(sf(s)))


	def test_encode(self):
		self.assertEqual('Y', YouCloseItFrame().encode())



class ResetFrameTests(unittest.TestCase):

	def test_eq(self):
		self.assertEqual(ResetFrame("why", True), ResetFrame("why", True))
		self.assertNotEqual(ResetFrame("why", True), ResetFrame("why", False))
		self.assertNotEqual(ResetFrame("why2", True), ResetFrame("why", True))


	def test_publicAttr(self):
		self.assertEqual("why", ResetFrame("why", True).reasonString)
		self.assertEqual(True, ResetFrame("why", True).applicationLevel)


	def test_repr(self):
		self.assertEqual("ResetFrame('why', True)", repr(ResetFrame("why", True)))


	def test_encode(self):
		self.assertEqual('the reason|0!', ResetFrame("the reason", False).encode())
		self.assertEqual('the reason|1!', ResetFrame("the reason", True).encode())


	def test_decode(self):
		for applicationLevel in (True, False):
			for reasonString in ('the reason', 'the | | reason', '', '|', '||'):
				s = reasonString + '|' + str(int(applicationLevel)) + '!'
				self.assertEqual(
					ResetFrame(reasonString, applicationLevel),
					ResetFrame.decode(sf(s)))


	def test_decodeFailedBadReason(self):
		s = '\x7freason|0!'
		self.assertRaises(
			InvalidFrame,
			lambda: ResetFrame.decode(sf(s)))


	def test_decodeFailedBadBoolean(self):
		s = 'reason|2!'
		self.assertRaises(
			InvalidFrame,
			lambda: ResetFrame.decode(sf(s)))



tk = TransportKillFrame

class TransportKillFrameTests(unittest.TestCase):

	def test_eq(self):
		self.assertEqual(
			TransportKillFrame(tk.stream_attach_failure),
			TransportKillFrame(tk.stream_attach_failure))
		self.assertNotEqual(
			TransportKillFrame(tk.stream_attach_failure),
			TransportKillFrame(tk.acked_unsent_strings))


	def test_publicAttr(self):
		self.assertEqual(
			tk.acked_unsent_strings,
			TransportKillFrame(tk.acked_unsent_strings).reason)


	def test_repr(self):
		self.assertEqual(
			"TransportKillFrame('frame_corruption')",
			repr(TransportKillFrame(tk.frame_corruption)))


	def test_encode(self):
		self.assertEqual('frame_corruptionK', TransportKillFrame(tk.frame_corruption).encode())


	def test_decode(self):
		for reason in tk.allReasons:
			s = reason + 'K'
			self.assertEqual(
				TransportKillFrame(reason),
				TransportKillFrame.decode(sf(s)))


	def test_decodeFailed(self):
		s = 'not_a_reasonK'
		self.assertRaises(
			InvalidFrame,
			lambda: TransportKillFrame.decode(sf(s)))


# TODO: add direct tests for decodeFrameFromClient, decodeFrameFromServer
