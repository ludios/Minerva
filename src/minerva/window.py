"""
Incoming and outgoing frame windows used by Minerva, analogous to TCP windows.

This entire file is private; you should not need to import it.
"""

import sys
import operator

from strfrag import StringFragment

_postImportVars = vars().keys()


class SACK(tuple):
	"""
	Represents a SACK.
	"""
	__slots__ = ()
	_MARKER = object()

	ackNumber = property(operator.itemgetter(1))
	sackList = property(operator.itemgetter(2))

	def __new__(cls, ackNumber, sackList):
		"""
		C{ackNumber} is an C{int} or C{long}.
		C{sackList} is a tuple of C{int}s and C{long}s.
		"""
		assert not isinstance(sackList, list)
		return tuple.__new__(cls, (cls._MARKER, ackNumber, sackList))


	def __repr__(self):
		return '%s(%d, %r)' % (self.__class__.__name__, self[1], self[2])



def totalSizeOf(s):
	"""
	@type s: C{str} or L{StringFragment}

	@return An estimate of how much memory (in bytes) string C{s} consumes.
	@rtype: C{int}
	"""
	return 30 + len(s)


class Queue(object):
	"""
	A send queue which assigns a monotonically increasing integer
	to each string.  It keeps each string until it is SACKed.

	Useful if you need to queue strings that may need to be sent
	multiple times (if a connection/transport fails).  It keeps track
	of how much memory the Queue is using, in case you want to
	do flow control.
	"""
	__slots__ = ('_counter', '_items', '_size')

	def __init__(self):
		self._counter = -1
		self._items = {}
		self._size = 0


	def append(self, item):
		size = totalSizeOf(item)
		self._items[self._counter + 1] = (item, size)
		self._counter += 1
		self._size += size


	def extend(self, items):
		for item in items:
			size = totalSizeOf(item)
			self._items[self._counter + 1] = (item, size)
			self._counter += 1
			self._size += size


	def __repr__(self):
		return '<Queue at 0x%x with %r item(s), counter=#%r, size=%r>' % (
			id(self), self.getQueuedCount(), self._counter, self._size)


	def iterItems(self, start=None):
		"""
		Yield (seqNum, item) for every item in the queue.

		If C{start} is not C{None}, items before L{start} will be skipped.
		"""
		if __debug__:
			if start is not None:
				assert start >= 0, start

		sortedItems = self._items.items()
		sortedItems.sort()
		for seqNum, (item, size) in sortedItems:
			if start is None or seqNum >= start:
				yield (seqNum, item)


	def handleSACK(self, sack):
		"""
		Remove all items that are no longer needed, based on C{sack}.

		Returns C{True} if ackNumber or any sackNumber was higher
		than the highest seqNum in the queue.  This would indicate a
		"bad SACK".  Note that as many items as possible are removed
		even in the "bad SACK" case.  If not bad SACK, returns C{False}.

		@param sack: SACK information
		@type sack: L{SACK}
		"""
		ackNum = sack.ackNumber
		assert ackNum >= -1, ackNum

		badSACK = False

		if ackNum > self._counter:
			badSACK = True

		sortedKeys = self._items.keys()
		sortedKeys.sort()

		for k in sortedKeys:
			if k > ackNum:
				break
			size = self._items[k][1]
			del self._items[k]
			self._size -= size

		for sackNum in sack.sackList:
			if sackNum > self._counter:
				badSACK = True
			try:
				size = self._items[sackNum][1]
				del self._items[sackNum]
				self._size -= size
			except KeyError:
				pass

		# Possibly reduce memory use by killing the old dict
		if not self._items:
			self._items = {}

		return badSACK


	def getQueuedCount(self):
		return len(self._items)


	def getMaxConsumption(self):
		"""
		@rtype: L{int}
		@return: maximum possible consumption of the queued items.

		Keep in mind that if queued items have children that point
		to the same object, this may overreport how much memory is really
		being consumed.
		"""
		return self._size



class _wasSF(str):
	"""
	A marker class for objects that were a L{StringFragment}
	before being converted to a str.
	"""
	__slots__ = ()



class Incoming(object):
	"""
	A receive window which can accept in-order (but possibly with gaps)
	numbered items, compute a SACK tuple for those items, and return
	an Array of in-order deliverable items.  It keeps track of how much
	memory the undeliverable items are using, and can reject items if
	they would push Incoming over an item or memory size limit.

	This is used to ensure that strings are delivered to the local *Stream
	reliably and in-order.  Caller is responsible for protecting against
	resource exhaustion attacks by checking the `hitLimit` value, or calling
	{@link #getUndeliverableCount} or {@link #getMaxConsumption}.

	Not-currently-deliverable L{StringFragment}s will be be converted to
	C{str}s while in Incoming, and converted back when you retrieve them.
	This is done because L{StringFragment}s may be referencing a giant
	C{str}, which we don't want to keep around.  It's also easier to get the
	size-in-memory of a C{str}.
	"""
	__slots__ = ('_lastAck', '_cached', '_size')

	def __init__(self):
		self._lastAck = -1

		# A dictionary to store items given to us, but not yet deliverable
		# (because there are gaps).
		self._cached = {}

		self._size = 0


	def give(self, numAndItemSeq, itemLimit=None, sizeLimit=None):
		"""
		Simultaneously give new items, and get deliverable items.

		@param numAndItemSeq: a sequence of *already sorted* (seqNum, strObj).
			C{seqNum} may be an C{int}, C{long}, or integral C{float}.
			C{strObj} may be a C{str} or L{StringFragment}.

		@return: (list of deliverable items, hitLimit?) 
		"""
		# TODO: maybe immediately reject items that have little chance
		# of delivery (seqNum far above lastAck + itemLimit) to further
		# reduce the possibility of ACAs.  Right now we have enough ACA
		# protection if itemLimit is no more than ~50.

		deliverable = []
		hitLimit = False
		for num, item in numAndItemSeq:
			assert isinstance(item, (str, StringFragment)), type(item)
			if num < 0:
				raise ValueError("Sequence num must be 0 or above, was %r" % (num,))

			if num == self._lastAck + 1:
				##print "deliverable.append(%r)" % (item,)
				deliverable.append(item)
				self._lastAck += 1
				while True:
					lastAckP1 = self._lastAck + 1
					if not lastAckP1 in self._cached:
						break
					cachedItem, cachedSize = self._cached[lastAckP1]
					##print "del self._cached[%r]" % (num,)
					deliverable.append(
						StringFragment(cachedItem, 0, len(cachedItem)) if \
						isinstance(cachedItem, _wasSF) else cachedItem)
					del self._cached[lastAckP1]
					self._size -= cachedSize
					self._lastAck = lastAckP1
			elif num <= self._lastAck:
				pass
			else:
				if itemLimit is not None and len(self._cached) >= itemLimit:
					hitLimit = True
					break
				# Do the conversion here so that it applies only to the
				# undeliverable items.
				if isinstance(item, StringFragment):
					item = _wasSF(item)
				size = totalSizeOf(item)
				if sizeLimit is not None and self._size + size > sizeLimit:
					hitLimit = True
					break
				##print "self._cached[%r] = %r" % (num, item)
				self._cached[num] = (item, size)
				self._size += size

		# Possibly reduce memory use by killing the old dict
		if not self._cached:
			self._cached = {}

		return deliverable, hitLimit


	def getSACK(self):
		"""
		@rtype: L{SACK}
		@return: A SACK that represents which items Incoming has received.
		"""
		sackNumbers = self._cached.keys()
		sackNumbers.sort()

		return SACK(self._lastAck, tuple(sackNumbers))


	def getUndeliverableCount(self):
		"""
		@rtype: L{int}
		@return: the number of undeliverable items.
		"""
		return len(self._cached)


	def getMaxConsumption(self):
		"""
		@rtype: L{int}
		@return: maximum possible consumption of the undeliverable items.

		Keep in mind that if undeliverable items have children that point
		to the same object, this may overreport how much memory is really
		being consumed.
		"""
		return self._size



try: from refbinder.api import bindRecursive
except ImportError: pass
else: bindRecursive(sys.modules[__name__], _postImportVars)
