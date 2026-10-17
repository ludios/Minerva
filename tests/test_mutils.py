from twisted.trial import unittest
from securetypes import securedict

from minerva.mutils import htmldumps, strictSecureDecodeJson, StrictDecodeError


class TestHtmlDumps(unittest.TestCase):

	def test_htmldumps(self):
		self.assertEqual(r'["<\/script>"]', htmldumps(["</script>"]))



class TestStrictSecureDecodeJson(unittest.TestCase):

	def test_usesSecuredict(self):
		out = strictSecureDecodeJson('{"a": {}}')
		self.assertEqual(securedict({"a": securedict()}), out)
		self.assertTrue(isinstance(out, securedict), type(out))
		self.assertTrue(isinstance(out["a"], securedict), type(out))


	def test_rejectsNanInf(self):
		self.assertRaises(StrictDecodeError, lambda: strictSecureDecodeJson('[NaN]'))
		self.assertRaises(StrictDecodeError, lambda: strictSecureDecodeJson('[Infinity]'))
		self.assertRaises(StrictDecodeError, lambda: strictSecureDecodeJson('[-Infinity]'))


	def test_rejectsTrailingBytes(self):
		self.assertRaises(StrictDecodeError, lambda: strictSecureDecodeJson('{"a": {}} '))
		self.assertRaises(StrictDecodeError, lambda: strictSecureDecodeJson('{"a": {}}\n'))
		self.assertRaises(StrictDecodeError, lambda: strictSecureDecodeJson('347681x'))
		self.assertEqual(347681, strictSecureDecodeJson('347681'))
