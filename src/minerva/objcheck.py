"""
Validation for objects received over the wire.

This entire file is private; you should not need to import it.  If you need
similar validations, copy the code and unit tests.
"""

import sys
import re
from math import log10

_postImportVars = vars().keys()


# Neither of these accept "-0"
_OKAY_NONNEG_INT = re.compile(r'^(0|[1-9]\d*)$')
_OKAY_INT = re.compile(r'^(0|\-?[1-9]\d*)$')

def strToNonNeg(value):
	"""
	A very strict numeric-string to non-zero integer converter.
	This should help prevent people from developing buggy clients
	that just happen to work with our current server.

	We don't use Python's int() because it allows a lot of things,
	including int('-0') and int(' -0').

	Raises C{ValueError} if negative.
	"""
	if _OKAY_NONNEG_INT.match(value):
		return int(value)

	raise ValueError("could not decode to non-negative integer: %r" % (value,))


def strToNonNegLimit(value, limit):
	"""
	Like L{strToNonNeg}, except with a numerical limit C{limit}.

	Raises C{ValueError} if too high (or negative).
	"""
	# Optimizations for the common case
	if limit == 2**53:
		declenlimit = 16
	elif limit == 2**31 - 1:
		declenlimit = 10
	else:
		declenlimit = int(log10(limit) + 1) if limit != 0 else 1

	if len(value) > declenlimit:
		raise ValueError("too high")

	if _OKAY_NONNEG_INT.match(value):
		num = int(value)
		if num > limit:
			raise ValueError("too high")
		return num

	raise ValueError("could not decode to non-negative integer: %r" % (value,))


def strToIntInRange(value, lower, upper):
	"""
	A very strict numeric-string to integer converter.

	@rtype: L{int} or L{long}
	@return: C{value} as converted from a str to an int/long.

	Raises C{ValueError} if too high or too low.
	"""
	if _OKAY_INT.match(value):
		num = int(value)
	else:
		raise ValueError("value %r does not look numeric" % (value,))

	if not lower <= num <= upper:
		raise ValueError("value %r not in range [%r, %r]" % (value, lower, upper))

	return num


def ensureInt(value):
	"""
	Convert C{value} from a L{float} to an equivalent L{int}/L{long} if
	possible, else raise L{ValueError}.  C{int}s and C{long}s pass through.

	@rtype: L{int} or L{long}
	@return: non-float equivalent of C{value}
	"""
	if value is True or value is False:
		raise TypeError("Even though int(False) and int(True) work, we disallow it.")
	inted = int(value)
	if inted != value:
		raise ValueError("%r cannot be converted to identical integer" % (value,))
	return inted


def ensureNonNegInt(value):
	"""
	Check that C{value} is non-negative and convert it to it an equivalent
	non-L{float} if necessary, else raise L{ValueError}.

	@rtype: L{int} or L{long}
	@return: non-float equivalent of C{value}

	Useful after getting some deserialized JSON with random stuff in it.
	"""

	if isinstance(value, (int, long, float)) and value is not True and value is not False:
		if value < 0:
			raise ValueError("%r is < 0" % (value,))
		elif isinstance(value, float):
			return ensureInt(value)
		else:
			return value
	else:
		raise TypeError("%r is not an int/long/float" % (value,))


def ensureNonNegIntLimit(value, limit):
	"""
	Check that C{value} is non-negative and C{<= limit} and
	convert it to it an equivalent non-L{float} if necessary, else raise L{ValueError}.

	@rtype: L{int} or L{long}
	@return: non-float equivalent of C{value}

	Useful after getting some deserialized JSON with random stuff in it.
	"""
	v = ensureNonNegInt(value)
	if v > limit:
		raise ValueError("%r is > limit %r" % (value, limit))
	return v


def ensureBool(value):
	"""
	Convert 1, 1.0, and True to True.
	Convert 0, 0.0, -0.0, and False to False.
	For all other values, raise L{ValueError}.

	@rtype: L{bool}
	@return: non-number equivalent of C{value}

	This is useful when getting JSON-decoded values from a peer, and you
	do not want to keep their bool-equivalent numbers around in memory.
	"""
	if value == True:
		return True
	elif value == False:
		return False
	else:
		raise ValueError("%r is not bool-equivalent to True or False" % (value,))



try: from refbinder.api import bindRecursive
except ImportError: pass
else: bindRecursive(sys.modules[__name__], _postImportVars)
