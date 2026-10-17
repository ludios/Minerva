from twisted.trial import unittest

from strfrag import StringFragment

from minerva.window import totalSizeOf, SACK, Queue, Incoming, _wasSF


class QueueTests(unittest.TestCase):
	"""
	Tests for L{window.Queue}
	"""
	def test_repr(self):
		q = Queue()
		self.assertEqual('<Queue at 0x%x with 0 item(s), counter=#-1, '
			'size=0>' % (id(q),), repr(q))

		q.extend(['a', 'b'])
		self.assertEqual('<Queue at 0x%x with 2 item(s), counter=#1, '
			'size=%d>' % (id(q), totalSizeOf('a') * 2), repr(q))

		q.handleSACK(SACK(0, ()))
		self.assertEqual('<Queue at 0x%x with 1 item(s), counter=#1, '
			'size=%d>' % (id(q), totalSizeOf('a')), repr(q))


	def test_getMaxConsumption(self):
		"""
		The size of the Queue increases when we extend it or append to it,
		and decreases when we give it an ackNumber or sackNum that
		causes it to remove items.
		"""
		q = Queue()
		self.assertEqual(0, q.getMaxConsumption())
		q.extend(['a', 'b'])
		self.assertEqual(totalSizeOf('a') * 2, q.getMaxConsumption())
		q.handleSACK(SACK(0, ()))
		self.assertEqual(totalSizeOf('a'), q.getMaxConsumption())
		# strange-looking SACK, but it does exercise the code we want to exercise
		q.handleSACK(SACK(0, (1,)))
		self.assertEqual(0, q.getMaxConsumption())
		q.handleSACK(SACK(1, ()))
		self.assertEqual(0, q.getMaxConsumption())
		q.append('cc')
		self.assertEqual(totalSizeOf('cc'), q.getMaxConsumption())


	def test_iterEmptyQueue(self):
		q = Queue()
		self.assertEqual([], list(q.iterItems(start=0)))


	def test_appendExtendQueue(self):
		q = Queue()
		q.append('zero')
		q.extend(['one', 'two'])
		self.assertEqual([(0, 'zero'), (1, 'one'), (2, 'two')], list(q.iterItems(start=0)))
		# iterItems is idempotent
		self.assertEqual([(0, 'zero'), (1, 'one'), (2, 'two')], list(q.iterItems(start=0)))


	def test_appendExtendQueueStart1(self):
		q = Queue()
		q.append('zero')
		q.extend(['one', 'two'])
		self.assertEqual([(1, 'one'), (2, 'two')], list(q.iterItems(start=1)))
		# iterItems is idempotent
		self.assertEqual([(1, 'one'), (2, 'two')], list(q.iterItems(start=1)))


	def test_appendExtendQueueStart3(self):
		q = Queue()
		q.append('zero')
		q.extend(['one', 'two'])
		self.assertEqual([], list(q.iterItems(start=3)))
		# iterItems is idempotent
		self.assertEqual([], list(q.iterItems(start=3)))


	def test_handleSACKOnlyAckNumber(self):
		q = Queue()
		q.append('zero')
		q.extend(['one', 'two'])

		self.assertEqual(False, q.handleSACK(SACK(0, ())))
		self.assertEqual([(1, 'one'), (2, 'two')], list(q.iterItems(start=1)))

		# Removing again is idempotent
		self.assertEqual(False, q.handleSACK(SACK(0, ())))
		self.assertEqual([(1, 'one'), (2, 'two')], list(q.iterItems(start=1)))


	def test_ackNumberTooHigh0(self):
		q = Queue()
		badSACK = q.handleSACK(SACK(0, ()))
		self.assertEqual(True, badSACK)


	def test_ackNumberTooHigh1(self):
		q = Queue()
		q.append('zero')
		badSACK = q.handleSACK(SACK(1, ()))
		self.assertEqual(True, badSACK)
		# Items were still removed, despite it being a bad SACK
		self.assertEqual([], list(q.iterItems()))


	def test_sackNumberTooHigh(self):
		q = Queue()
		q.extend(['zero', 'one', 'two', 'three'])
		badSACK = q.handleSACK(SACK(0, (2, 5)))
		self.assertEqual(True, badSACK)
		# Items were still removed, despite it being a bad SACK
		self.assertEqual([(1, 'one'), (3, 'three')], list(q.iterItems()))


	def test_handleSACKToHigherNum(self):
		q = Queue()
		q.extend(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
		self.assertEqual(False, q.handleSACK(SACK(1, ())))
		self.assertEqual(False, q.handleSACK(SACK(3, ())))

		# There should be 5 items left in the queue
		self.assertEqual([(4,'4'), (5,'5'), (6,'6'), (7,'7'), (8,'8'), (9,'9'), (10,'10')], list(q.iterItems(start=4)))


	def test_iterItemsNoStartNumber(self):
		"""
		A L{start} for iterItems is not required.
		"""
		q = Queue()
		q.append('zero')
		q.extend(['one', 'two'])
		self.assertEqual([(0, 'zero'), (1, 'one'), (2, 'two')], list(q.iterItems()))
		self.assertEqual(False, q.handleSACK(SACK(-1, ())))
		self.assertEqual([(0, 'zero'), (1, 'one'), (2, 'two')], list(q.iterItems()))
		self.assertEqual(False, q.handleSACK(SACK(0, ())))
		self.assertEqual([(1, 'one'), (2, 'two')], list(q.iterItems()))


	def test_handleSACK(self):
		"""
		handleSACK actually removes the selectively-acknowledged items from the queue 
		"""
		q = Queue()
		q.append('zero')
		q.extend(['one', 'two', 'three'])
		self.assertEqual([(0, 'zero'), (1, 'one'), (2, 'two'), (3, 'three')], list(q.iterItems()))
		self.assertEqual(False, q.handleSACK(SACK(-1, (1,))))
		self.assertEqual([(0, 'zero'), (2, 'two'), (3, 'three')], list(q.iterItems()))
		self.assertEqual(False, q.handleSACK(SACK(0, (3,))))
		self.assertEqual([(2, 'two')], list(q.iterItems()))
		q.append('four')
		self.assertEqual([(2, 'two'), (4, 'four')], list(q.iterItems()))
		# although this is a very strange SACK because it should have
		# been (4, ()), it is still legal
		self.assertEqual(False, q.handleSACK(SACK(0, (2, 4))))
		self.assertEqual([], list(q.iterItems()))
		q.append('five')
		self.assertEqual([(5, 'five')], list(q.iterItems()))


	def test_handleSACKBothAckAndSackNumRemoveItems(self):
		"""
		Another handleSACK test.  This covers a wrong-variable-in-loop bug
		we had.
		"""
		q = Queue()
		q.extend(['zero', 'one', 'two', 'three', 'four'])
		self.assertEqual(False, q.handleSACK(SACK(0, (1, 3))))
		self.assertEqual([(2, 'two'), (4, 'four')], list(q.iterItems()))



class IncomingTests(unittest.TestCase):
	"""
	Tests for L{window.Incoming}
	"""
	def test_SACKNoItems(self):
		i = Incoming()
		self.assertEqual(SACK(-1, ()), i.getSACK())


	def test_threeItems(self):
		i = Incoming()
		self.assertEqual(
			(['string0', 'string1', 'string2'], False),
			i.give([[0, 'string0'], [1, 'string1'], [2, 'string2']]))
		self.assertEqual(SACK(2, ()), i.getSACK())


	def test_itemMissing(self):
		i = Incoming()
		self.assertEqual(
			(['string0', 'string1'], False),
			i.give([[0, 'string0'], [1, 'string1'], [3, 'string3']]))
		self.assertEqual(SACK(1, (3,)), i.getSACK())


	def test_twoItemsMissing(self):
		i = Incoming()
		self.assertEqual(
			(['string0', 'string1'], False),
			i.give([[0, 'string0'], [1, 'string1'], [4, 'string4']]))
		self.assertEqual(SACK(1, (4,)), i.getSACK())


	def test_twoRangesMissing(self):
		i = Incoming()
		self.assertEqual(
			(['string0', 'string1'], False),
			i.give([[0, 'string0'], [1, 'string1'], [4, 'string4'], [6, 'string6']]))
		self.assertEqual(SACK(1, (4, 6)), i.getSACK())


	def test_twoRangesMissingAbove9(self):
		"""
		Test that the sackList is sorted by the numeric value of the
		numbers.  This test was ported from Javascript and is not really
		necessary in Python.
		"""
		i = Incoming()
		self.assertEqual(
			(['string0', 'string1'], False),
			i.give([[0, 'string0'], [1, 'string1'], [4, 'string4'], [10, 'string6']]))
		self.assertEqual(SACK(1, (4, 10)), i.getSACK())


	def test_twoRangesMissingThenFill(self):
		i = Incoming()
		self.assertEqual(
			(['string0', 'string1'], False),
			i.give([[0, 'string0'], [1, 'string1'], [4, 'string4'], [6, 'string6']]))
		self.assertEqual(SACK(1, (4, 6)), i.getSACK())
		self.assertEqual(
			(['string2', 'string3', 'string4', 'string5', 'string6'], False),
			i.give([[2, 'string2'], [3, 'string3'], [5, 'string5']]))
		self.assertEqual(SACK(6, ()), i.getSACK())


	def test_outOfOrder(self):
		i = Incoming()
		# string0 missing
		self.assertEqual(([], False), i.give([[1, 'string1'], [2, 'string2']]))
		self.assertEqual(SACK(-1, (1, 2)), i.getSACK())
		# finally deliver it
		self.assertEqual((['string0', 'string1', 'string2'], False), i.give([[0, 'string0']]))
		# make sure it still works
		self.assertEqual((['string3'], False), i.give([[3, 'string3']]))
		self.assertEqual(SACK(3, ()), i.getSACK())


	def test_outOfOrderJustOneCall(self):
		"""
		L{Incoming} handles all the strings even when they're given
		out-of-order in one L{Incoming.give} call.

		You should *not* pass .give unsorted sequences in production code,
		because you may hit the item/size limit.  It will also be slower because
		it must modify a dictionary more frequently.
		"""
		i = Incoming()
		self.assertEqual((['string0', 'string1'], False), i.give([[1, 'string1'], [0, 'string0']]))
		self.assertEqual(SACK(1, ()), i.getSACK())


	def test_negativeSequenceNum(self):
		i = Incoming()
		self.assertRaises(ValueError, lambda: i.give([[-1, 'string']]))
		self.assertRaises(ValueError, lambda: i.give([[-2, 'string']]))


	def test_getUndeliverableCount(self):
		i = Incoming()
		self.assertEqual(0, i.getUndeliverableCount())
		i.give([[1, 'string1']])
		self.assertEqual(1, i.getUndeliverableCount())
		i.give([[2, 'string2']])
		self.assertEqual(2, i.getUndeliverableCount())
		i.give([[0, 'string0']])
		self.assertEqual(0, i.getUndeliverableCount())


	def test_itemsGivenTwice(self):
		"""
		If an already-delivered item is given again, it is completely ignored
		and does not occupy space in the internal cache.
		"""
		i = Incoming()
		i.give([[0, 'string0'], [1, 'string1']])
		self.assertEqual(0, i.getUndeliverableCount())

		i.give([[0, 'string0']])
		self.assertEqual(0, i.getUndeliverableCount())
		i.give([[1, 'string1']])
		self.assertEqual(0, i.getUndeliverableCount())
		i.give([[0, 'string0'], [1, 'string1']])
		self.assertEqual(0, i.getUndeliverableCount())
		i.give([[0, 'string0'], [1, 'string1'], [2, 'string2']])
		self.assertEqual(0, i.getUndeliverableCount())


	def test_hashFloatEqualsHashInt(self):
		"""
		L{Incoming} relies on this property of Python.
		"""
		self.assertEqual(hash(-1.0), hash(-1))
		self.assertEqual(hash(5.0), hash(5))


	def test_itemLimit(self):
		i = Incoming()
		self.assertEqual(([], False), i.give([[1, 'string1']], itemLimit=3))
		self.assertEqual(([], False), i.give([[2, 'string2']], itemLimit=3))
		self.assertEqual(([], False), i.give([[3, 'string3']], itemLimit=3))
		self.assertEqual(([], True), i.give([[4, 'string4']], itemLimit=3))
		self.assertEqual(([], True), i.give([[5, 'string5']], itemLimit=3))

		# The items we kept giving it past the limit are dropped to the floor
		deliverable, hitLimit = i.give([[0, 'string0']], itemLimit=3)
		self.assertEqual(False, hitLimit)
		self.assertEqual(['string0', 'string1', 'string2', 'string3'], deliverable)

		self.assertEqual(0, i.getUndeliverableCount())
		self.assertEqual(0, i.getMaxConsumption())


	def test_sizeLimit(self):
		stringSize = totalSizeOf('string1')
		i = Incoming()
		self.assertEqual(([], False), i.give([[1, 'string1']], sizeLimit=stringSize * 3))
		self.assertEqual(([], False), i.give([[2, 'string2']], sizeLimit=stringSize * 3))
		self.assertEqual(([], False), i.give([[3, 'string3']], sizeLimit=stringSize * 3))
		self.assertEqual(([], True), i.give([[4, 'string4']], sizeLimit=stringSize * 3))
		self.assertEqual(([], True), i.give([[5, 'string5']], sizeLimit=stringSize * 3))

		# The items we kept giving it past the limit are dropped to the floor
		deliverable, hitLimit = i.give([[0, 'string0']], sizeLimit=stringSize * 3)
		self.assertEqual(['string0', 'string1', 'string2', 'string3'], deliverable)
		self.assertEqual(False, hitLimit)

		self.assertEqual(0, i.getUndeliverableCount())
		self.assertEqual(0, i.getMaxConsumption())



class IncomingConsumptionTests(unittest.TestCase):
	"""
	Tests for L{window.Incoming}'s memory-exhaustion-prevention
	"""
	def test_noStringsEverGiven(self):
		i = Incoming()
		self.assertEqual(0, i.getMaxConsumption())


	def test_simple(self):
		i = Incoming()
		_ = i.give([[1, 'string1'], [2, 'string2'], [3, 'string3']])
		self.assertEqual(totalSizeOf('string1') * 3, i.getMaxConsumption())

		_ = i.give([[4, 'string4'], [5, 'string5'], [6, 'string6']])
		self.assertEqual(totalSizeOf('string1') * 6, i.getMaxConsumption())


	def test_StringFragmentConvertToStr(self):
		"""
		L{StringFragment}s are converted to C{window._wasSF}s if they are
		undeliverable inside L{Incoming}.
		"""
		i = Incoming()
		s = _wasSF("helloworld" * 100)
		sf = StringFragment(s, 0, len(s))
		i.give([[1, sf]])
		self.assertEqual(totalSizeOf(s), i.getMaxConsumption())


	def test_strConvertedBackToStringFragment(self):
		"""
		L{window._wasSF}s are converted back to C{StringFragment}s before
		being delivered.
		"""
		i = Incoming()
		s = _wasSF("helloworld" * 100)
		sf = StringFragment(s, 0, len(s))
		i.give([[1, sf]])
		self.assertEqual(([sf, sf], False), i.give([[0, sf]]))


	def test_itemSizeChangedWhileInIncoming(self):
		"""
		If the size of an item changed while it was in Incoming,
		Incoming does *not* go into an inconsistent state (for example,
		thinking that _size is < 0)
		"""
		class LengthChangingString(str):
			def __len__(self2):
				return self2.sayLength

		i = Incoming()
		mutable = LengthChangingString("hi")
		mutable.sayLength = 2
		assert len(mutable) == 2, len(mutable)

		i.give([[1, mutable]])
		sizeBefore = i.getMaxConsumption()
		self.assertTrue(sizeBefore > 0, sizeBefore)

		mutable.sayLength = 3
		assert len(mutable) == 3, len(mutable)

		i.give([[0, "0"]])
		sizeAfter = i.getMaxConsumption()
		self.assertEqual(0, sizeAfter)
