from twisted.internet import defer
from twisted.python import failure
from twisted.trial import unittest

from webmagic.fakes import ListLog

from minerva.qan import (
	OkayAnswer, KnownErrorAnswer, UnknownErrorAnswer, Question, Notification,
	Cancellation, QANHelper, qanFrameToString, InvalidQANFrame,
	stringToQANFrame, KnownError, UnknownError, QuestionFailed)


class QANFrameTests(unittest.TestCase):

	def test_sameTypeEquality(self):
		self.assertEqual(OkayAnswer("blah", 10), OkayAnswer("blah", 10))
		self.assertNotEqual(OkayAnswer("blah", 11), OkayAnswer("blah", 10))
		self.assertNotEqual(OkayAnswer("blahx", 10), OkayAnswer("blah", 10))


	def test_differentTypeEquality(self):
		self.assertNotEqual(OkayAnswer("blah", 10), Question("blah", 10))
		self.assertNotEqual(OkayAnswer("blah", 10), KnownErrorAnswer("blah", 10))
		self.assertNotEqual(Question("blah", 10), KnownErrorAnswer("blah", 10))


	def test_qanFrameToStringValid(self):
		self.assertEqual("blah#", qanFrameToString(Notification("blah")))

		self.assertEqual("blah|0Q", qanFrameToString(Question("blah", 0)))
		self.assertEqual("blah|100Q", qanFrameToString(Question("blah", 100)))

		self.assertEqual("blah|100K", qanFrameToString(OkayAnswer("blah", 100)))
		self.assertEqual("blah|100E", qanFrameToString(KnownErrorAnswer("blah", 100)))
		self.assertEqual("blah|100U", qanFrameToString(UnknownErrorAnswer("blah", 100)))
		self.assertEqual("100C", qanFrameToString(Cancellation(100)))


	def test_qanFrameToStringInvalid(self):
		for bad in [None, True, False, u"blah", 3, 3.0, (), [], {}, object()]:
			self.assertRaises(TypeError, lambda: qanFrameToString(Notification(bad)))


	def test_stringToQANFrameValid(self):
		self.assertEqual(Question("blah", 10), stringToQANFrame("blah|10Q"))
		self.assertEqual(OkayAnswer("blah", 10), stringToQANFrame("blah|10K"))
		self.assertEqual(KnownErrorAnswer("blah", 10), stringToQANFrame("blah|10E"))
		self.assertEqual(UnknownErrorAnswer("blah", 10), stringToQANFrame("blah|10U"))
		self.assertEqual(Cancellation(10), stringToQANFrame("10C"))
		self.assertEqual(Notification("blah"), stringToQANFrame("blah#"))


	def test_stringToQANFrameInvalid(self):
		self.assertRaises(InvalidQANFrame, lambda: stringToQANFrame(""))
		self.assertRaises(InvalidQANFrame, lambda: stringToQANFrame("whatX"))
		self.assertRaises(InvalidQANFrame, lambda: stringToQANFrame("blah|10X"))
		self.assertRaises(InvalidQANFrame, lambda: stringToQANFrame("1x0C"))
		self.assertRaises(InvalidQANFrame, lambda: stringToQANFrame("C"))
		self.assertRaises(InvalidQANFrame, lambda: stringToQANFrame("blah|1x0Q"))
		self.assertRaises(InvalidQANFrame, lambda: stringToQANFrame("Q"))


	def test_repr(self):
		self.assertEqual("Question('blah', 10)", repr(Question('blah', 10)))
		self.assertEqual("OkayAnswer('blah', 10)", repr(OkayAnswer('blah', 10)))
		self.assertEqual("KnownErrorAnswer('blah', 10)", repr(KnownErrorAnswer('blah', 10)))
		self.assertEqual("Cancellation(10)", repr(Cancellation(10)))
		self.assertEqual("Notification('blah')", repr(Notification('blah')))



class QANHelperTests(unittest.TestCase):

	def test_repr(self):
		h = QANHelper(None, None, lambda _: None, None)
		self.assertEqual("<QANHelper asked 0 questions, waiting for 0 "
			"peer answers and 0 local answers>", repr(h))
		h.ask("what?")
		self.assertEqual("<QANHelper asked 1 questions, waiting for 1 "
			"peer answers and 0 local answers>", repr(h))


	def test_ask(self):
		sent = ListLog()
		def sendQANFrame(frame):
			sent.append(frame)

		answers = ListLog()
		def gotOkayAnswer(answer):
			answers.append((answer, 'okay'))

		def gotErrorAnswerExpect(expectedFailure):
			def gotErrorAnswer(failure):
				failure.trap(expectedFailure)
				answers.append((failure.value[0], 'error'))
			return gotErrorAnswer

		fatalErrors = ListLog()
		def fatalError(msg):
			fatalErrors.append(msg)

		h = QANHelper(None, None, sendQANFrame, fatalError)
		d1 = h.ask("what?")
		d1.addCallbacks(gotOkayAnswer, gotErrorAnswerExpect(None))

		# Make sure QANHelper wrote something to the peer
		self.assertEqual([
			Question("what?", 1),
		], sent.getNew())

		# We shouldn't have an answer yet
		self.assertEqual([], answers.getNew())

		# An answer with a wrong QID calls fatalError
		self.assertEqual([], fatalErrors.getNew())
		h.handleQANFrame(OkayAnswer("answer with wrong qid", 100))
		self.assertEqual(["Received an answer with invalid qid: 100"], fatalErrors.getNew())

		### TODO: we might have to set up a new QANHelper after the fatalError;
		### the current implementation is lenient.

		# Feed this "OkayAnswer from the peer" into QANHelper
		h.handleQANFrame(OkayAnswer("no.", 1))

		self.assertEqual([('no.', 'okay')], answers.getNew())


		d2 = h.ask("I want a KnownError response to this one")
		d2.addCallbacks(gotOkayAnswer, gotErrorAnswerExpect(KnownError))

		# Feed this "KnownErrorAnswer from the peer" into QANHelper
		h.handleQANFrame(KnownErrorAnswer("KnownErrorAnswer as asked", 2))

		self.assertEqual([('KnownErrorAnswer as asked', 'error')], answers.getNew())


		d3 = h.ask("I want an UnknownError response to this one")
		d3.addCallbacks(gotOkayAnswer, gotErrorAnswerExpect(UnknownError))

		# Feed this "UnknownErrorAnswer from the peer" into QANHelper
		h.handleQANFrame(UnknownErrorAnswer("UnknownErrorAnswer as asked", 3))

		self.assertEqual([('UnknownErrorAnswer as asked', 'error')], answers.getNew())


	def test_notify(self):
		sent = []
		def sendQANFrame(frame):
			sent.append(frame)

		h = QANHelper(None, None, sendQANFrame, None)
		ret = h.notify("you've got mail")
		self.assertIdentical(None, ret)

		# Make sure QANHelper wrote something to the peer
		self.assertEqual([
			Notification("you've got mail"),
		], sent)


	def test_notificationReceived(self):
		received = []
		def bodyReceived(body, isQuestion):
			received.append((body, isQuestion))

		h = QANHelper(bodyReceived, None, None, None)
		h.handleQANFrame(Notification("poke"))
		h.handleQANFrame(Notification("and again"))
		self.assertEqual([
			('poke', False),
			('and again', False)
		], received)


	def test_questionReceived(self):
		received = []
		def bodyReceived(body, isQuestion):
			received.append((body, isQuestion))
			return "chilly"

		sent = []
		def sendQANFrame(frame):
			sent.append(frame)

		h = QANHelper(bodyReceived, None, sendQANFrame, None)
		h.handleQANFrame(Question("the weather?", 1))
		h.handleQANFrame(Question("how about now?", 2))
		self.assertEqual([
			('the weather?', True),
			('how about now?', True)
		], received)

		self.assertEqual([
			OkayAnswer("chilly", 1),
			OkayAnswer("chilly", 2),
		], sent)


	def test_questionReceivedAsync(self):
		received = []
		answerDs = [
			defer.Deferred(),
			defer.Deferred(),
			defer.Deferred(),
		]
		def bodyReceived(body, isQuestion):
			received.append((body, isQuestion))
			return answerDs.pop(0)

		sent = []
		def sendQANFrame(frame):
			sent.append(frame)

		h = QANHelper(bodyReceived, None, sendQANFrame, None)
		d1 = answerDs[0]
		d2 = answerDs[1]
		d3 = answerDs[2]
		h.handleQANFrame(Question("the weather?", 1))
		h.handleQANFrame(Question("how about now?", 2))
		h.handleQANFrame(Question("and now?", 3))
		self.assertEqual([
			('the weather?', True),
			('how about now?', True),
			('and now?', True),
		], received)

		self.assertEqual([], sent)

		# Test some non-str responses, since we support those, at least
		# inside QANHelper.
		d2.callback(["rainy", 9000])
		d1.callback("hurricane")
		d3.errback(KnownError(["weather station is broken", "yep"]))

		self.assertEqual([
			OkayAnswer(["rainy", 9000], 2),
			OkayAnswer("hurricane", 1),
			KnownErrorAnswer(["weather station is broken", "yep"], 3),
		], sent)


	def test_questionReceivedDuplicateQid(self):
		received = ListLog()
		def bodyReceived(body, isQuestion):
			received.append((body, isQuestion))
			return defer.Deferred()

		nonlocal = dict(fatalReason=None)
		def fatalError(reason):
			nonlocal['fatalReason'] = reason

		h = QANHelper(bodyReceived, None, None, fatalError)
		h.handleQANFrame(Question("what?", 1))
		h.handleQANFrame(Question("where?", 1))

		self.assertEqual([("what?", True)], received.getNew())

		self.assertEqual("Received Question with duplicate qid: 1", nonlocal['fatalReason'])


	def test_theyCancel(self):
		nonlocal = dict(
			cancellerDoesErrbackCalled=False,
			cancellerDoesCallbackCalled=False,
		)
		def cancellerDoesErrback(d):
			nonlocal['cancellerDoesErrbackCalled'] = True
			d.errback(KnownError("okay, you'll never know"))

		def cancellerDoesCallback(d):
			nonlocal['cancellerDoesCallbackCalled'] = True
			d.callback("maybe a little warm")

		received = []
		answerDs = [
			defer.Deferred(),
			defer.Deferred(cancellerDoesErrback),
			defer.Deferred(),
			defer.Deferred(cancellerDoesCallback),
		]
		def bodyReceived(body, isQuestion):
			received.append((body, isQuestion))
			return answerDs.pop(0)

		sent = ListLog()
		def sendQANFrame(frame):
			sent.append(frame)

		h = QANHelper(bodyReceived, None, sendQANFrame, None)
		d1 = answerDs[0]
		d2 = answerDs[1]
		d3 = answerDs[2]
		d4 = answerDs[3]
		h.handleQANFrame(Question("the weather?", 1))
		h.handleQANFrame(Question("how about now?", 2))
		h.handleQANFrame(Question("and now?", 3))
		h.handleQANFrame(Question("this evening?", 4))
		self.assertEqual([
			('the weather?', True),
			('how about now?', True),
			('and now?', True),
			('this evening?', True),
		], received)

		self.assertEqual([], sent.getNew())

		self.assertEqual(False, nonlocal['cancellerDoesErrbackCalled'])
		self.assertEqual(False, nonlocal['cancellerDoesCallbackCalled'])

		# Cancel Question #2
		h.handleQANFrame(Cancellation(2))
		self.assertTrue(nonlocal['cancellerDoesErrbackCalled'])
		self.assertEqual([
			KnownErrorAnswer("okay, you'll never know", 2),
		], sent.getNew())

		# Cancel Question #4
		h.handleQANFrame(Cancellation(4))
		self.assertTrue(nonlocal['cancellerDoesCallbackCalled'])
		self.assertEqual([
			OkayAnswer("maybe a little warm", 4)
		], sent.getNew())

		# Cancel Question #1, which has no canceller
		h.handleQANFrame(Cancellation(1))
		self.assertEqual([
			UnknownErrorAnswer("CancelledError", 1),
		], sent.getNew())

		d3.errback(KnownError("weather station is broken"))
		self.assertEqual([
			KnownErrorAnswer("weather station is broken", 3),
		], sent.getNew())


	def test_questionCausesException(self):
		"""
		A Question that causes bodyReceived to raise an exception leads
		to a call to logError, and an UnknownErrorResponse("Uncaught exception")
		sent to the peer.
		"""
		loggedErrors = []
		def logError(message, failure):
			loggedErrors.append((message, failure))

		def bodyReceived(body, isQuestion):
			raise ValueError("bodyReceived did something wrong")

		sent = ListLog()
		def sendQANFrame(frame):
			sent.append(frame)

		h = QANHelper(bodyReceived, logError, sendQANFrame, None)
		h.handleQANFrame(Question("How much wood would a wood chuck chuck?", 1))

		self.assertEqual("Peer's Question #1 caused uncaught exception", loggedErrors[0][0])
		self.assertIsInstance(loggedErrors[0][1], failure.Failure)

		self.assertEqual([UnknownErrorAnswer("Uncaught exception", 1)], sent.getNew())


	def test_notificationCausesException(self):
		"""
		A Notification that causes bodyReceived to raise an exception leads
		to a call to logError, and no response sent to the peer.
		"""
		loggedErrors = []
		def logError(message, failure):
			loggedErrors.append((message, failure))

		def bodyReceived(body, isQuestion):
			raise ValueError("bodyReceived did something wrong")

		sent = ListLog()
		def sendQANFrame(frame):
			sent.append(frame)

		h = QANHelper(bodyReceived, logError, sendQANFrame, None)
		h.handleQANFrame(Notification("You've got more mail"))

		self.assertEqual("Peer's Notification caused uncaught exception", loggedErrors[0][0])
		self.assertIsInstance(loggedErrors[0][1], failure.Failure)

		self.assertEqual([], sent.getNew())


	def test_theyCancelNonexistentQuestion(self):
		h = QANHelper(None, None, None, None)
		# Cancellation a nonexistent Question does not raise an error
		h.handleQANFrame(Cancellation(1))
		h.handleQANFrame(Cancellation(1))
		h.handleQANFrame(Cancellation(2))


	def test_weCancel(self):
		sent = ListLog()
		def sendQANFrame(frame):
			sent.append(frame)

		h = QANHelper(None, None, sendQANFrame, None)
		d = h.ask("going to the theater?")

		self.assertEqual([
			Question("going to the theater?", 1),
		], sent.getNew())

		d.cancel()

		self.assertEqual([
			Cancellation(1),
		], sent.getNew())

		self.assertTrue(d.called)
		d2 = self.assertFailure(d, defer.CancelledError)
		assert d2.called

		# Peer always sends an answer, which QANHelper must ignore.
		h.handleQANFrame(OkayAnswer("nope", 1))


	def test_failAll(self):
		sent = ListLog()
		def sendQANFrame(frame):
			sent.append(frame)

		h = QANHelper(None, None, sendQANFrame, None)
		d1 = h.ask("going to the theater?")
		d2 = h.ask("mu?")

		self.assertEqual([
			Question("going to the theater?", 1),
			Question("mu?", 2),
		], sent.getNew())

		h.failAll("just because")
		self.assertTrue(d1.called)
		d1_ = self.assertFailure(d1, QuestionFailed)
		d1_.addCallback(lambda e: self.assertEqual("just because", str(e)))
		assert d1_.called

		self.assertTrue(d2.called)
		d2_ = self.assertFailure(d2, QuestionFailed)
		d2_.addCallback(lambda e: self.assertEqual("just because", str(e)))
		assert d2_.called

		# Peer can still send an answer to the failed Questions
		h.handleQANFrame(OkayAnswer("no", 1))
		h.handleQANFrame(KnownErrorAnswer("what?", 2))
