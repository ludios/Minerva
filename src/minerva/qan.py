"""
QAN is a protocol that allows asking the peer a question and receiving an
answer or error-answer.  You can think of this as the "simplest wire-level
implementation of Deferreds", which is what AMP calls itself, though QAN takes
it even further: there is no command dispatching, and requests/responses
are completely unspecified.  (Though there are some helper functions here
that assume the requests/responses are bytestrings.)

QAN does not require Minerva; you can use it over any bidirectional framed
stream.
"""

import sys
import operator

from twisted.python import failure
from twisted.internet import defer

from minerva.objcheck import strToNonNegLimit


_postImportVars = vars().keys()


# Not a meaningful superclass, just something to avoid copy/pasting
class _BodyAndId(tuple):
	__slots__ = ()

	body = property(operator.itemgetter(1))
	qid = property(operator.itemgetter(2))

	def __new__(cls, body, qid):
		return tuple.__new__(cls, (cls._MARKER, body, qid))


	def __repr__(self):
		return '%s(%r, %r)' % (self.__class__.__name__, self[1], self[2])



class _JustQid(tuple):
	__slots__ = ()

	qid = property(operator.itemgetter(1))

	def __new__(cls, body):
		return tuple.__new__(cls, (cls._MARKER, body))


	def __repr__(self):
		return '%s(%r)' % (self.__class__.__name__, self[1])



class _JustBody(tuple):
	__slots__ = ()

	body = property(operator.itemgetter(1))

	def __new__(cls, body):
		return tuple.__new__(cls, (cls._MARKER, body))


	def __repr__(self):
		return '%s(%r)' % (self.__class__.__name__, self[1])



class Question(_BodyAndId):
	__slots__ = ()
	_MARKER = object()



class OkayAnswer(_BodyAndId):
	__slots__ = ()
	_MARKER = object()



class KnownErrorAnswer(_BodyAndId):
	__slots__ = ()
	_MARKER = object()



class UnknownErrorAnswer(_BodyAndId):
	__slots__ = ()
	_MARKER = object()



class Cancellation(_JustQid):
	__slots__ = ()
	_MARKER = object()



class Notification(_JustBody):
	__slots__ = ()
	_MARKER = object()



qanTypeToCode = {
	 Question: "Q"
	,OkayAnswer: "K"
	,KnownErrorAnswer: "E"
	,UnknownErrorAnswer: "U"
	,Cancellation: "C"
	,Notification: "#"
}


def qanFrameToString(qanFrame):
	"""
	@param qanFrame: The QAN frame to encode
	@type qanFrame: a L{Question} or L{OkayAnswer} or L{KnownErrorAnswer} or
		L{UnknownErrorAnswer} or L{Cancellation} or L{Notification}, all of
		which must have a C{str} C{.body}.  (Except for L{Cancellation},
		which has no C{.body}.)

	@return: The encoded QAN frame
	@rtype: str
	"""
	qanFrameType = type(qanFrame)
	code = qanTypeToCode[qanFrameType]
	if qanFrameType == Cancellation:
		return str(qanFrame.qid) + code
	else:
		if not isinstance(qanFrame.body, str):
			raise TypeError("qanFrame.body must be a str, was %r" % (
				qanFrame.body,))

		if qanFrameType == Notification:
			return qanFrame.body + code
		else:
			return qanFrame.body + "|" + str(qanFrame.qid) + code


class InvalidQANFrame(Exception):
	pass



def _qidOrThrow(s):
	try:
		return strToNonNegLimit(s, 2**53)
	except ValueError:
		raise InvalidQANFrame("bad qid")


def stringToQANFrame(frameString):
	"""
	@param frameString: The QAN frame, encoded as a string
	@type frameString: C{str}

	@return: The QAN frame
	@rtype qf: a L{Question} or L{OkayAnswer} or L{ErrorAnswer} or
		L{Cancellation} or L{Notification}, with a C{str} C{.body}.
	"""
	try:
		lastByte = frameString[-1]
	except IndexError:
		raise InvalidQANFrame("0-length frame")

	if lastByte == "#":
		return Notification(frameString[:-1])
	elif lastByte == "C":
		qid = _qidOrThrow(frameString[:-1])
		return Cancellation(qid)
	else:
		try:
			body, rest = frameString.rsplit('|', 1)
		except ValueError:
			raise InvalidQANFrame("Expected pipe char in frame")
		qid = _qidOrThrow(rest[:-1])

		if lastByte == "Q":
			return Question(body, qid)
		elif lastByte == "K":
			return OkayAnswer(body, qid)
		elif lastByte == "E":
			return KnownErrorAnswer(body, qid)
		elif lastByte == "U":
			return UnknownErrorAnswer(body, qid)
		else:
			raise InvalidQANFrame("Invalid QAN frame type %r" % lastByte)


def isAnswerFrame(qanFrame):
	"""
	Is C{qanFrame} an L{OkayAnswer}, L{KnownErrorAnswer}, or L{UnknownErrorAnswer}?
	"""
	return isinstance(qanFrame, (OkayAnswer, KnownErrorAnswer, UnknownErrorAnswer))


def frameHasBody(qanFrame):
	"""
	Does this C{qanFrame} have a body?  (Everything but L{Cancellation} does.)
	"""
	return not isinstance(qanFrame, Cancellation)


class KnownError(Exception):
	pass



class UnknownError(Exception):
	pass



class QuestionFailed(Exception):
	pass



class QANHelper(object):
	def __init__(self, bodyReceived, logError, sendQANFrame, fatalError):
		"""
		@param bodyReceived: The 2-arg function to call when
			a Question or Notification is received (via a call to .handleString).
			Called with arguments: body, isQuestion.

		@param logError: A 2-arg function called when bodyReceived raises
			an exception, or when QANHelper has a non-fatal internal error.
			Called with arguments: error message, L{Failure} object

		@param sendQANFrame: A 1-arg function that sends a QAN frame to the
			peer.  Called with argument: qanFrame.

		@param fatalError: A 1-arg function called when QANHelper can no longer
			handle QAN frames.  Called with argument: reason (a C{str} with bytes
			in inclusive range 0x20 (SPACE) to 0x7E (~)).  After fatalError is called,
			you must stop calling C{handleQANFrame} to prevent fatalError from
			possibly being called again.
		"""
		self._bodyReceived = bodyReceived
		self._logError = logError
		self._sendQANFrame = sendQANFrame
		self._fatalError = fatalError

		self._qidCounter = 0
		self._ourQuestions = {}
		self._theirQuestions = {}


	def __repr__(self):
		return ('<%s asked %d questions, waiting for %d peer answers '
			'and %d local answers>') % (self.__class__.__name__,
				self._qidCounter, len(self._ourQuestions),
				len(self._theirQuestions))


	def _sendOkayAnswer(self, body, qid):
		del self._theirQuestions[qid]
		self._sendQANFrame(OkayAnswer(body, qid))


	def _sendErrorAnswer(self, failure, qid):
		del self._theirQuestions[qid]
		if failure.check(KnownError):
			body = failure.value[0]
			self._sendQANFrame(KnownErrorAnswer(body, qid))
		elif failure.check(defer.CancelledError):
			self._sendQANFrame(UnknownErrorAnswer("CancelledError", qid))
		else:
			self._logError("Peer's Question #%d caused uncaught "
				"exception" % (qid,), failure)
			# We intentionally do not reveal information about the
			# exception.
			self._sendQANFrame(UnknownErrorAnswer("Uncaught exception", qid))


	def handleQANFrame(self, qanFrame):
		if isAnswerFrame(qanFrame):
			qid = qanFrame.qid
			try:
				d = self._ourQuestions.pop(qid)
			except KeyError:
				self._fatalError("Received an answer with invalid qid: %d" % (qid,))
				return

			if d is None:
				# Ignore the answer to a question we cancelled or failAll'ed.
				pass
			elif isinstance(qanFrame, OkayAnswer):
				d.callback(qanFrame.body)
			elif isinstance(qanFrame, KnownErrorAnswer):
				d.errback(KnownError(qanFrame.body))
			elif isinstance(qanFrame, UnknownErrorAnswer):
				d.errback(UnknownError(qanFrame.body))
			else:
				raise RuntimeError("handleQANFrame bug")

		elif isinstance(qanFrame, Notification):
			try:
				self._bodyReceived(qanFrame.body, False)
			except Exception:
				self._logError("Peer's Notification caused uncaught "
					"exception", failure.Failure())

		elif isinstance(qanFrame, Question):
			qid = qanFrame.qid
			if qid in self._theirQuestions:
				self._fatalError("Received Question with duplicate qid: %d" % (qid,))
				return
			d = defer.maybeDeferred(
				self._bodyReceived, qanFrame.body, True)
			self._theirQuestions[qid] = d
			d.addCallbacks(
				self._sendOkayAnswer, self._sendErrorAnswer,
				callbackArgs=(qid,), errbackArgs=(qid,))
			d.addErrback(lambda failure: self._logError(
				"Bug in QANHelper._sendOkayAnswer or _sendErrorAnswer", failure))

		elif isinstance(qanFrame, Cancellation):
			qid = qanFrame.qid
			try:
				# We don't .pop() it here because a cancelled Deferred
				# still goes through the callback or errback chain, and
				# our _sendOkayAnswer and _sendErrorAnswer
				# deletes it from self._theirQuestions.
				d = self._theirQuestions[qid]
			except KeyError:
				# Cancellations for nonexistent questions are ignored.
				pass
			else:
				d.cancel()


	def _sendCancel(self, qid):
		self._ourQuestions[qid] = None

		# Note: when we cancel something, we still expect to get either
		# an OkayAnswer or *ErrorAnswer from the peer, at least in the
		# typical case where the Stream does not reset.
		self._sendQANFrame(Cancellation(qid))

		# Because we don't call .callback or .errback in this canceller,
		# Deferred calls .errback(CancelledError()) for us.


	def ask(self, body):
		"""
		Send a Question to the peer.

		@param body: The question body
		@type body: *

		@return: a Deferred that will callback the response object, or errback
			with L{KnownError} or L{UnknownError} or L{QuestionFailed}.
		@rtype: L{defer.Deferred}
		"""
		qid = self._qidCounter + 1
		# Note: _sendQANFrame may raise exception if body is invalid
		self._sendQANFrame(Question(body, qid))
		self._qidCounter += 1

		assert qid not in self._ourQuestions
		d = defer.Deferred(lambda _: self._sendCancel(qid))
		self._ourQuestions[qid] = d
		return d


	def notify(self, body):
		"""
		Send a Notification to the peer.

		@param body: The notification body
		@type body: *

		@return: None
		@rtype: C{None}
		"""
		self._sendQANFrame(Notification(body))


	def failAll(self, reason):
		"""
		Errback all of our questions with L{QuestionFailed}.

		@param reason: Reason for failing; used as the L{QuestionFailed}
			exception message.
		@type reason: C{str}
		"""
		# .copy() because some buggy errback might .ask() a question
		for qid, d in self._ourQuestions.copy().iteritems():
			self._ourQuestions[qid] = None
			d.errback(QuestionFailed(reason))



try: from refbinder.api import bindRecursive
except ImportError: pass
else: bindRecursive(sys.modules[__name__], _postImportVars)
