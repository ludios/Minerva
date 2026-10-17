from twisted.trial import unittest

from minerva import objcheck


class StrToNonNegTests(unittest.TestCase):

	def _call(self, s):
		return objcheck.strToNonNeg(s)


	def test_strToNonNeg_okay(self):
		self.assertEqual(0, self._call("0"))
		self.assertEqual(3, self._call("3"))
		self.assertEqual(12390, self._call("12390"))

		# Unicode is valid, too
		self.assertEqual(0, self._call(u"0"))
		self.assertEqual(12390, self._call(u"12390"))


	def test_strToNonNeg_TypeErrors(self):
		self.assertRaises(TypeError, lambda: self._call(None))
		self.assertRaises(TypeError, lambda: self._call([]))
		self.assertRaises(TypeError, lambda: self._call({}))


	def test_strToNonNeg_ValueErrors(self):
		# Empty str is invalid
		self.assertRaises(ValueError, lambda: self._call(""))

		# Anything with a leading zero is invalid
		self.assertRaises(ValueError, lambda: self._call("07"))
		self.assertRaises(ValueError, lambda: self._call("08"))
		self.assertRaises(ValueError, lambda: self._call("09"))
		self.assertRaises(ValueError, lambda: self._call("007"))
		self.assertRaises(ValueError, lambda: self._call("0007"))

		# Anything with non-digit character is invalid
		self.assertRaises(ValueError, lambda: self._call("-7"))
		self.assertRaises(ValueError, lambda: self._call("7e4"))
		self.assertRaises(ValueError, lambda: self._call("7.0"))
		self.assertRaises(ValueError, lambda: self._call("7."))
		self.assertRaises(ValueError, lambda: self._call("0.0"))

		# Hex is rejected
		self.assertRaises(ValueError, lambda: self._call("7f"))
		self.assertRaises(ValueError, lambda: self._call("f7"))



class StrToNonNegLimitTests(StrToNonNegTests):

	def _call(self, s, limit=2**128):
		return objcheck.strToNonNegLimit(s, limit)


	def test_withinLimit(self):
		self.assertEqual(0, self._call("0", 0))
		self.assertEqual(1, self._call("1", 1))
		self.assertEqual(9, self._call("9", 9))
		self.assertEqual(9, self._call("9", 10))
		self.assertEqual(2**32, self._call(str(2**32), 2**32))
		self.assertEqual(2**53, self._call(str(2**53), 2**53))
		self.assertEqual(2**65, self._call(str(2**65), 2**65))


	def test_outsideLimit(self):
		# exercise the first `num > limit:` case
		self.assertRaises(ValueError, lambda: self._call("1", 0))
		self.assertRaises(ValueError, lambda: self._call("9", 8))
		# exercise the `if len(value) > declenlimit:` case
		self.assertRaises(ValueError, lambda: self._call("999999999999999999999", 8))
		# exercise the last `num > limit:` case
		self.assertRaises(ValueError, lambda: self._call(str(2**31), 2**31 - 1))
		self.assertRaises(ValueError, lambda: self._call(str(2**53 + 1), 2**53))
		self.assertRaises(ValueError, lambda: self._call(str(2**65 + 1), 2**65))



class StrToIntInRangeTests(unittest.TestCase):

	def test_strToIntInRange_withinLimit(self):
		self.assertEqual(3, objcheck.strToIntInRange("3", 3, 3))
		self.assertEqual(3, objcheck.strToIntInRange("3", -3, 3))
		self.assertEqual(-3, objcheck.strToIntInRange("-3", -3, 3))
		self.assertEqual(0, objcheck.strToIntInRange("0", 0, 0))


	def test_strToIntInRange_outsideLimit(self):
		self.assertRaises(ValueError, lambda: objcheck.strToIntInRange("-4", -3, 3))
		self.assertRaises(ValueError, lambda: objcheck.strToIntInRange("4", -3, 3))


	def test_strToIntInRange_badNumbers(self):
		self.assertRaises(ValueError, lambda: objcheck.strToIntInRange("1.", -3, 3))
		self.assertRaises(ValueError, lambda: objcheck.strToIntInRange("1.0", -3, 3))
		self.assertRaises(ValueError, lambda: objcheck.strToIntInRange("1.5", -3, 3))
		self.assertRaises(ValueError, lambda: objcheck.strToIntInRange("-0", -3, 3))
		self.assertRaises(ValueError, lambda: objcheck.strToIntInRange("", -3, 3))
		self.assertRaises(ValueError, lambda: objcheck.strToIntInRange("x", -3, 3))
		self.assertRaises(ValueError, lambda: objcheck.strToIntInRange("-", -3, 3))


	def test_strToIntInRange_TypeErrors(self):
		self.assertRaises(TypeError, lambda: objcheck.strToIntInRange(None))
		self.assertRaises(TypeError, lambda: objcheck.strToIntInRange([]))
		self.assertRaises(TypeError, lambda: objcheck.strToIntInRange({}))



class EnsureIntTests(unittest.TestCase):

	def test_ensureInt(self):
		self.assertEqual(0, objcheck.ensureInt(0))
		self.assertEqual(-1, objcheck.ensureInt(-1))
		self.assertEqual(-1, objcheck.ensureInt(-1.0))
		self.assertTrue(isinstance(objcheck.ensureInt(-1.0), int))
		self.assertEqual(0, objcheck.ensureInt(-0.0))
		self.assertTrue(isinstance(objcheck.ensureInt(-0.0), int))
		self.assertEqual(2, objcheck.ensureInt(2.0))
		self.assertTrue(isinstance(objcheck.ensureInt(2.0), int))
		self.assertEqual(200000000000000000000000000, objcheck.ensureInt(200000000000000000000000000))


	def test_ensureIntExceptions(self):
		self.assertRaises(ValueError, lambda: objcheck.ensureInt("0"))
		self.assertRaises(ValueError, lambda: objcheck.ensureInt("-0"))
		self.assertRaises(TypeError, lambda: objcheck.ensureInt({}))
		self.assertRaises(TypeError, lambda: objcheck.ensureInt([]))
		self.assertRaises(TypeError, lambda: objcheck.ensureInt(True))
		self.assertRaises(TypeError, lambda: objcheck.ensureInt(False))



class EnsureNonNegIntTests(unittest.TestCase):

	function = lambda _ignoredSelf, x: objcheck.ensureNonNegInt(x)

	def test_ensureNonNegInt(self):
		for expected, input in [
			(0, 0),
			(0, -0),
			(0, -0.0),
			(2, 2.0),
		]:
			self.assertEqual(expected, input)
			self.assertTrue(isinstance(expected, int))


	def test_ensureNonNegIntExceptions(self):
		self.assertRaises(ValueError, lambda: self.function(0.001))
		self.assertRaises(ValueError, lambda: self.function(-1))
		self.assertRaises(ValueError, lambda: self.function(-1.0))
		self.assertRaises(ValueError, lambda: self.function(-2.0))
		self.assertRaises(ValueError, lambda: self.function(-100000000000000000000000000000))

		self.assertRaises(TypeError, lambda: self.function("0"))
		self.assertRaises(TypeError, lambda: self.function("-0"))
		self.assertRaises(TypeError, lambda: self.function("0.001"))

		self.assertRaises(TypeError, lambda: self.function(True))
		self.assertRaises(TypeError, lambda: self.function(False))

		self.assertRaises(TypeError, lambda: self.function({}))
		self.assertRaises(TypeError, lambda: self.function([]))



class EnsureNonNegIntLimitTests(unittest.TestCase):

	function = lambda _ignoredSelf, x: objcheck.ensureNonNegIntLimit(x, 2**31-1)

	def test_ensureNonNegIntLimitEdgeCase(self):
		self.assertEqual(2**31 - 1, self.function(2**31 - 1))


	def test_ensureNonNegIntLimitExceptionsTooHigh(self):
		self.assertRaises(ValueError, lambda: self.function(2**31))
		self.assertRaises(ValueError, lambda: self.function(2**32))



class EnsureBoolTests(unittest.TestCase):

	def test_True(self):
		for t in (1, 1.0, True):
			self.assertIdentical(True, objcheck.ensureBool(t))


	def test_False(self):
		for f in (0, 0.0, -0.0, False):
			self.assertIdentical(False, objcheck.ensureBool(f))


	def test_ValueError(self):
		for e in (-0.5, -1.00001, 1.0001, [], {}, set(), float('nan'), float('inf')):
			self.assertRaises(ValueError, lambda: objcheck.ensureBool(e))
