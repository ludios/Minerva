from twisted.trial import unittest

import _protocols


class DummyNetStringDecoder(_protocols.NetStringDecoder):

	def __init__(self):
		self.gotStrings = []


	def dataCallback(self, line):
		self.gotStrings.append(line)



class DummyBencodeStringDecoder(_protocols.BencodeStringDecoder):

	def __init__(self):
		self.gotStrings = []


	def dataCallback(self, line):
		self.gotStrings.append(line)



# modified copy/paste from twisted.test.test_protocols
class NetStringDecoderTestCase(unittest.TestCase):

	# for max length 699
	strings = ['hello', 'world', 'how', 'are', 'you123', ':today', "a"*515]

	# for max length 50
	illegalSequences = [
		'9999999999999999999999', 'abc', '4:abcde',
		'51:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab,',]

	trailingComma = ','

	receiver = DummyNetStringDecoder

	def test_buffer(self):
		"""
		Test that when strings are received in chunks of different lengths,
		they are still parsed correctly.
		"""
		out = ''
		for s in self.strings:
			out += str(len(s))+':'+s+self.trailingComma

		for packet_size in range(1, 20):
			##print "packet_size", packet_size
			a = self.receiver()
			a.MAX_LENGTH = 699

			for i in range(len(out)/packet_size + 1):
				s = out[i*packet_size:(i+1)*packet_size]
				if s != '':
					##print 'sending', repr(s)
					a.dataReceived(s)

			self.assertEquals(''.join(a.gotStrings), ''.join(self.strings))


	def test_illegal(self):
		"""
		Assert that illegal strings raise a ParseError.

		This is basically redundant with L{test_illegalWithPacketSizes}
		but keep it anyway for debugging.
		"""
		for s in self.illegalSequences:
			a = self.receiver()
			a.MAX_LENGTH = 50
			##print 'Sending', repr(s)
			self.assertRaises(_protocols.ParseError, lambda s=s: a.dataReceived(s))


	def test_illegalWithPacketSizes(self):
		"""
		Assert that illegal strings raise a ParseError,
		even when they arrive in variable packet sizes.
		"""

		def sendData(a, sequence, packet_size):
			for i in range(len(sequence)/packet_size + 1):
				s = sequence[i*packet_size:(i+1)*packet_size]
				if s != '':
					##print 'sending', repr(s)
					a.dataReceived(s)


		for sequence in self.illegalSequences:
			for packet_size in range(1, 2):

				##print 'packet_size', packet_size

				a = self.receiver()
				a.MAX_LENGTH = 50

				##print 'Sending in pieces', repr(sequence)

				self.assertRaises(
					_protocols.ParseError,
					lambda: sendData(a, sequence, packet_size)
				)



class BencodeStringDecoderTestCase(NetStringDecoderTestCase):

	# for max length 50
	illegalSequences = [
		'9999999999999999999999', 'abc', '4:abcde',
		'51:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab',]

	trailingComma = ''

	receiver = receiver = DummyBencodeStringDecoder
