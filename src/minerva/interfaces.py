"""
Interfaces for Minerva.

All interfaces here are public.
"""

from zope.interface import Interface


# A copy of twisted.internet.interfaces.IConsumer with the `write` method
# removed.
class IConsumerWithoutWrite(Interface):
	"""
	A consumer consumes data from a producer.
	"""
	def registerProducer(producer, streaming):
		"""
		Register to receive data from a producer.

		This sets self to be a consumer for a producer.  When this object runs
		out of data (as when a send(2) call on a socket succeeds in moving the
		last data from a userspace buffer into a kernelspace buffer), it will
		ask the producer to resumeProducing().

		For L{IPullProducer} providers, C{resumeProducing} will be called once
		each time data is required.

		For L{IPushProducer} providers, C{pauseProducing} will be called
		whenever the write buffer fills up and C{resumeProducing} will only be
		called when it empties.

		@type producer: L{IProducer} provider

		@type streaming: C{bool}
		@param streaming: C{True} if C{producer} provides L{IPushProducer},
		C{False} if C{producer} provides L{IPullProducer}.

		@raise RuntimeError: If a producer is already registered.

		@return: C{None}
		"""


	def unregisterProducer():
		"""
		Stop consuming data from a producer, without disconnecting.
		"""



# Note: while we mention L{ServerStream} in this interface, this interface
# is also applicable to a ClientStream written in Python.
class IStringProtocol(Interface):
	"""
	An interface for string-based communication that abstracts
	away the Comet logic and transports.

	This interface is analogous to L{twisted.internet.interfaces.IProtocol}

	Note: if you call stream.reset, some (or all) of the strings you
	have recently sent may be lost.  If you need a proper close, use
	your own application-level strings to determine that it is safe to
	close, then call reset.

	The simplest way to end dead ServerStreams is to use an application-level
	ping message that your client application sends (say every 55 seconds),
	and end the ServerStream if no such message has been received for
	2 minutes.
	"""

	def streamStarted(stream):
		"""
		Called when the local *Stream object associated with this protocol
		has started.  On the server, this is usually called after the client
		attaches their first transport.  On the client, this is called when
		you call C{stream.start()}.

		You'll want to keep the stream around with C{self.stream = stream}.

		@param stream: the L{ServerStream} that was started.
		@type stream: L{ServerStream}
		"""


	def streamReset(reasonString, applicationLevel):
		"""
		Called when this stream has reset, either internally by
		L{ServerStream}, or a call to ServerStream.reset, or by a reset
		frame from the peer.

		@param reasonString: The reason the stream reset.
			String contains only bytes in inclusive range 0x20 - 0x7E.
		@type reasonString: str

		@type applicationLevel: Was the reason caused by an application (not
			Minerva internals?)
		"""


	def stringReceived(s):
		"""
		@param s: A restricted string from the peer.
		@type s: C{str}
		"""
	del stringReceived # Because it's optional.  TODO: Interface subclass?


	def stringsReceived(strings):
		"""
		NOTE: Implement `stringReceived` instead.  It's safer and simpler
		to use.  If this method is implemented, `stringReceived` (singular)
		will not be called.

		Called whenever one or more strings are received.

		If you need to, you may mutate the list and keep references to it.

		This is `stringsReceived` instead of `stringReceived` only as an
		optimization for CPython.  The number of strings you will receive at
		once is subject to variances in TCP activity.  Do *not* rely on being
		called with a certain number of strings.

		@type strings: list
		@param strings: a list of L{StringFragment} objects.  You can convert
			them to C{str}s by C{str()}ing them.  Do *not* keep them around
			in L{StringFragment} form because they may consume more
			memory than you expect.
		"""
	del stringsReceived # Because it's optional.  TODO: Interface subclass?



class IStringFactory(Interface):
	"""
	Interface for L{IStringProtocol} factories.
	"""
	def buildProtocol():
		"""
		Called when a L{ServerStream} has been established.

		Unlike the analogous Twisted L{twisted.internet.interfaces.IFactory},
		you cannot refuse a connection here.

		An implementation should
			construct an object providing I{IStringProtocol},
			do C{obj.factory = self},
			and return C{obj},
		with optionally more steps in between.

		@return: an object providing L{IStringProtocol}.
		"""



class IQANProtocol(Interface):
	"""
	An interface for string-based communication that allows for
	question-answer-notify.
	"""
	def streamStarted(stream, qanHelper):
		"""
		Called when the local *Stream object associated with this protocol
		has started.  On the server, this is usually called after the client
		attaches their first transport.  On the client, this is called when
		you call C{stream.start()}.

		You'll want to keep the stream around with C{self.stream = stream}.
		You'll want to keep the QANHelper around with C{self.qanHelper = qanHelper}.

		You must not call C{stream.sendString}; use C{qanHelper.ask} or
		C{qanHelper.notify} for all of your communication.

		@param stream: the L{ServerStream} that was started.
		@type stream: L{ServerStream}

		@param qanHelper: the L{QANHelper} coupled with the L{ServerStream}.
		@type qanHelper: L{QANHelper}
		"""


	def streamReset(reasonString, applicationLevel):
		"""
		Called when this stream has reset, either internally by
		L{ServerStream}, or a call to ServerStream.reset, or by a reset
		frame from the peer.

		@param reasonString: The reason the stream reset.
			String contains only bytes in inclusive range 0x20 - 0x7E.
		@type reasonString: str

		@type applicationLevel: Was the reason caused by an application (not
			Minerva internals?)
		"""


	def bodyReceived(body, isQuestion):
		"""
		Called when a Question or Notification has been received from the peer.

		@param body: The QAN body from the peer.  Always a restricted string.
		@type body: C{str}

		@param isQuestion: True if the QAN body arrived as a question that can
			be answered, False if it arrived as a Notification.  If it is a question,
			this method's return value (or Deferred) will be used as the answer.
			Answer *must* be a restricted string C{str}.  If L{qan.KnownError}
			is raised (or errbacked), the string value of the L{qan.KnownError}
			will be sent as the error-answer.  If another exception is raised,
			an uninformative unknown-error-answer will be sent to the peer.
		@type s: C{str}

		@return: If C{isQuestion}, an answer to the question.
		@rtype: C{str} or L{Deferred} or C{None}.
		@raise KnownError: When an error-answer is desired.
		"""



class IStreamTransportCreated(Interface):
	def transportCreated(self, transportInfo):
		"""
		@param transportInfo: A L{TransportInfo} object with information
			about the transport that was just created.
		"""



class IStreamTransportDestroyed(Interface):
	def transportDestroyed(self, transportInfo):
		"""
		@param transportInfo: A L{TransportInfo} object with information
			about the transport that was just destroyed.
		"""


# In the future, there might be an ITrackerTransportCreated, to watch
# transports that never even attach to a Stream.
