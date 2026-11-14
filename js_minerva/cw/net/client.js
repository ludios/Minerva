/**
 * @fileoverview Minerva client for web browsers.
 *
 * The Minerva server, {@code mserver.py}, is good companion reading.
 *
 * If you make modifications, keep in mind that the unit tests are not
 * complete enough to prevent regressions.  You may want to use
 * the /chatapp/ page to check the behavior, and the demos in
 * js_minerva/demos/, as well as a tools like HttpFox, Firebug, and Wireshark.
 *
 * There is a lot of behavior we're optimizing for in this file:
 * 	- sending as little redundant data as possible
 * 	- receiving as little redundant data as possible
 * 	- anti-DoS (not making crazy amount of requests if peer is
 * 		unreachable or misbehaving)
 * 	- low latency (no excessive setTimeout(..., 0) )
 */

goog.provide('cw.net.MAX_FRAME_LENGTH');
goog.provide('cw.net.SocketEndpoint');
goog.provide('cw.net.ExpandedSocketEndpoint_');
goog.provide('cw.net.HttpEndpoint');
goog.provide('cw.net.ExpandedHttpEndpoint_');
goog.provide('cw.net.Endpoint');
goog.provide('cw.net.IStringProtocol');
goog.provide('cw.net.TransportInfo');
goog.provide('cw.net.QANProtocolWrapper');
goog.provide('cw.net.HttpStreamingMode');
goog.provide('cw.net.IStreamPolicy');
goog.provide('cw.net.DefaultStreamPolicy');
goog.provide('cw.net.ClientStream');
goog.provide('cw.net.ClientTransport');
goog.provide('cw.net.DoNothingTransport');
goog.provide('cw.net.TransportType_');

goog.require('goog.asserts');
goog.require('goog.async.DeferredList');
goog.require('goog.array');
goog.require('goog.events');
goog.require('goog.events.EventType');
goog.require('goog.structs.Set');
goog.require('goog.debug.Logger');
goog.require('goog.Disposable');
goog.require('goog.uri.utils');
goog.require('goog.userAgent');
goog.require('cw.clock');
goog.require('cw.dethrobber');
goog.require('cw.eventual');
goog.require('cw.record');
goog.require('cw.repr');
goog.require('cw.string');
goog.require('cw.net.SACK');
goog.require('cw.net.Queue');
goog.require('cw.net.Incoming');
goog.require('cw.net.theXHRMasterTracker_');
goog.require('cw.net.loadFlashConnector');
goog.require('cw.net.FlashSocketTracker');
goog.require('cw.net.FlashSocketConduit');
goog.require('cw.net.theXDRTracker');
goog.require('cw.net.stringToQANFrame');
goog.require('cw.net.qanFrameToString');
goog.require('cw.net.frameHasBody');
goog.require('cw.net.QANHelper');
goog.require('cw.net.breaker_FlashConnector_swf');
goog.require('goog.ui.media.FlashObject');

goog.require('cw.net.Frame');
goog.require('cw.net.TransportKillReason');
goog.require('cw.net.HelloFrame');
goog.require('cw.net.StringFrame');
goog.require('cw.net.SeqNumFrame');
goog.require('cw.net.SackFrame');
goog.require('cw.net.StreamStatusFrame');
goog.require('cw.net.YouCloseItFrame');
goog.require('cw.net.CommentFrame');
goog.require('cw.net.ResetFrame');
goog.require('cw.net.TransportKillFrame');
goog.require('cw.net.InvalidFrame');
goog.require('cw.net.HttpFormat');
goog.require('cw.net.isRestrictedString');
goog.require('cw.net.decodeFrameFromServer');


/**
 * Whether this is a standalone build of the Minerva client.
 * @define {boolean}
 * @private
 */
cw.net.STANDALONE_CLIENT_BUILD_ = false;


/**
 * The `FlashSocketTracker` used by all `ClientTransport`s on this page.
 *
 * Only one .swf will be created on the page, using the .swf loaded from the
 * first endpoint.
 *
 * @type {!cw.net.FlashSocketTracker}
 * @private
 */
cw.net.ourFlashSocketTracker_;


/**
 * Object to represent a Socket endpoint.
 *
 * @param {string} primaryUrl Absolute or relative URL to the WebPort
 * 	resource (which hosts the .swf needed).
 * @param {string} host Hostname for socket-like transports.
 * @param {number} port Port for socket-like transports.
 * @constructor
 */
cw.net.SocketEndpoint = function(primaryUrl, host, port) {
	/** @type {string} */
	this.primaryUrl = primaryUrl;
	/** @type {string} */
	this.host = host;
	/** @type {number} */
	this.port = port;
};



/**
 * Object to represent a Socket endpoint with the `FlashSocketTracker` needed
 * for making connections.
 *
 * @param {string} host Hostname for socket-like transports.
 * @param {number} port Port for socket-like transports.
 * @param {!cw.net.FlashSocketTracker} tracker The `FlashSocketTracker` that
 * 	will help us make a connection.
 * @constructor
 */
cw.net.ExpandedSocketEndpoint_ = function(host, port, tracker) {
	/** @type {string} */
	this.host = host;
	/** @type {number} */
	this.port = port;
	/** @type {!cw.net.FlashSocketTracker} */
	this.tracker = tracker;
};



/**
 * Object to represent an HTTP endpoint.
 *
 * @param {string} primaryUrl Absolute or relative URL for primary HTTP
 * 	transports.  If it contains token "%random%", the token will be replaced
 * 	with a random subdomain.
 * @param {string=} secondaryUrl Absolute or relative URL for secondary HTTP
 * 	transports.  If it contains token "%random%", the token will be replaced
 * 	with a random subdomain.
 * @constructor
 */
cw.net.HttpEndpoint = function(primaryUrl, secondaryUrl) {
	goog.asserts.assertString(primaryUrl);
	if(!secondaryUrl) {
		secondaryUrl = primaryUrl;
	}
	/** @type {string} */
	this.primaryUrl = primaryUrl;
	/** @type {string} */
	this.secondaryUrl = secondaryUrl;
};

cw.net.HttpEndpoint.prototype.__reprPush__ = function(sb, stack) {
	sb.push("<HttpEndpoint primaryUrl=");
	cw.repr.reprPush(this.primaryUrl, sb, stack);
	sb.push(", secondaryUrl=");
	cw.repr.reprPush(this.secondaryUrl, sb, stack);
	sb.push(">");
};



/**
 * Object to represent an HTTP endpoint with the window references (if needed)
 * for making cross-subdomain HTTP requests.
 *
 * @param {string} primaryUrl Absolute URL for primary HTTP transports.
 * @param {!Window} primaryWindow The contentWindow of an iframe that may
 * 	help us make XHR requests to {@code primaryUrl}, or this page's window.
 * @param {string} secondaryUrl Absolute URL for secondary HTTP transports.
 * @param {!Window} secondaryWindow The contentWindow of an iframe that may
 * 	help us make XHR requests to {@code secondaryUrl}, or this page's window.
 * @constructor
 */
cw.net.ExpandedHttpEndpoint_ = function(primaryUrl, primaryWindow, secondaryUrl, secondaryWindow) {
	goog.asserts.assertString(primaryUrl);
	goog.asserts.assertString(secondaryUrl);
	/** @type {string} */
	this.primaryUrl = primaryUrl;
	/** @type {!Window} */
	this.primaryWindow = primaryWindow;
	/** @type {string} */
	this.secondaryUrl = secondaryUrl;
	/** @type {!Window} */
	this.secondaryWindow = secondaryWindow;

	// Doing XHR with relative URLs is broken in some older browsers
	// (if I recall correctly, in Safari when XHR is done from iframes).
	// Also, some logic in client.js checks for "https://".  So, disallow
	// relative URLs.
	this.ensureAbsoluteURLs_();

	this.ensureSameOrigin_();
};

/**
 * @private
 */
cw.net.ExpandedHttpEndpoint_.prototype.ensureAbsoluteURLs_ = function() {
	if((this.primaryUrl.indexOf("http://") == 0 || this.primaryUrl.indexOf("https://") == 0) &&
	(this.secondaryUrl.indexOf("http://") == 0 || this.secondaryUrl.indexOf("https://") == 0)) {
		// OK
	} else {
		throw Error("primaryUrl and secondUrl must be absolute URLs "+
			"with http or https scheme");
	}
};

/**
 * Ensure that primaryWindow has the same origin as primaryUrl.
 * Ensure that secondaryWindow has the same origin as secondaryUrl.
 * @private
 */
cw.net.ExpandedHttpEndpoint_.prototype.ensureSameOrigin_ = function() {
	// Note: URLs for iframes can change, but we hold a reference to
	// its window, not the iframe itself.  But, bad things might happen if
	// we later make requests on a "dead" window.
	var primaryWindowHref = this.primaryWindow.location.href;
	if(!goog.uri.utils.haveSameDomain(this.primaryUrl, primaryWindowHref)) {
		throw Error("primaryWindow not same origin as primaryUrl: " + primaryWindowHref);
	}
	var secondaryWindowHref = this.secondaryWindow.location.href;
	if(!goog.uri.utils.haveSameDomain(this.secondaryUrl, secondaryWindowHref)) {
		throw Error("secondaryWindow not same origin as secondaryUrl: " + secondaryWindowHref);
	}
};

cw.net.ExpandedHttpEndpoint_.prototype.__reprPush__ = function(sb, stack) {
	sb.push("<ExpandedHttpEndpoint_ primaryUrl=");
	cw.repr.reprPush(this.primaryUrl, sb, stack);
	sb.push(", secondaryUrl=");
	cw.repr.reprPush(this.secondaryUrl, sb, stack);
	sb.push(">");
};



/**
 * @typedef {
 * 	cw.net.SocketEndpoint|
 * 	cw.net.ExpandedSocketEndpoint_|
 * 	cw.net.HttpEndpoint|
 * 	cw.net.ExpandedHttpEndpoint_}
 */
cw.net.Endpoint;


/**
 * The first frame we must see from an HTTP transport.
 * @type {!cw.net.Frame}
 * @const
 */
cw.net.HTTP_RESPONSE_PREAMBLE = new cw.net.CommentFrame(";)]}");

/**
 * The Minerva-level protocol version.
 * @type {number}
 * @const
 */
cw.net.PROTOCOL_VERSION = 2;

/**
 * The default maximum duration for long-polling HTTP transports.
 * @type {number}
 * @const
 */
cw.net.DEFAULT_HTTP_LONGPOLL_DURATION = 25000;

/**
 * The default maximum duration for streaming HTTP transports.
 * @type {number}
 * @const
 */
cw.net.DEFAULT_HTTP_STREAMING_DURATION = (3600 - 20) * 1000;

/**
 * The heartbeat interval for non-HTTP transports, in milliseconds.  If not 0,
 * (no heartbeat), try to keep it divisible by 1000 to avoid wasted bandwidth.
 * If larger, it takes longer to detect a hung transport.
 * @type {number}
 * @const
 */
cw.net.HEARTBEAT_INTERVAL = 10000;

/**
 * The maximum duration a round trip should take, in milliseconds.  This
 * includes any underlying TCP retransmits that TCP needs.  Thus, this is
 * not like a ping time, but rather a "TCP round trip time".
 * @type {number}
 * @const
 */
cw.net.DEFAULT_RTT_GUESS = 3000;

/**
 * The maximum variance we expect for the "RTT guess" above.
 * @type {number}
 * @const
 */
cw.net.DEFAULT_RTT_VARIANCE = 1500;

/**
 * The worst download speed we expect to see, in bytes/sec.
 * @type {number}
 * @const
 */
cw.net.DEFAULT_DL_SPEED = 3 * 1024;

/**
 * The maximum duration we expect the Minerva server to freeze.
 * @type {number}
 * @const
 */
cw.net.MAX_SERVER_JANK = 2000;

/**
 * The maximum frame length we expect to receive, in bytes.
 * @type {number}
 * @const
 */
cw.net.MAX_FRAME_LENGTH = 1024 * 1024;



/**
 * The HTTP streaming mode.
 * @enum {number}
 * @private
 */
cw.net.HttpStreamingMode = {
	NO_STREAMING: 1, // don't stream
	STREAMING: 2, // do stream, with normal maxInactivity
	STREAMING_PARANOID: 3 // do stream, with lower maxInactivity.
	// STREAMING_PARANOID is not really implemented yet.
};



/**
 * An interface for an object that decides what kind of transport to use,
 * and gets feedback about whether a transport is working.
 * @interface
 */
cw.net.IStreamPolicy = function() {
};

/**
 * @return {!cw.net.HttpStreamingMode}
 */
cw.net.IStreamPolicy.prototype.getHttpStreamingMode = function() {
};



/**
 * A basic default stream policy.  Note: this doesn't do HTTP streaming yet,
 * but it will once we have automatic negotation.
 * @constructor
 * @implements {cw.net.IStreamPolicy}
 */
cw.net.DefaultStreamPolicy = function() {

};

/**
 * @return {!cw.net.HttpStreamingMode}
 */
cw.net.DefaultStreamPolicy.prototype.getHttpStreamingMode = function() {
	return cw.net.HttpStreamingMode.NO_STREAMING;
};



/**
 * @return {string} A random streamId, usually with 25 or 26 characters.
 * @private
 */
cw.net.makeStreamId_ = function() {
	return cw.string.getCleanRandomString() + cw.string.getCleanRandomString();
};



/**
 * An interface for string-based communication that abstracts
 * away the Comet logic and transports.
 *
 * You don't have to use this interface; you can just set stream.onstring and
 * stream.onreset.  If you do use this interface, use stream.bindToProtocol to
 * conveniently bind ClientStream's onstring and onreset to the corresponding
 * methods in this interface.
 * @interface
 */
cw.net.IStringProtocol = function() {
};

/**
 * Called when the local *Stream object associated with this protocol
 * has started.  On the server, this is usually called after the client
 * attaches their first transport.  On the client, this is called when
 * you call {@code stream.start()}.
 *
 * You'll want to keep the stream around with {@code self.stream = stream}.
 *
 * @param {!cw.net.ClientStream} stream The stream associated with this protocol
 */
cw.net.IStringProtocol.prototype.streamStarted = function(stream) {
};

/**
 * Called when this stream has reset for any reason.  See {@link #onreset} docs.
 *
 * @param {string} reasonString Textual reason why stream has reset.
 * 	String contains only characters in inclusive range 0x20 - 0x7E.
 * @param {boolean} applicationLevel
 */
cw.net.IStringProtocol.prototype.streamReset = function(reasonString, applicationLevel) {
};

/**
 * Called when a string has been received from the peer.  See {@link #onstring}
 * docs.
 *
 * @param {string} s The restricted string
 */
cw.net.IStringProtocol.prototype.stringReceived = function(s) {
};



/**
 * An interface for string-based communication that allows for
 * question-answer-notify.
 * @interface
 */
cw.net.IQANProtocol = function() {
};

/**
 * Called when the local *Stream object associated with this protocol
 * has started.  On the server, this is usually called after the client
 * attaches their first transport.  On the client, this is called when
 * you call {@code stream.start()}.
 *
 * You'll want to keep the stream around with {@code this.stream = stream}.
 * You'll want to keep the QANHelper around with {@code this.qanHelper = qanHelper}.
 *
 * You must not call {@code stream.sendString}; use {@code qanHelper.ask} or
 * {@code qanHelper.notify} for all of your communication.
 *
 * @param {!cw.net.ClientStream} stream The stream associated with this protocol
 * @param {!cw.net.QANHelper} qanHelper The {@code QANHelper} coupled with
 * 	the {@code ClientStream}.
 */
cw.net.IQANProtocol.prototype.streamStarted = function(stream, qanHelper) {
};

/**
 * Called when this stream has reset for any reason.  See {@link #onreset} docs.
 *
 * @param {string} reasonString Textual reason why stream has reset.
 * 	String contains only characters in inclusive range 0x20 - 0x7E.
 * @param {boolean} applicationLevel
 */
cw.net.IQANProtocol.prototype.streamReset = function(reasonString, applicationLevel) {
};

/**
 * Called when a Question or Notification has been received from the peer.
 *
 * @param {string} body The QAN body from the peer.  Always a restricted string.
 *
 * @param {boolean} isQuestion True if the QAN body arrived as a question that
 * 	can be answered, False if it arrived as a Notification.  If it is a question,
 * 	this method's return value (or Deferred) will be used as the answer.
 * 	Answer *must* be a restricted string.  If {@code cw.net.KnownError}
 * 	is raised (or errbacked), the string value of the {@code cw.net.KnownError}
 * 	will be sent as the error-answer.  If another exception is raised,
 * 	an uninformative unknown-error-answer will be sent to the peer.
 *
 * @return {(string|goog.async.Deferred)} If {@code isQuestion}, an answer to
 * 	the question.
 * @throws {cw.net.KnownError} When an error-answer is desired.
 */
cw.net.IQANProtocol.prototype.bodyReceived = function(body, isQuestion) {
};



/**
 * @private
 */
cw.net.throwErrorIntoWindow_ = function(error) {
	goog.global.setTimeout(function() {
		// The stack trace is clobbered when the error is rethrown.  Append
		// the stack trace to the message if available.  Since no one is
		// capturing this error, the stack trace will be printed to the
		// debug console.
		if (goog.DEBUG && goog.isDef(error.message) && error.stack) {
			error.message += '\n' + error.stack;
		}
		throw error;
	}, 0);
};


/**
 * This is an {@code IStringProtocol} that makes your {@code IQANProtocol} work.
 * See {@code IQANProtocol}.
 *
 * @param {*} qanProtocol
 * @param {boolean=} validateBodies Validate locally-created bodies of questions
 * 	and answers?  Default true.  Set to {@code false} if you're sure your
 * 	application works correctly.
 * @param {boolean=} throwIntoWindow If true, QANProtocolWrapper
 * 	will log errors as WARNINGs, without also throwing the errors into the
 * 	window.  Default is true.
 *
 * @implements {cw.net.IStringProtocol}
 * @constructor
 */
cw.net.QANProtocolWrapper = function(qanProtocol, validateBodies, throwIntoWindow) {
	if(!goog.isDef(validateBodies)) {
		validateBodies = true;
	}

	if(!goog.isDef(throwIntoWindow)) {
		throwIntoWindow = true;
	}

	/**
	 * @type {!cw.net.IQANProtocol}
	 */
	this.qanProtocol = /** @type {!cw.net.IQANProtocol} */ (qanProtocol);

	/**
	 * @type {boolean}
	 * @private
	 */
	this.validateBodies_ = validateBodies;

	/**
	 * @type {boolean}
	 * @private
	 */
	this.throwIntoWindow_ = throwIntoWindow;
};

/**
 * @type {!goog.debug.Logger}
 * @protected
 */
cw.net.QANProtocolWrapper.prototype.logger_ =
	goog.debug.Logger.getLogger('cw.net.QANProtocolWrapper');

/**
 * @param {string} message
 * @param {!Error} error
 */
cw.net.QANProtocolWrapper.prototype.logError_ = function(message, error) {
	this.logger_.warning(message, error);

	// Since the user of Minerva might not have a logger set up, throw
	// the error into the window as well.  goog.async.Deferred does this too.
	if(this.throwIntoWindow_) {
		cw.net.throwErrorIntoWindow_(error);
	}
};

/**
 * @param {!cw.net.QANFrame} qanFrame
 */
cw.net.QANProtocolWrapper.prototype.sendQANFrame_ = function(qanFrame) {
	this.stream.sendString(cw.net.qanFrameToString(qanFrame), this.validateBodies_);
};

/**
 * @param {string} reason
 */
cw.net.QANProtocolWrapper.prototype.fatalError_ = function(reason) {
	this.stream.reset("QANHelper said: "  + reason);
};

/**
 * @param {!cw.net.ClientStream} stream
 */
cw.net.QANProtocolWrapper.prototype.streamStarted = function(stream) {
	/**
	 * @type {!cw.net.ClientStream}
	 */
	this.stream = stream;
	/**
	 * @type {!cw.net.QANHelper}
	 */
	this.qanHelper = new cw.net.QANHelper(
		/* Coerce because QANHelper works with any type, but IQANProtocol
		 * always get a string. */
		/** @type {function(*, boolean)} */ (
			cw.net.STANDALONE_CLIENT_BUILD_ ?
				goog.bind(this.qanProtocol['bodyReceived'], this.qanProtocol) :
				goog.bind(this.qanProtocol.bodyReceived, this.qanProtocol)),
		goog.bind(this.logError_, this),
		goog.bind(this.sendQANFrame_, this),
		goog.bind(this.fatalError_, this));
	if(cw.net.STANDALONE_CLIENT_BUILD_) {
		this.qanProtocol['streamStarted'].call(this.qanProtocol, this.stream, this.qanHelper);
	} else {
		this.qanProtocol.streamStarted(this.stream, this.qanHelper);
	}
};

/**
 * @param {string} reasonString
 * @param {boolean} applicationLevel
 */
cw.net.QANProtocolWrapper.prototype.streamReset = function(reasonString, applicationLevel) {
	this.qanHelper.failAll("Stream reset " +
		"applicationLevel=" + cw.repr.repr(applicationLevel) +
		", reason: " + reasonString);
	if(cw.net.STANDALONE_CLIENT_BUILD_) {
		this.qanProtocol['streamReset'].call(this.qanProtocol, reasonString, applicationLevel);
	} else {
		this.qanProtocol.streamReset(reasonString, applicationLevel);
	}
};

/**
 * @param {string} s
 */
cw.net.QANProtocolWrapper.prototype.stringReceived = function(s) {
	try {
		var qanFrame = cw.net.stringToQANFrame(s);
	} catch(e) {
		if(!(e instanceof cw.net.InvalidQANFrame)) {
			throw e;
		}
		this.stream.reset("Bad QAN frame.  Did peer send a non-QAN string?");
		return;
	}
	this.qanHelper.handleQANFrame(qanFrame);
};



/**
 * States that a ClientStream can be in.
 * @enum {string}
 * @private
 */
cw.net.StreamState_ = {
	// Note that these strings are used for < and > comparison
	UNSTARTED: "1_UNSTARTED",
	WAITING_RESOURCES: "2_WAITING_RESOURCES",
	STARTED: "3_STARTED",
	RESETTING: "4_RESETTING",
	DISCONNECTED: "5_DISCONNECTED"
};



/**
 * A context object used as the context in calls to
 * ClientStream.(onstring|onreset|ondisconnect).  ClientStream uses this as the
 * context rather than the ClientStream object itself to prevent users from
 * messing up the ClientStream object's state with their `this.x` mutations.
 *
 * @param {!cw.net.ClientStream} stream
 *
 * @constructor
 */
cw.net.UserContext = function(stream) {
	/**
	 * @type {!cw.net.ClientStream}
	 */
	this.stream = stream;
};

/**
 * @param {!Array.<string>} sb
 * @param {!Array.<*>} stack
 */
cw.net.UserContext.prototype.__reprPush__ = function(sb, stack) {
	sb.push("<UserContext for ");
	cw.repr.reprPush(this.stream, sb, stack);
	sb.push(">");
};

/**
 * @return {string}
 */
cw.net.UserContext.prototype.toString = function() {
	return cw.repr.repr(this);
};


/**
 * @param {number} transportNumber
 * @param {boolean} isPrimary
 * @param {boolean} streamingFromPeer
 * @param {boolean} streamingToPeer
 * @extends {cw.record.Record}
 * @constructor
 */
cw.net.TransportInfo = function(transportNumber, isPrimary, streamingFromPeer, streamingToPeer) {
	cw.record.Record.call(this, 'TransportInfo', [transportNumber, isPrimary, streamingFromPeer, streamingToPeer]);
	/** @type {number} */
	this.transportNumber = transportNumber;
	/** @type {boolean} */
	this.isPrimary = isPrimary;
	/** @type {boolean} */
	this.streamingFromPeer = streamingFromPeer;
	/** @type {boolean} */
	this.streamingToPeer = streamingToPeer;

};
goog.inherits(cw.net.TransportInfo, cw.record.Record);



/**
 * The client-side representation of a Minerva stream.
 *
 * ClientStream is sort-of analogous to {@code twisted.internet.tcp.Connection}.
 * ClientStream can span many TCP connections/HTTP requests.
 *
 * @param {!cw.net.Endpoint} endpoint
 * @param {!cw.net.IStreamPolicy=} streamPolicy
 * @param {!cw.eventual.CallQueue=} callQueue
 *
 * @constructor
 * @implements {RWPropertiesClientStream}
 * @extends {goog.Disposable}
 */
cw.net.ClientStream = function(endpoint, streamPolicy, callQueue) {
	goog.Disposable.call(this);

	/**
	 * TODO: add a method to change the endpoint while the ClientStream is
	 * running.  This method may need to dispose existing transports.
	 * @type {!cw.net.Endpoint}
	 * @private
	 */
	this.endpoint_ = endpoint;

	/**
	 * The stream policy object.
	 * @type {!cw.net.IStreamPolicy}
	 * @private
	 */
	this.streamPolicy_ = streamPolicy ? streamPolicy : new cw.net.DefaultStreamPolicy();

	/**
	 * @type {!cw.eventual.CallQueue}
	 * @private
	 */
	this.callQueue_ = callQueue ? callQueue : cw.eventual.theCallQueue;

	/**
	 * A set of all currently-online transports.
	 * @type {!goog.structs.Set}
	 * @private
	 */
	this.transports_ = new goog.structs.Set();

	/**
	 * This stream's unique ID.  Note that client may pick a bad ID that
	 * collides with another bad ID, but this is entirely the client's fault.
	 * @type {string}
	 */
	this.streamId = cw.net.makeStreamId_();

	/**
	 * The send queue.  Outgoing strings land here before being sent to the
	 * peer.
	 * @type {!cw.net.Queue}
	 * @private
	 */
	this.queue_ = new cw.net.Queue();

	/**
	 * The receive window.  Incoming strings land here before being sent to
	 * a {@link cw.net.IStringProtocol}.
	 * @type {!cw.net.Incoming}
	 * @private
	 */
	this.incoming_ = new cw.net.Incoming();

	/**
	 * The numeric key for our window.onload listener (if we listen).
	 * @type {?number}
	 * @private
	 */
	this.windowLoadEvent_ = null;

	/**
	 * An Array of {@code XDRFrame}s that this ClientStream is using.
	 * @type {!Array.<!cw.net.XDRFrame>}
	 * @private
	 */
	this.xdrFramesInUse_ = [];

	/**
	 * @type {!cw.net.UserContext}
	 * @private
	 */
	this.userContext_ = new cw.net.UserContext(this);

	/**
	 * Just for optimization: {@code this.tryToSendSoonCallback_} bound to
	 * {@code this}.
	 * @type {!Function}
	 * @private
	 */
	this.boundTryToSendSoonCallback_ = goog.bind(this.tryToSendSoonCallback_, this);

	// For WebKit browsers, we need an ugly hack to prevent the loading
	// spinner/throbber from spinning indefinitely if there is an open XHR
	// request.  If window.onload fires, abort HTTP requests, wait ~100ms,
	// then tryToSend_.  Note that it may never fire if window is already
	// loaded, or if it never finishes loading.
	if(goog.userAgent.WEBKIT) {
		this.windowLoadEvent_ = goog.events.listenOnce(
			goog.global, goog.events.EventType.LOAD,
			this.restartHttpRequests_, false, this);
	}
};
goog.inherits(cw.net.ClientStream, goog.Disposable);

/**
 * @type {!goog.debug.Logger}
 * @protected
 */
cw.net.ClientStream.prototype.logger_ =
	goog.debug.Logger.getLogger('cw.net.ClientStream');

/**
 * The last SACK we have received.
 * @type {!cw.net.SACK}
 * @private
 */
cw.net.ClientStream.prototype.lastSackSeenByClient_ = new cw.net.SACK(-1, []);

/**
 * The last SACK the server has definitely received, as far as we know.  This
 * information is used to decide whether to (re)send a SackFrame.
 * @type {!cw.net.SACK}
 * @private
 */
cw.net.ClientStream.prototype.lastSackSeenByServer_ = new cw.net.SACK(-1, []);

/**
 * Maximum number of undelivered strings allowed in {@code this.incoming_},
 * before ignoring further strings over the offending transport (and closing it).
 * @type {number}
 */
cw.net.ClientStream.prototype.maxUndeliveredStrings = 50;

/**
 * Maximum number of undelivered bytes allowed in {@code this.incoming_},
 * before ignoring further strings over the offending transport (and closing it).
 * @type {number}
 */
cw.net.ClientStream.prototype.maxUndeliveredBytes = 1 * 1024 * 1024;

/**
 * The function to call when the ClientStream has received a string.
 *
 * @type {?function(string):*}
 */
cw.net.ClientStream.prototype.onstring = null;

/**
 * The function to call when you call {@code ClientStream.start}
 *
 * @type {?function(!cw.net.ClientStream):*}
 */
cw.net.ClientStream.prototype.onstarted = null;

/**
 * The function to call when a new transport is created.
 *
 * @type {?function(!cw.net.TransportInfo):*}
 */
cw.net.ClientStream.prototype.ontransportcreated = null;

/**
 * The function to call when a transport is destroyed.
 *
 * @type {?function(!cw.net.TransportInfo):*}
 */
cw.net.ClientStream.prototype.ontransportdestroyed = null;


/**
 * The function to call when this stream has reset, either internally by
 * ClientStream, or a call to ClientStream.reset, or by a ResetFrame from the
 * peer.
 *
 * The first parameter is a textual reason for why the stream has reset.  This
 * string contains only characters in inclusive range 0x20 - 0x7E.
 *
 * The second parameter is whether the reset was an application-level reset
 * (vs. stream internal reset).
 *
 * @type {?function(string, boolean):*}
 */
cw.net.ClientStream.prototype.onreset = null;

/**
 * The function to call after the ClientStream is completely done.
 * @type {Function}
 */
cw.net.ClientStream.prototype.ondisconnect = null;

/**
 * The setTimeout ticket for a delayed call to tryToSend_, or null.
 * @type {?number}
 * @private
 */
cw.net.ClientStream.prototype.sendTicket_ = null;

/**
 * Has the server ever known about the stream?  Set to `true` after
 * we get a {@link cw.net.StreamCreatedFrame}.  Never set back to `false`.
 *
 * If `false`, the transports that ClientStream makes must have HelloFrame with
 * `requestNewStream`.
 * @type {boolean}
 * @private
 */
cw.net.ClientStream.prototype.streamExistedAtServer_ = false;

/**
 * Is a secondary transport suppressed because stream might not exist on
 * server yet?
 * @type {boolean}
 * @private
 */
cw.net.ClientStream.prototype.secondaryIsWaitingForStreamToExist_ = false;

/**
 * State the stream is in.
 * @type {!cw.net.StreamState_}
 * @private
 */
cw.net.ClientStream.prototype.state_ = cw.net.StreamState_.UNSTARTED;

/**
 * Counter used to uniquely assign a transportNumber for the
 * transports in this stream.
 * @type {number}
 * @private
 */
cw.net.ClientStream.prototype.transportCount_ = -1;

/**
 * The primary transport, for receiving S2C strings (and possibly sending C2S
 * strings).
 * @type {cw.net.ClientTransport|cw.net.DoNothingTransport}
 * @private
 */
cw.net.ClientStream.prototype.primaryTransport_ = null;

/**
 * The secondary transport.  It is created to send strings/sacks if the primary
 * transport cannot send anything after it has been created.  This is the
 * case for any HTTP transport.
 * @type {cw.net.ClientTransport|cw.net.DoNothingTransport}
 * @private
 */
cw.net.ClientStream.prototype.secondaryTransport_ = null;

/**
 * The transport dedicated to resetting the stream.  If primary transport is
 * capable of sending after being created, this type of transport is not
 * created, and the ResetFrame is sent over the primary transport instead.
 * @type {cw.net.ClientTransport}
 * @private
 */
cw.net.ClientStream.prototype.resettingTransport_ = null;

/**
 * The current penalty for the ClientStream.  Increased when transports die with
 * errors that suggest that the stream is permanently broken.  Reset back to
 * 0 when a transport with no penalty goes offline.
 * @type {number}
 * @private
 */
cw.net.ClientStream.prototype.streamPenalty_ = 0;

/**
 * How many times in a row the primary transport has been followed
 * by a {@link cw.net.DoNothingTransport}.
 * @type {number}
 * @private
 */
cw.net.ClientStream.prototype.primaryDelayCount_ = 0;

/**
 * How many times in a row the secondary transport has been followed
 * by a {@link cw.net.DoNothingTransport}.
 * @type {number}
 * @private
 */
cw.net.ClientStream.prototype.secondaryDelayCount_ = 0;

/**
 * @param {!Array.<string>} sb
 * @param {!Array.<*>} stack
 */
cw.net.ClientStream.prototype.__reprPush__ = function(sb, stack) {
	sb.push('<ClientStream id=');
	cw.repr.reprPush(this.streamId, sb, stack);
	sb.push(', state=', String(this.state_));
	sb.push(', primary=');
	cw.repr.reprPush(this.primaryTransport_, sb, stack);
	sb.push(', secondary=');
	cw.repr.reprPush(this.secondaryTransport_, sb, stack);
	sb.push(', resetting=');
	cw.repr.reprPush(this.resettingTransport_, sb, stack);
	sb.push('>');
};

/**
 * @return {string}
 */
cw.net.ClientStream.prototype.toString = function() {
	return cw.repr.repr(this);
};

/**
 * @return {!cw.net.UserContext} The user context object (the object that is
 * 	`this` in calls to (onstring|onreset|ondisconnect)).
 */
cw.net.ClientStream.prototype.getUserContext = function() {
	return this.userContext_;
};

/**
 * @param {!cw.net.IStringProtocol} proto The protocol to bind this
 * 	ClientStream's {@code on*} methods to.  If you changed your
 * 	protocol's methods, you must call {@code bindToProtocol} again.
 */
cw.net.ClientStream.prototype.bindToProtocol = function(proto) {
	// In standalone Minerva, we use 'quotedMethods' because the user will
	// have normal method names, not Compiler-munged method names.
	if(cw.net.STANDALONE_CLIENT_BUILD_) {
		if(!goog.isDef(proto['streamStarted'])) {
			throw Error("Protocol is missing required method streamStarted");
		}
		if(!goog.isDef(proto['streamReset'])) {
			throw Error("Protocol is missing required method streamReset");
		}
		if(!goog.isDef(proto['stringReceived'])) {
			throw Error("Protocol is missing required method stringReceived");
		}
		this.onstarted = goog.bind(proto['streamStarted'], proto);
		this.onreset = goog.bind(proto['streamReset'], proto);
		this.onstring = goog.bind(proto['stringReceived'], proto);
		// Optional methods
		this.ontransportcreated = goog.isDef(proto['transportCreated']) ?
			goog.bind(proto['transportCreated'], proto) : null;
		this.ontransportdestroyed = goog.isDef(proto['transportDestroyed']) ?
			goog.bind(proto['transportDestroyed'], proto) : null;
	} else {
		if(!goog.isDef(proto.streamStarted)) {
			throw Error("Protocol is missing required method streamStarted");
		}
		if(!goog.isDef(proto.streamReset)) {
			throw Error("Protocol is missing required method streamReset");
		}
		if(!goog.isDef(proto.stringReceived)) {
			throw Error("Protocol is missing required method stringReceived");
		}
		this.onstarted = goog.bind(proto.streamStarted, proto);
		this.onreset = goog.bind(proto.streamReset, proto);
		this.onstring = goog.bind(proto.stringReceived, proto);
		// Optional methods
		this.ontransportcreated = goog.isDef(proto.transportCreated) ?
			goog.bind(proto.transportCreated, proto) : null;
		this.ontransportdestroyed = goog.isDef(proto.transportDestroyed) ?
			goog.bind(proto.transportDestroyed, proto) : null;
	}
};

/**
 * @return {number} The highest seqNum that was written to the peer over any
 * 	currently-open transport, or -1 if none.
 * @private
 */
cw.net.ClientStream.prototype.getHighestSeqNumSent_ = function() {
	var nums = [-1]; // have -1 in case no primary or secondary
	if(this.primaryTransport_) {
		nums.push(this.primaryTransport_.ourSeqNum_);
	}
	if(this.secondaryTransport_) {
		nums.push(this.secondaryTransport_.ourSeqNum_);
	}
	return Math.max.apply(Math.max, nums);
};

/**
 * @param {!cw.net.SACK} sack
 * @return {boolean} Have we already written sack `sack` over any
 * 	currently-open transport?
 */
cw.net.ClientStream.prototype.hasAlreadyWrittenSack_ = function(sack) {
	if(this.primaryTransport_ &&
	sack.equals(this.primaryTransport_.lastSackWritten_)) {
		return true;
	} else if(this.secondaryTransport_ &&
	sack.equals(this.secondaryTransport_.lastSackWritten_)) {
		return true;
	} else {
		return false;
	}
};

/**
 * @private
 */
cw.net.ClientStream.prototype.ensureQueueIntegrity_ = function() {
	if(!this.streamExistedAtServer_) {
		goog.asserts.assert(
			this.queue_.getQueuedCount() == 0 ||
			this.queue_.getQueuedKeys()[0] === 0,
			"Stream does not exist at server, but we have already " +
			"removed item #0 from our queue?");
	}
};

/**
 * @param {boolean} maybeNeedToSendStrings
 * @param {boolean} maybeNeedToSendSack
 * @return {string} Some text to be used in a log message
 * @private
 */
cw.net.ClientStream.prototype.getSendingWhatText_ = function(
maybeNeedToSendStrings, maybeNeedToSendSack) {
	if(maybeNeedToSendStrings && maybeNeedToSendSack) {
		return "string(s)+SACK";
	} else if(maybeNeedToSendStrings) {
		return "string(s)";
	} else if(maybeNeedToSendSack) {
		return "SACK";
	} else {
		return "nothing!?";
	}
};

/**
 * @private
 */
cw.net.ClientStream.prototype.tryToSend_ = function() {
	this.ensureQueueIntegrity_();
	if(this.state_ < cw.net.StreamState_.STARTED) {
		return;
	}
	goog.asserts.assert(
		this.state_ == cw.net.StreamState_.STARTED,
		"tryToSend_: state is " + this.state_);

	// No need to tryToSend_ soon, since we're doing it right now
	this.cancelTryToSendSoon_();

	var haveQueueItems = (this.queue_.getQueuedCount() != 0);
	var currentSack = this.incoming_.getSACK();
	var maybeNeedToSendSack =
		!currentSack.equals(this.lastSackSeenByServer_) &&
		!this.hasAlreadyWrittenSack_(currentSack);
	var highestSeqNumSent = this.getHighestSeqNumSent_();
	var maybeNeedToSendStrings =
		haveQueueItems && highestSeqNumSent < this.queue_.getLastItemNumber();

//	this.logger_.finest('In tryToSend_, ' + cw.repr.repr({
//		queue: this.queue_, currentSack: currentSack,
//		lastSackSeenByServer_: this.lastSackSeenByServer_,
//		haveQueueItems: haveQueueItems,
//		maybeNeedToSendSack: maybeNeedToSendSack,
//		maybeNeedToSendStrings: maybeNeedToSendStrings,
//		highestSeqNumSent: highestSeqNumSent}));

	if(maybeNeedToSendStrings || maybeNeedToSendSack) {
		var sendingWhat = this.getSendingWhatText_(
			maybeNeedToSendStrings, maybeNeedToSendSack);

		// After we're in STARTED, we always have a primary transport,
		// even if its underlying object hasn't connected yet.
		if(this.primaryTransport_.canFlushMoreThanOnce_) {
			this.logger_.finest(
				"tryToSend_: writing " + sendingWhat + " to primary");
			if(maybeNeedToSendSack) {
				this.primaryTransport_.writeSack_(currentSack);
			}
			if(maybeNeedToSendStrings) {
				this.primaryTransport_.writeStrings_(
					this.queue_, highestSeqNumSent + 1);
			}
			this.primaryTransport_.flush_();
		// For robustness reasons, wait until we know that the stream
		// exists on server before creating secondary transports.
		} else if(this.secondaryTransport_ == null) {
			if(!this.streamExistedAtServer_) {
				this.logger_.finest("tryToSend_: not creating a secondary " +
					"because stream might not exist on server");
				this.secondaryIsWaitingForStreamToExist_ = true;
			} else {
				this.logger_.finest(
					"tryToSend_: creating secondary to send " + sendingWhat);
				this.secondaryTransport_ = this.createNewTransport_(false, true);
				if(!this.secondaryTransport_) {
					return;
				}
				// No need to writeSack_ because a sack is included in the HelloFrame.
				if(maybeNeedToSendStrings) {
					this.secondaryTransport_.writeStrings_(
						this.queue_, highestSeqNumSent + 1);
				}
				this.secondaryTransport_.flush_();
			}
		} else {
			this.logger_.finest(
				"tryToSend_: need to send " + sendingWhat + ", but can't right now");
		}
	}
};

/**
 * @private
 */
cw.net.ClientStream.prototype.cancelTryToSendSoon_ = function() {
	if(this.sendTicket_ != null) {
		this.callQueue_.clock.clearTimeout(this.sendTicket_);
		this.sendTicket_ = null;
	}
};

/**
 * @private
 */
cw.net.ClientStream.prototype.tryToSendSoonCallback_ = function() {
	this.sendTicket_ = null;
	this.tryToSend_();
};

/**
 * @private
 */
cw.net.ClientStream.prototype.tryToSendSoon_ = function() {
	// Try to send in 6ms because most browsers clamp setTimeout
	// to 4ms (as HTML5[1] demands), and our 6ms might give user's
	// 0ms-5ms timeouts a chance to run first (and send more strings).
	// [1] http://www.w3.org/TR/html5/timers.html#timers
	// Test page: http://www.belshe.com/test/timers.html
	if(this.sendTicket_ == null) {
		this.sendTicket_ = this.callQueue_.clock.setTimeout(
			this.boundTryToSendSoonCallback_, 6);
	}
};

/**
 * WebKit spinner-killer hack.
 * See the JSDoc in the constructor near {@code this.windowLoadEvent_}.
 * @private
 */
cw.net.ClientStream.prototype.restartHttpRequests_ = function() {
	this.windowLoadEvent_ = null;
	if(this.primaryTransport_ && this.primaryTransport_.isHttpTransport_()) {
		this.logger_.info("restartHttpRequests_: aborting primary");
		this.primaryTransport_.abortToStopSpinner_();
	}
	if(this.secondaryTransport_ && this.secondaryTransport_.isHttpTransport_()) {
		this.logger_.info("restartHttpRequests_: aborting secondary");
		this.secondaryTransport_.abortToStopSpinner_();
	}
	// Don't abort resettingTransport_.
};

/**
 * Send restricted string `string` to the peer.  String MUST contain only
 * 	characters in inclusive range U+0020 (SPACE) - U+007E (~).  You may call
 * 	this method even before the ClientStream is started with {@link #start}.
 * 	String is always queued for sending "very soon", so multiple calls will
 * 	not lead to redundant network activity.
 * @param {string} string Restricted string to send.
 * @param {boolean=} validate Throw Error if string is not a restricted string?
 * 	Default true.  Set this to `false` for a slight speedup.
 */
cw.net.ClientStream.prototype.sendString = function(string, validate) {
	if(!goog.isDef(validate)) {
		validate = true;
	}
	if(this.state_ > cw.net.StreamState_.STARTED) {
		throw Error("sendString: Can't send in state " + this.state_);
	}
	if(validate) {
		if(!goog.isString(string)) {
			throw Error("sendString: not a string: " + cw.repr.repr(string));
		}
		if(!cw.net.isRestrictedString(string)) {
			throw Error("sendString: string " +
				"has illegal chars: " + cw.repr.repr(string));
		}
	}
	this.queue_.append(string);
	this.tryToSendSoon_();
};

/**
 * Get the appropriate TransportType_ for our current endpoint.
 * @private
 * @return {!cw.net.TransportType_}
 */
cw.net.ClientStream.prototype.getTransportType_ = function() {
	var transportType;
	if(this.endpoint_ instanceof cw.net.ExpandedHttpEndpoint_) {
		var httpStreamingMode = this.streamPolicy_.getHttpStreamingMode();
		if(httpStreamingMode == cw.net.HttpStreamingMode.NO_STREAMING) {
			transportType = cw.net.TransportType_.XHR_LONGPOLL;
		} else {
			transportType = cw.net.TransportType_.XHR_STREAM;
		}
		// TODO: lower maxInactivity for STREAMING_PARANOID.
	} else if(this.endpoint_ instanceof cw.net.ExpandedSocketEndpoint_) {
		transportType = cw.net.TransportType_.FLASH_SOCKET;
	} else {
		throw Error("Don't support endpoint " + cw.repr.repr(this.endpoint_));
	}
	return transportType;
};

/**
 * @private
 * @return {!cw.net.ClientTransport} The newly-instantiated transport.
 * This method exists so that it can be overriden in tests.
 */
cw.net.ClientStream.prototype.instantiateTransport_ =
function(callQueue, stream, transportNumber, transportType,
endpoint, becomePrimary) {
	return new cw.net.ClientTransport(
		callQueue, stream, transportNumber, transportType,
		endpoint, becomePrimary);
};

/**
 * @param {boolean} becomePrimary Whether this transport should become
 * 	primary transport.
 * @param {boolean} tellProtocol Call ontransportcreated? (if defined)
 * @return {cw.net.ClientTransport} The newly-created transport, or null, if
 * 	a transport was abandoned because ontransportcreated called reset/dispose.
 */
cw.net.ClientStream.prototype.createNewTransport_ = function(becomePrimary, tellProtocol) {
	var transportType = this.getTransportType_();
	this.transportCount_ += 1;
	var transport = this.instantiateTransport_(
		this.callQueue_, this, this.transportCount_, transportType,
			this.endpoint_, becomePrimary);
	this.logger_.finest("Created: " + transport.getDescription_());
	if(tellProtocol) {
		if(this.ontransportcreated) {
			var info = transport.getInfo();
			try {
				this.ontransportcreated.call(this.userContext_, info);
			} catch(error) {
				this.logger_.warning(
					"ontransportcreated raised uncaught exception", error);
				cw.net.throwErrorIntoWindow_(error);
			}
		}
		// Under ontransportcreated, the state may have changed completely!
		// The ClientStream may be RESETTING or disposed.
		if(this.isResettingOrDisposed_()) {
			return null;
		}
	}
	this.transports_.add(transport);
	return transport;
};

/**
 * Create a dummy transport that waits for N milliseconds and goes offline.
 * @param {number} delay
 * @param {number} times
 * @return {!cw.net.DoNothingTransport} The newly-created transport.
 */
cw.net.ClientStream.prototype.createWastingTransport_ = function(delay, times) {
	var transport = new cw.net.DoNothingTransport(
		this.callQueue_, this, delay, times);
	this.logger_.finest("Created: " + transport.getDescription_() +
		", delay=" + delay + ", times=" + times);
	this.transports_.add(transport);
	return transport;
};

/**
 * Called by a transport which has received indication that the stream has
 * been successfully created.  The server sends StreamCreatedFrame as the
 * first frame over *every* transport with `requestNewStream`, so this
 * method might be called more than once.  This method is idempotent.
 * @param {boolean} avoidCreatingTransports
 * @private
 */
cw.net.ClientStream.prototype.streamSuccessfullyCreated_ = function(avoidCreatingTransports) {
	this.logger_.finest('Stream is now confirmed to exist at server.');
	this.streamExistedAtServer_ = true;
	// See comment for cw.net.ClientStream.prototype.stringsReceived_
	if(this.secondaryIsWaitingForStreamToExist_ && !avoidCreatingTransports) {
		// This method is idempotent, so we should set this to false
		// to avoid calling tryToSend_ more than necessary.
		this.secondaryIsWaitingForStreamToExist_ = false;
		this.tryToSend_();
	}
};

/**
 * @param {!cw.net.SACK} lastSackSeen The last SACK frame seen by the peer.
 * @private
 */
cw.net.ClientStream.prototype.streamStatusReceived_ = function(lastSackSeen) {
	this.lastSackSeenByServer_ = lastSackSeen;
};

/**
 * Return a suitable delay for the next transport, based on transport's
 * properties (and whether it is primary/secondary).  If times=0, it is safe
 * to create a new real transport right away, even under caller's stack frame.
 *
 * @param {!(cw.net.ClientTransport|cw.net.DoNothingTransport)} transport The
 * 	previous transport.
 * @return {!Array.<number>} (Delay in milliseconds, times to repeat delay).
 * @private
 * // TODO: types for tuples
 */
cw.net.ClientStream.prototype.getDelayForNextTransport_ = function(transport) {
	var delay;
	var times;
	var isWaster = transport instanceof cw.net.DoNothingTransport;
	if(!isWaster && transport.abortedForSpinner_) {
		var _ = cw.dethrobber.getDelayToStopSpinner();
		delay = _[0];
		times = _[1];
		this.logger_.finest("getDelayForNextTransport_: " +
			cw.repr.repr({'delay': delay, 'times': times}));
		return [delay, times];
	}

	var considerDelay = transport.considerDelayingNextTransport_();
	var count;
	if(transport == this.primaryTransport_) {
		if(considerDelay) {
			count = ++this.primaryDelayCount_;
		} else if(!isWaster) {
			count = this.primaryDelayCount_ = 0;
		}
	} else { // secondaryTransport_
		if(considerDelay) {
			count = ++this.secondaryDelayCount_;
		} else if(!isWaster) {
			count = this.secondaryDelayCount_ = 0;
		}
	}
	if(isWaster || !count) {
		delay = 0;
		times = 0;
		this.logger_.finest("getDelayForNextTransport_: " +
			cw.repr.repr({'count': count, 'delay': delay, 'times': times}));
	} else {
		var base = 2000 * Math.min(count, 3);
		// Add random variance, so that if the server dies we don't get
		// hit by every client at the same time.
		var variance = Math.floor(Math.random() * 4000) - 2000;
		var oldDuration = transport.getUnderlyingDuration_();
		delay = Math.max(0, base + variance - oldDuration);
		times = delay ? 1 : 0;
		this.logger_.finest("getDelayForNextTransport_: " +
			cw.repr.repr({'count': count, 'base': base, 'variance': variance,
				'oldDuration': oldDuration, 'delay': delay, 'times': times}));
	}
	return [delay, times];
};

/**
 * ClientTransport calls this to tell ClientStream that it has disconnected.
 * @param {!cw.net.ClientTransport|cw.net.DoNothingTransport} transport
 * @private
 */
cw.net.ClientStream.prototype.transportOffline_ = function(transport) {
	var removed = this.transports_.remove(transport);
	if(!removed) {
		throw Error("transportOffline_: Transport was not removed?");
	}
	this.logger_.fine('Offline: ' + transport.getDescription_());

	var wasResettingTransport = (this.state_ == cw.net.StreamState_.RESETTING &&
		transport.wroteResetFrame_);

	// We don't tell the user about transportCreated for resettingTransport_s,
	// so don't tell them about transportDestroyed for them either.
	if(transport instanceof cw.net.ClientTransport && !wasResettingTransport) {
		if(this.ontransportdestroyed) {
			var info = transport.getInfo();
			try {
				this.ontransportdestroyed.call(this.userContext_, info);
			} catch(error) {
				this.logger_.warning(
					"ontransportdestroyed raised uncaught exception", error);
				cw.net.throwErrorIntoWindow_(error);
			}
		}
		// Under ontransportdestroyed, the state may have changed completely!
		// The ClientStream may be RESETTING or disposed.
		if(this.isResettingOrDisposed_()) {
			return null;
		}
	}

	if(!transport.penalty_) {
		this.streamPenalty_ = 0;
	} else {
		this.streamPenalty_ += transport.penalty_;
	}

	if(this.streamPenalty_ >= 1) {
		this.logger_.info("transportOffline_: Doing an internal " +
			"reset because streamPenalty_ reached limit.");
		this.internalReset_("stream penalty reached limit");
	}

	if(this.state_ > cw.net.StreamState_.STARTED) {
		if(wasResettingTransport) {
			this.logger_.fine('Disposing because resettingTransport_ is done.');
			this.dispose();
		} else {
			this.logger_.fine("Not creating a transport because " +
				"ClientStream is in state " + this.state_);
		}
	} else {
		var _ = this.getDelayForNextTransport_(transport);
		var delay = _[0];
		var times = _[1];
		if(transport == this.primaryTransport_) {
			// Must null primaryTransport_ before calling
			// this.getHighestSeqNumSent_(), so that it doesn't assume
			// primaryTransport_ is still connected.
			this.primaryTransport_ = null;
			if(!times) {
				var highestSeqNumSent = this.getHighestSeqNumSent_();
				this.primaryTransport_ = this.createNewTransport_(true, true);
				if(!this.primaryTransport_) {
					return;
				}
				// No need to writeSack_ because a sack is included in the HelloFrame.
				this.primaryTransport_.writeStrings_(this.queue_, highestSeqNumSent + 1);
			} else {
				this.primaryTransport_ = this.createWastingTransport_(delay, times);
			}
			this.primaryTransport_.flush_();
		} else if(transport == this.secondaryTransport_) {
			this.secondaryTransport_ = null;
			if(!times) {
				// More data might have been queued while the secondary transport
				// was getting a response.  It's also possible that the server didn't
				// ACK what we just sent, so we have to send it again.
				this.tryToSend_();
			} else {
				this.secondaryTransport_ = this.createWastingTransport_(delay, times);
				this.secondaryTransport_.flush_();
			}
		}
	}
};

/**
 * @param {string} reasonString
 * @param {boolean} applicationLevel
 * @private
 */
cw.net.ClientStream.prototype.callOnReset_ = function(reasonString, applicationLevel) {
	if(this.onreset) {
		try {
			this.onreset.call(this.userContext_, reasonString, applicationLevel);
		} catch(error) {
			this.logger_.warning(
				"onreset raised uncaught exception", error);
			cw.net.throwErrorIntoWindow_(error);
		}
	}
};

/**
 * Reset (disconnect) the stream with reason {@code reasonString}.
 * Any strings queued for sending will never be sent.
 *
 * Implementation details: This tries to send a ResetFrame once,
 * either over the existing primary transport, or over a new secondary
 * transport.  The server might never receive a ResetFrame.
 *
 * @param {string} reasonString Reason why resetting the stream
 */
cw.net.ClientStream.prototype.reset = function(reasonString) {
	goog.asserts.assertString(reasonString);

	if(this.state_ > cw.net.StreamState_.STARTED) {
		throw Error("reset: Can't send reset in state " + this.state_);
	}

	this.cancelTryToSendSoon_();

	if(this.queue_.getQueuedCount() != 0) {
		this.logger_.warning("reset: strings in send queue will never be sent: " +
			cw.repr.repr(this.queue_));
	}

	this.state_ = cw.net.StreamState_.RESETTING;
	if(this.primaryTransport_ && this.primaryTransport_.canFlushMoreThanOnce_) {
		this.logger_.info("reset: Sending ResetFrame over existing primary.");
		this.primaryTransport_.writeReset_(reasonString, true/* applicationLevel */);
		this.primaryTransport_.flush_();
		// If server gets the ResetFrame, it will close the transport (or send YouCloseIt).
		// Eventually transportOffline_ is called (we hope), which no
		// longer makes a new transport because this.state_ > STARTED
	} else {
		// Primary is either offline or can't send after started, so
		// we need to create a secondary transport to send a reset frame.

		// Dispose primary and secondary transports to free up connection
		// slots, which is hopefully not necessary.
		if(this.primaryTransport_) {
			this.logger_.fine("reset: Disposing primary before sending ResetFrame.");
			this.primaryTransport_.dispose();
		}
		if(this.secondaryTransport_) {
			this.logger_.fine("reset: Disposing secondary before sending ResetFrame.");
			this.secondaryTransport_.dispose();
		}

		this.logger_.info("reset: Creating resettingTransport_ for sending ResetFrame.");
		this.resettingTransport_ = this.createNewTransport_(false, false);
		this.resettingTransport_.writeReset_(reasonString, true/* applicationLevel */);
		this.resettingTransport_.flush_();
		// Comment above about primaryTransport_.flush_() applies here too.
	}

	this.callOnReset_(reasonString, true/* applicationLevel */);
};

/**
 * @private
 */
cw.net.ClientStream.prototype.disposeAllTransports_ = function() {
	var transports = this.transports_.getValues();
	for(var i=0; i < transports.length; i++) {
		transports[i].dispose();
	}
};

/**
 * @param {string} reasonString
 * @param {boolean} applicationLevel
 * @private
 */
cw.net.ClientStream.prototype.doReset_ = function(reasonString, applicationLevel) {
	this.callOnReset_(reasonString, applicationLevel);
	// Keep in mind both the "Minerva does reset" and "client app calls
	// reset" cases, and keep the onreset and ondisconnect call
	// order sane.
	this.dispose();
};

/**
 * ClientTransport calls this when it gets a reset frame from server.
 * ClientTransport still needs to call transportOffline after this.
 * @param {string} reasonString
 * @param {boolean} applicationLevel
 * @private
 */
cw.net.ClientStream.prototype.resetFromPeer_ = function(reasonString, applicationLevel) {
	this.doReset_(reasonString, applicationLevel);
};

/**
 * Called by ClientStream if it has given up on the stream.  This does *not*
 * try to send a ResetFrame to the server.
 * @param {string} reasonString
 * @private
 */
cw.net.ClientStream.prototype.internalReset_ = function(reasonString) {
	this.doReset_(reasonString, false/* applicationLevel */);
};

/**
 * @return {boolean}
 */
cw.net.ClientStream.prototype.isResettingOrDisposed_ = function() {
	return this.state_ == cw.net.StreamState_.RESETTING || this.isDisposed();
};

/**
 * ClientTransport calls this to tell ClientStream about received strings.
 * @param {!cw.net.ClientTransport} transport The transport that received
 * 	these strings.
 * @param {!cw.net.SeqNumStringPairs_} pairs Sorted Array of
 * 	(seqNum, string) pairs that transport has received.
 * @param {boolean} avoidCreatingTransports
 * @private
 */
cw.net.ClientStream.prototype.stringsReceived_ = function(transport, pairs, avoidCreatingTransports) {
	goog.asserts.assert(
		this.state_ == cw.net.StreamState_.STARTED,
		"stringsReceived_: state is " + this.state_);

	var _ = this.incoming_.give(
		pairs, this.maxUndeliveredStrings, this.maxUndeliveredBytes);

	var items = _[0];
	var hitLimit = _[1];
	// Don't look at hitLimit yet; deliver the deliverable strings even if
	// the receive window is overflowing.
	if(items) {
		for(var i=0; i < items.length; i++) {
			var s = items[i];
			if(this.onstring) {
				try {
					this.onstring.call(this.userContext_, s);
				} catch(error) {
					this.logger_.warning(
						"onstring raised uncaught exception", error);
					cw.net.throwErrorIntoWindow_(error);
				}
			}
			// Under onstring, the state may have changed completely!
			// The ClientStream may be RESETTING or disposed.
			if(this.isResettingOrDisposed_()) {
				return;
			}
		}
	}

	// Because we received strings, we may need to send a SACK.
	// Do this after calling onstring, because onstring may queue more
	// strings for sending.  Note that in that case, tryToSendSoon_
	// has already been called.
	//
	// Long-polling transports call with avoidCreatingTransports=true because
	// ClientStream will create a new transport after that long-poll closes.
	// We know it will close very soon because it just received strings.
	// The new transport will have a SACK, so it is stupid to create a new
	// secondary transport right now to send a SACK redundantly.  (Note that
	// the new tryToSend*Soon*_ alleviates the problem anyway.)  For HTTP
	// streaming, the transport might not close for a while, so we do call
	// tryToSendSoon_.
	if(!avoidCreatingTransports) { // TODO: maybe we want && !hitLimit?
		this.tryToSendSoon_();
	}

	// Possibly unnecessary at this writing.
	if(this.isResettingOrDisposed_()) {
		return;
	}

	if(hitLimit) {
		transport.causedRwinOverflow_();
	}
};

/**
 * Called by transports to tell me that server has received at least some of
 *	our C2S strings.  This method possibly removes some queued items from
 * 	our send queue.
 * @param {!cw.net.SACK} sack
 * @return {boolean} Whether the SACK was bad
 * @private
 */
cw.net.ClientStream.prototype.sackReceived_ = function(sack) {
	this.lastSackSeenByClient_ = sack;
	return this.queue_.handleSACK(sack);
};

/**
 * @return {!cw.net.SACK} A SACK that represents the state of our
 * 	receive window.
 * @private
 */
cw.net.ClientStream.prototype.getSACK_ = function() {
	return this.incoming_.getSACK();
};

/**
 * Called if .start() fails
 * @private
 */
cw.net.ClientStream.prototype.earlyFailure_ = function(err) {
	this.logger_.severe('Failed to start ' + cw.repr.repr(this) +
		'; error was ' + cw.repr.repr(err.message));
	this.dispose();
	return null;
};

/**
 * Called by application to start the ClientStream.
 */
cw.net.ClientStream.prototype.start = function() {
	if(this.onmessage) {
		throw Error("ClientStream.start: Hey, you! It's `onstring`, not " +
			"`onmessage`! Refusing to start.")
	}
	if(this.state_ != cw.net.StreamState_.UNSTARTED) {
		throw new Error("ClientStream.start: " + cw.repr.repr(this) +
			" already started");
	}
	if(this.onstarted) {
		this.onstarted(this);
	}
	this.state_ = cw.net.StreamState_.WAITING_RESOURCES;

	if(this.endpoint_ instanceof cw.net.HttpEndpoint) {
		var d1 = cw.net.theXDRTracker.getWindowForUrl(
			this.endpoint_.primaryUrl, this);
		var d2 = cw.net.theXDRTracker.getWindowForUrl(
			this.endpoint_.secondaryUrl, this);

		var d = goog.async.DeferredList.gatherResults([d1, d2]);
		d.addCallback(goog.bind(this.expandHttpEndpoint_, this));
		d.addErrback(goog.bind(this.earlyFailure_, this));
	} else if(this.endpoint_ instanceof cw.net.SocketEndpoint) {
		if(cw.net.ourFlashSocketTracker_) {
			this.expandSocketEndpoint_();
		} else {
			var d = cw.net.loadFlashConnector(this.callQueue_, this.endpoint_.primaryUrl);
			var that = this;
			d.addCallback(function(bridge) {
				// If two streams were started at once, ourFlashSocketTracker_
				// may have already been set.
				if(!cw.net.ourFlashSocketTracker_) {
					cw.net.ourFlashSocketTracker_ =
						new cw.net.FlashSocketTracker(that.callQueue_, bridge);
				}
				return null;
			});
			d.addCallback(goog.bind(this.expandSocketEndpoint_, this));
			d.addErrback(goog.bind(this.earlyFailure_, this));
		}
	} else {
		this.startFirstTransport_();
	}
};

/**
 * @param {!Array.<!cw.net.XDRFrame>} xdrFrames
 */
cw.net.ClientStream.prototype.expandHttpEndpoint_ = function(xdrFrames) {
	var waitResState = cw.net.StreamState_.WAITING_RESOURCES;
	goog.asserts.assert(this.state_ == waitResState,
		"Expected stream state " + waitResState + ", was " + this.state_);

	goog.asserts.assert(xdrFrames.length == 2,
		"Wrong xdrFrames.length: " + xdrFrames.length);

	var primaryWindow = xdrFrames[0].contentWindow;
	var secondaryWindow = xdrFrames[1].contentWindow;
	var primaryUrl = xdrFrames[0].expandedUrl;
	var secondaryUrl = xdrFrames[1].expandedUrl;

	this.xdrFramesInUse_.push(xdrFrames[0]);
	this.xdrFramesInUse_.push(xdrFrames[1]);

	// TODO: maybe do something other than replace this.endpoint_
	this.endpoint_ = new cw.net.ExpandedHttpEndpoint_(
		primaryUrl, primaryWindow, secondaryUrl, secondaryWindow);

	this.startFirstTransport_();
};

cw.net.ClientStream.prototype.expandSocketEndpoint_ = function() {
	var host = this.endpoint_.host;
	var port = this.endpoint_.port;
	var tracker = cw.net.ourFlashSocketTracker_;

	goog.asserts.assert(tracker != null, "ourFlashSocketTracker_ is null");

	// TODO: maybe do something other than replace this.endpoint_
	this.endpoint_ = new cw.net.ExpandedSocketEndpoint_(
		host, port, tracker);

	this.startFirstTransport_();
};

cw.net.ClientStream.prototype.startFirstTransport_ = function() {
	this.state_ = cw.net.StreamState_.STARTED;
	this.primaryTransport_ = this.createNewTransport_(true, true);
	if(!this.primaryTransport_) {
		return;
	}
	this.primaryTransport_.writeStrings_(this.queue_, null);
	this.primaryTransport_.flush_();
};

cw.net.ClientStream.prototype.disposeInternal = function() {
	this.logger_.info(cw.repr.repr(this) + " in disposeInternal.");
	this.cancelTryToSendSoon_();
	this.state_ = cw.net.StreamState_.DISCONNECTED;
	this.disposeAllTransports_();

	for(var i=0; i < this.xdrFramesInUse_.length; i++) {
		var frame = this.xdrFramesInUse_[i];
		cw.net.theXDRTracker.stoppedUsingXDRFrame(frame, this);
	}

	if(goog.userAgent.WEBKIT && this.windowLoadEvent_) {
		goog.events.unlistenByKey(this.windowLoadEvent_);
		this.windowLoadEvent_ = null;
	}

	// Must be called after stoppedUsingXDRFrame calls, so that if a new
	// ClientStream is created immediately, it can reuse the existing iframes
	// (if iframes were indeed used).
	if(this.ondisconnect) {
		this.ondisconnect.call(this.userContext_);
	}

	// Clear any likely circular references
	delete this.transports_;
	delete this.primaryTransport_;
	delete this.secondaryTransport_;
	delete this.resettingTransport_;
	delete this.userContext_;

	cw.net.ClientStream.superClass_.disposeInternal.call(this);
};

// notifyFinish?
// producers?




/**
 * @enum {number}
 * @private
 */
cw.net.TransportType_ = {
	XHR_LONGPOLL: 1,
	XHR_STREAM: 2,
	FLASH_SOCKET: 3
};


/**
 * One ClientTransport is instantiated for every HTTP request we make
 * (for HTTP endpoints), or for every TCP connection we make (for
 * Flash Socket/WebSocket endpoints).
 *
 * Differences between Py Minerva's ServerTransport and JS Minerva's ClientTransport:
 * 	- We have no Interface defined for ClientTransport.
 * 	- ClientTransport makes connections, ServerTransport receives connections.
 * 	- ClientTransport deals with unicode strings (though restricted in range),
 * 		ServerTransport deals with bytes (also restricted in range).
 * 	- ClientTransport may have subtly different ResetFrame behavior (more
 * 		StringFrames make it through? Really? TODO: describe)
 *
 * @param {!cw.eventual.CallQueue} callQueue
 * @param {!cw.net.ClientStream} stream
 * @param {number} transportNumber
 * @param {!cw.net.TransportType_} transportType
 * @param {!cw.net.Endpoint} endpoint
 * @param {boolean} becomePrimary Should this transport try to become primary
 * 	transport?
 *
 * @constructor
 * @extends {goog.Disposable}
 * @private
 */
cw.net.ClientTransport = function(callQueue, stream, transportNumber,
transportType, endpoint, becomePrimary) {
	goog.Disposable.call(this);

	/**
	 * @type {!cw.eventual.CallQueue}
	 * @private
	 */
	this.callQueue_ = callQueue;

	/**
	 * The ClientStream we're associated with.
	 * @type {cw.net.ClientStream}
	 * @private
	 */
	this.stream_ = stream;

	/**
	 * @type {number}
	 */
	this.transportNumber = transportNumber;

	/**
	 * @type {!cw.net.TransportType_}
	 * @private
	 */
	this.transportType_ = transportType;

	/**
	 * Where we should connect to.
	 * @type {!cw.net.Endpoint}
	 * @private
	 */
	this.endpoint_ = endpoint;

	/**
	 * Very temporary send buffer, always [] before returning control
	 * to browser event loop.
	 * @type {!Array.<!cw.net.Frame>}
	 * @private
	 */
	this.toSendFrames_ = [];

	/**
	 * Should this transport try to become primary transport?
	 * If true, we'll send a HelloFrame that says we want to receive strings,
	 * 	and the transport may or may not stay open for a while.
	 * If false,
	 * 	for HTTP transports: we'll make a request (possibly with some
	 * 		C2S strings) and the server will close it because the transport
	 * 		is not receiving strings.
	 * 	for non-HTTP transports: we'll make a connection.  ClientStream will
	 * 		be able to continue to send strings over it.  ClientStream can
	 * 		call ClientTransport.dispose to close it at any time.
	 * @type {boolean}
	 * @private
	 */
	this.becomePrimary_ = becomePrimary;

	/**
	 * Can this transport send more strings after it has been started?
	 * @type {boolean}
	 * @private
	 */
	this.canFlushMoreThanOnce_ = !this.isHttpTransport_();

	/**
	 * Can server stream frames to this transport?
	 * @type {boolean}
	 * @private
	 */
	this.s2cStreaming =
		(this.transportType_ != cw.net.TransportType_.XHR_LONGPOLL);

	/**
	 * @type {function(): void}
	 * @private
	 */
	this.boundTimedOut_ = goog.bind(this.timedOut_, this);
};
goog.inherits(cw.net.ClientTransport, goog.Disposable);

/**
 * @type {!goog.debug.Logger}
 * @protected
 */
cw.net.ClientTransport.prototype.logger_ =
	goog.debug.Logger.getLogger('cw.net.ClientTransport');

/**
 * The underlying object used to send and receive frames.
 * @type {goog.net.XhrIo|cw.net.FlashSocketConduit}
 */
cw.net.ClientTransport.prototype.underlying_ = null;

/**
 * When the underlying TCP connection or HTTP request started.
 * @type {?number}
 * @private
 */
cw.net.ClientTransport.prototype.underlyingStartTime_ = null;

/**
 * When the underlying TCP connection or HTTP request ended.
 * @type {?number}
 * @private
 */
cw.net.ClientTransport.prototype.underlyingStopTime_ = null;

/**
 * The ticket for the receive timeout, or null, if no timeout.
 * @type {?number}
 * @private
 */
cw.net.ClientTransport.prototype.recvTimeout_ = null;

/**
 * Whether the underlying TCP connection or HTTP request has been made.
 * @type {boolean}
 * @private
 */
cw.net.ClientTransport.prototype.started_ = false;

/**
 * Whether we're in the `framesReceived_` loop.
 * @type {boolean}
 * @private
 */
cw.net.ClientTransport.prototype.spinning_ = false;

/**
 * The last SACK written to the peer.
 * @type {cw.net.SACK}
 * @private
 */
cw.net.ClientTransport.prototype.lastSackWritten_ = null;

/**
 * The number of frames from the peer that we have successfully decoded.
 * @type {number}
 * @private
 */
cw.net.ClientTransport.prototype.framesDecoded_ = 0;

/**
 * The seqNum of the last string we wrote to the peer, or -1 if none.
 * @type {number}
 * @private
 */
cw.net.ClientTransport.prototype.ourSeqNum_ = -1;

/**
 * The seqNum of the next string we might receive from the peer, minus 1.
 * @type {number}
 * @private
 */
cw.net.ClientTransport.prototype.peerSeqNum_ = -1;

/**
 * Has {@link #writeReset_} been called on this transport?
 * @type {boolean}
 * @private
 */
cw.net.ClientTransport.prototype.wroteResetFrame_ = false;

/**
 * Was this transport aborted because ClientStream is trying to stop
 * the browser spinner from spinning?
 * @type {boolean}
 * @private
 */
cw.net.ClientTransport.prototype.abortedForSpinner_ = false;

/**
 * The additional likelihood that stream is dead on server or permanently
 * unreachable.  This is a guess based on what this transport has received.
 * @type {number}
 * @private
 */
cw.net.ClientTransport.prototype.penalty_ = 0;

/**
 * Did the transport receive data that suggests ClientStream should possibly
 * delay the next transport?
 * @type {boolean}
 * @private
 */
cw.net.ClientTransport.prototype.hadProblems_ = false;


/**
 * @param {!Array.<string>} sb
 * @param {!Array.<*>} stack
 * @private
 */
cw.net.ClientTransport.prototype.__reprPush__ = function(sb, stack) {
	sb.push(
		'<ClientTransport #', String(this.transportNumber),
		', becomePrimary=', String(this.becomePrimary_), '>');
};

/**
 * @return {string} A short description of the transport.  Used only for log
 * 	messages.
 * @private
 */
cw.net.ClientTransport.prototype.getDescription_ = function() {
	return (this.becomePrimary_ ? "Prim. T#" : "Sec. T#") + this.transportNumber;
};

/**
 * @return {boolean} Whether ClientStream should consider a
 * 	{@link cw.net.DoNothingTransport} for the next transport.
 * @private
 */
cw.net.ClientTransport.prototype.considerDelayingNextTransport_ = function() {
	return !!(this.hadProblems_ || !this.framesDecoded_);
};

/**
 * @return {number} How many milliseconds the underlying TCP connection or
 * 	HTTP request was open.
 * @private
 */
cw.net.ClientTransport.prototype.getUnderlyingDuration_ = function() {
	goog.asserts.assertNumber(this.underlyingStartTime_, "start time not a num");
	goog.asserts.assertNumber(this.underlyingStopTime_, "stop time not a num");
	return Math.max(0, this.underlyingStopTime_ - this.underlyingStartTime_);
};

/**
 * @return {boolean} Whether this ClientTransport is an HTTP transport.
 * @private
 */
cw.net.ClientTransport.prototype.isHttpTransport_ = function() {
	return (
		this.transportType_ == cw.net.TransportType_.XHR_LONGPOLL ||
		this.transportType_ == cw.net.TransportType_.XHR_STREAM);
};

/**
 * @param {!cw.net.Frame} frame
 * @return {boolean} True if {@code frame} was expected to be
 * 	{@link #HTTP_RESPONSE_PREAMBLE} but was not, else undefined.
 */
cw.net.ClientTransport.prototype.ensurePreambleIfHttpAndFirstFrame_ = function(frame) {
	// For HTTP transports, first frame must be the anti-script-inclusion
	// preamble.  While intended to stop attackers who include script
	// tags pointing to a WebPort URL, it also provides good
	// protection against us parsing and reading frames from a page
	// returned by an intermediary like a proxy or a WiFi access paywall.
	if(this.framesDecoded_ == 1 &&
	!frame.equals(cw.net.HTTP_RESPONSE_PREAMBLE) &&
	this.isHttpTransport_()) {
		this.logger_.warning(this.getDescription_() + " is closing soon because " +
			"got bad preamble: " + cw.repr.repr(frame));
		// No penalty because we want to treat this just like "cannot connect to peer".
		return true;
	}
	return false;
};

/**
 * @typedef {Array.<!Array.<number|string>>} An Array of
 * 	(seqNum, string) pairs.
 * @private
 * // TODO: types for tuples
 */
cw.net.SeqNumStringPairs_;

/**
 * @param {!cw.net.SeqNumStringPairs_} bunchedStrings Unsorted Array of
 * 	(seqNum, string) pairs collected in {@link #framesReceived_}.
 * @private
 */
cw.net.ClientTransport.prototype.handleStrings_ = function(bunchedStrings) {
	// bunchedStrings is already sorted 99.99%+ of the time, but we
	// must sort it anyway.
	var compareZeroth = function(a, b) {
		return a[0] > b[0] ? 1 : a[0] < b[0] ? -1 : 0;
	};
	goog.array.sort(bunchedStrings, compareZeroth);
	var avoidCreatingTransports = !this.s2cStreaming;
	this.stream_.stringsReceived_(this, bunchedStrings, avoidCreatingTransports);
	// Remember that a lot can happen underneath that stringsReceived call,
	// including a call to our own `writeStrings_` or `writeReset_` or `dispose`.
};

/**
 * @param {string} frameStr
 * @param {!cw.net.SeqNumStringPairs_} bunchedStrings An unsorted Array of
 * 	[seqNum, string] pairs that this method can push into, or clear.
 * @return {boolean} Whether ClientTransport must now dispose.
 * @private
 */
cw.net.ClientTransport.prototype.handleFrame_ = function(frameStr, bunchedStrings) {
	try {
		/** @type {!cw.net.Frame} Decoded frame */
		var frame = cw.net.decodeFrameFromServer(frameStr);
		this.framesDecoded_ += 1;
		this.logger_.fine(this.getDescription_() + ' RECV ' + cw.repr.repr(frame));

		if(this.ensurePreambleIfHttpAndFirstFrame_(frame)) {
			return true;
		}

		if(frame instanceof cw.net.StringFrame) {
			// Check that the string does not have illegal characters.
			// If it does, it's probably because of HTTP response corruption.
			if(!cw.net.isRestrictedString(frame.string)) {
				this.hadProblems_ = true;
				return true;
			}
			this.peerSeqNum_ += 1;
			// Because we may have received multiple Minerva strings, collect
			// them into a Array and then deliver them all at once to ClientStream.
			// This does *not* add any latency.  It does reduce the number of funcalls.
			bunchedStrings.push([this.peerSeqNum_, frame.string]);
		} else if(frame instanceof cw.net.SackFrame) {
			if(this.stream_.sackReceived_(frame.sack)) {
				this.logger_.warning(this.getDescription_() +
					" is closing soon because got bad SackFrame");
				this.hadProblems_ = true;
				return true;
			}
		} else if(frame instanceof cw.net.SeqNumFrame) {
			this.peerSeqNum_ = frame.seqNum - 1;
		} else if(frame instanceof cw.net.StreamStatusFrame) {
			this.stream_.streamStatusReceived_(frame.lastSackSeen);
		} else if(frame instanceof cw.net.YouCloseItFrame) {
			this.logger_.finest(this.getDescription_() +
				" is closing soon because got YouCloseItFrame");
			return true;
		} else if(frame instanceof cw.net.TransportKillFrame) {
			this.hadProblems_ = true;
			if(frame.reason == cw.net.TransportKillReason.stream_attach_failure) {
				this.penalty_ += 1;
			} else if(frame.reason == cw.net.TransportKillReason.acked_unsent_strings) {
				this.penalty_ += 0.5;
			}
			// No penalty for frame_corruption, rwin_overflow, or
			// invalid_frame_type_or_arguments
			this.logger_.finest(this.getDescription_() +
				" is closing soon because got " + cw.repr.repr(frame));
			return true;
		} else if(frame instanceof cw.net.CommentFrame) {
			// Ignore it
		} else if(frame instanceof cw.net.StreamCreatedFrame) {
			var avoidCreatingTransports = !this.s2cStreaming;
			this.stream_.streamSuccessfullyCreated_(avoidCreatingTransports);
		} else {
			if(bunchedStrings.length) {
				this.handleStrings_(bunchedStrings);
				goog.array.clear(bunchedStrings);
			}
			if(frame instanceof cw.net.ResetFrame) {
				this.stream_.resetFromPeer_(frame.reasonString, frame.applicationLevel);
				// closeSoon = true is unnecessary here because resetFromPeer_
				// will dispose all transports, but we'll dispose ourselves anyway.
				return true;
			} else {
				throw Error(this.getDescription_() +
					" had unexpected state in framesReceived_.");
			}
		}
	} catch(e) {
		if(!(e instanceof cw.net.InvalidFrame)) {
			throw e;
		}
		this.logger_.warning(this.getDescription_() +
			" is closing soon because got InvalidFrame: " + cw.repr.repr(frameStr));
		// No penalty because this cause is almost certainly
		// due to corruption by intermediary.
		this.hadProblems_ = true;
		return true;
	}
	return false; // don't closeSoon
};

/**
 * @param {!Array.<string>} frames Encoded frames received from peer.
 * @private
 */
cw.net.ClientTransport.prototype.framesReceived_ = function(frames) {
	this.spinning_ = true;
	try {
		var closeSoon = false;
		var bunchedStrings = [];
		for(var i=0, len=frames.length; i < len; i++) {
			// handleFrame_ below calls methods on stream_ for many
			// reasons, and those methods can synchronously dispose us.
			// Note that we might have been disposed before entering
			// framesReceived_; for example, if we were disposed while
			// making an HTTP request.
			if(this.isDisposed()) {
				this.logger_.info(this.getDescription_() +
					" returning from loop because we're disposed.");
				return;
			}
			var frameStr = frames[i];
			closeSoon = this.handleFrame_(frameStr, bunchedStrings);
			if(closeSoon) {
				break;
			}
		}

		if(bunchedStrings.length) {
			this.handleStrings_(bunchedStrings);
			bunchedStrings = [];
		}
		this.spinning_ = false;
		if(this.toSendFrames_.length) {
			this.flush_();
		}
		if(closeSoon) {
			this.logger_.finest(this.getDescription_() + " closeSoon is " +
				"true.  Frames were: " + cw.repr.repr(frames));
			this.dispose();
		}
	} finally {
		this.spinning_ = false;
	}
};

/**
 * Called by a timer if the transport can't connect in time, or if it stops
 * receiving bytes.
 * @private
 */
cw.net.ClientTransport.prototype.timedOut_ = function() {
	this.logger_.warning(this.getDescription_() +
		" timed out due to lack of connection or no data being received.");
	this.dispose();
};

/**
 * @private
 */
cw.net.ClientTransport.prototype.clearRecvTimeout_ = function() {
	if(this.recvTimeout_ != null) {
		this.callQueue_.clock.clearTimeout(this.recvTimeout_);
		this.recvTimeout_ = null;
	}
};

/**
 * @param {number} ms Milliseconds to set the receive timeout to.
 * @private
 */
cw.net.ClientTransport.prototype.setRecvTimeout_ = function(ms) {
	goog.asserts.assert(!isNaN(ms), 'ms is NaN');
	this.clearRecvTimeout_();
	ms = Math.round(ms);
	this.recvTimeout_ = this.callQueue_.clock.setTimeout(
		this.boundTimedOut_, ms);
	this.logger_.fine(this.getDescription_() + "'s receive timeout set to " + ms + " ms.");
};

/**
 * Called by {@link cw.net.XHRMaster} after it receives headers.
 * @param {?number} contentLength The Content-Length if a valid one was
 * 	received, or null.
 * @private
 */
cw.net.ClientTransport.prototype.contentLengthMaybeReceived_ = function(contentLength) {
	this.logger_.fine(this.getDescription_() + " got Content-Length: " + contentLength);
	// Only adjust the timeout for XHR_LONGPOLL.  For all other transports,
	// we have proper feedback as we receive data, and can rely on the timeout
	// set by peerStillAlive_.
	if(this.transportType_ == cw.net.TransportType_.XHR_LONGPOLL) {
		if(contentLength == null) {
			this.logger_.warning("Expected to receive a valid " +
				"Content-Length, but did not.");
			// The response could be even bigger, but we don't have any
			// information to go on.
			contentLength = 500000;
		}
		this.setRecvTimeout_(
			cw.net.MAX_SERVER_JANK +
			(contentLength / cw.net.DEFAULT_DL_SPEED) * 1000);
	}
};

/**
 * Called by underlying_ when it connects or receives any bytes from the
 * peer (even when it's not a full frame yet).
 * @private
 */
cw.net.ClientTransport.prototype.peerStillAlive_ = function() {
	if(this.transportType_ == cw.net.TransportType_.XHR_LONGPOLL) {
		// Ignore peerStillAlive_ for XHR_LONGPOLL because peerStillAlive_
		// events for it are unreliable: it might only be fired once, even
		// as it continues downloading.
	} else if(
	this.transportType_ == cw.net.TransportType_.FLASH_SOCKET ||
	this.transportType_ == cw.net.TransportType_.XHR_STREAM) {
		this.setRecvTimeout_(
			cw.net.MAX_SERVER_JANK +
			cw.net.DEFAULT_RTT_VARIANCE +
			cw.net.HEARTBEAT_INTERVAL);
	} else {
		throw Error("peerStillAlive_: Don't know what to do for this transportType: " +
			this.transportType_);
	}
};

/**
 * Called by XHRMaster.
 * @private
 */
cw.net.ClientTransport.prototype.httpResponseEnded_ = function() {
	this.dispose();
};

/**
 * @param {string} payload The request body (containing encoded frames).
 * @private
 */
cw.net.ClientTransport.prototype.makeHttpRequest_ = function(payload) {
	var url = this.becomePrimary_ ?
		this.endpoint_.primaryUrl : this.endpoint_.secondaryUrl;
	var contentWindow = this.becomePrimary_ ?
		this.endpoint_.primaryWindow : this.endpoint_.secondaryWindow;

	goog.asserts.assert(this.underlying_ === null, 'already have an underlying_');
	this.underlying_ = cw.net.theXHRMasterTracker_.createNew(
		this, contentWindow);

	this.underlyingStartTime_ = cw.clock.getTime(this.callQueue_.clock);
	this.underlying_.makeRequest(url, 'POST', payload);

	var involvesSSL = (url.indexOf('https://') == 0);
	// TCP usually takes one round trip; SSL usually takes another two.
	var connectRTTs = involvesSSL ? 3 : 1;

	// Set a timeout for the maximum duration we expect before a response.
	// You might think that we can set a lower timeout here to just wait
	// for the headers, but that is not the case: there are probably many
	// proxies that wait for a full response before writing out the response
	// headers.
	//
	// Give it 1 RTT for a DNS request, plus 3 or 1 RTTs for the connect,
	// plus half an RTT for the request close, plus two server janks,
	// plus the actual duration of the request.
	//
	// Note: we assume that the HTTP response headers are small enough
	// to not stall even a slow connection.
	var duration;
	if(this.s2cStreaming) {
		// Server always writes a heartbeat early
		duration = 0;
	} else if(this.becomePrimary_) {
		duration = cw.net.DEFAULT_HTTP_LONGPOLL_DURATION;
	} else {
		duration = 0;
	}
	this.setRecvTimeout_(
		cw.net.DEFAULT_RTT_GUESS * (1.5 + connectRTTs) +
		cw.net.MAX_SERVER_JANK * 2 +
		duration);
};

/**
 * @return {!cw.net.HelloFrame}
 * @private
 */
cw.net.ClientTransport.prototype.makeHelloFrame_ = function() {
	var hello = new cw.net.HelloFrame();
	hello.transportNumber = this.transportNumber;
	hello.protocolVersion = cw.net.PROTOCOL_VERSION;
	hello.httpFormat = cw.net.HttpFormat.FORMAT_XHR;
	if(!this.stream_.streamExistedAtServer_) {
		hello.requestNewStream = true;
	}
	hello.streamId = this.stream_.streamId;
	hello.streamingResponse = this.s2cStreaming;
	if(hello.streamingResponse) {
		hello.needPaddingBytes = 4096;
	}
	// TODO: investigate if any browsers are thrashing CPU by copying
	// the whole thing during XHR streaming.
	hello.maxReceiveBytes = 300000;
	hello.maxInactivity =
		this.s2cStreaming ? Math.floor(cw.net.HEARTBEAT_INTERVAL / 1000) : 0;
	hello.useMyTcpAcks = false;
	if(this.becomePrimary_) {
		hello.succeedsTransport = null;
		var duration = this.s2cStreaming ?
			cw.net.DEFAULT_HTTP_STREAMING_DURATION :
			cw.net.DEFAULT_HTTP_LONGPOLL_DURATION;
		// Only use maxOpenTime for primary transports, because we trust
		// the server to quickly close secondary transports.
		hello.maxOpenTime = Math.floor(duration / 1000);
	}
	hello.sack = this.stream_.getSACK_();
	hello.lastSackSeenByClient = this.stream_.lastSackSeenByClient_;
	return hello;
};

/**
 * Append frame to the internal send buffer.
 * @param {!cw.net.Frame} frame
 * @private
 */
cw.net.ClientTransport.prototype.writeFrame_ = function(frame) {
	this.toSendFrames_.push(frame);
	// Potentially useful when debugging
	//this.logger_.severe('toSendFrames_: ' + cw.repr.repr(this.toSendFrames_));
};

/**
 * @private
 */
cw.net.ClientTransport.prototype.writeInitialFrames_ = function() {
	var hello = this.makeHelloFrame_();
	this.writeFrame_(hello);
	// HelloFrame includes a sack.
	this.lastSackWritten_ = /** @type {!cw.net.SACK} */ (hello.sack);
};

/**
 * Flush the internal send buffer and return an HTTP POST payload.
 * @return {string} The HTTP POST payload.
 * @private
 */
cw.net.ClientTransport.prototype.flushBufferAsHttpPayload_ = function() {
	var sb = [];
	for(var i=0, len=this.toSendFrames_.length; i < len; i++) {
		var frame = this.toSendFrames_[i];
		frame.encodeToPieces(sb);
		sb.push('\n');
	}
	this.toSendFrames_ = [];
	return sb.join("");
};

/**
 * Flush the internal send buffer and return an Array of encoded frames.
 * @return {!Array.<string>} The encoded frames.
 * @private
 */
cw.net.ClientTransport.prototype.flushBufferAsEncodedFrames_ = function() {
	var frames = [];
	for(var i=0, len=this.toSendFrames_.length; i < len; i++) {
		var frame = this.toSendFrames_[i];
		frames.push(frame.encode());
	}
	this.toSendFrames_ = [];
	return frames;
};

/**
 * Called by our underlying_, a {@link cw.net.FlashSocketConduit}.
 * @param {boolean} probablyCrashed Did Flash Player probably crash?
 * @private
 */
cw.net.ClientTransport.prototype.flashSocketTerminated_ = function(probablyCrashed) {
	if(probablyCrashed) {
		// Right now, we don't support switching endpoints, so increase the
		// penalty, which will usually make ClientStream give up very soon.
		// TODO: remove this after we can switch to another Endpoint.
		this.penalty_ += 0.5;
	}

	// We treat close/ioerror/securityerror all the same.
	this.dispose();
};

/**
 * @param {!Array.<string>} frames Encoded frames to send right away.
 * @private
 */
cw.net.ClientTransport.prototype.makeFlashConnection_ = function(frames) {
	var endpoint = this.endpoint_;
	this.underlying_ = new cw.net.FlashSocketConduit(this);
	// TODO: pass a FlashSocketTracker to FlashSocketConduit's constructor;
	// make it create the socket.
	var socket = endpoint.tracker.createNew(this.underlying_);
	this.underlying_.socket_ = socket;
	this.underlyingStartTime_ = cw.clock.getTime(this.callQueue_.clock);
	this.underlying_.connect(endpoint.host, endpoint.port);
	// .connect may detect a Flash Player crash and call oncrash, which
	// disposes the FlashSocketConduit.
	if(this.underlying_.isDisposed()) {
		return;
	}
	this.underlying_.writeFrames(frames);
	// .writeFrames may detect a Flash Player crash and call oncrash, which
	// disposes the FlashSocketConduit.
	if(this.underlying_.isDisposed()) {
		return;
	}

	// Give it 1 RTT for a DNS request, and 1 RTT for the TCP connection.
	// Our DEFAULT_RTT_GUESS covers any underlying retransmits.  Also,
	// the DNS name might be already resolved.  Keep in mind that if this
	// timeout is high enough (probably > 20000), then Flash itself might
	// timeout with onsecurityerror.
	this.setRecvTimeout_(
		cw.net.DEFAULT_RTT_GUESS * 2 +
		cw.net.MAX_SERVER_JANK);
};

/**
 * Flush internally queued frames to the underlying connection/HTTP request.
 * If necessary, make the initial connection/HTTP request.
 *
 * This can be called after calling {@link #writeStrings_} and/or
 * {@link #writeReset_} on a non-started transport.  For transports
 * with streaming upload, you can of course also call those methods
 * after starting.
 *
 * @private
 */
cw.net.ClientTransport.prototype.flush_ = function() {
	if(this.started_ && !this.canFlushMoreThanOnce_) {
		throw Error("flush_: Can't flush more than once to this transport.");
	}

	if(this.spinning_) {
		this.logger_.finest(this.getDescription_() +
			" flush_: Returning because spinning right now.");
		return;
	}

	var wasStarted = this.started_;
	this.started_ = true;

	if(!wasStarted && !this.toSendFrames_.length) {
		this.writeInitialFrames_();
	}

	// Just debug logging
	for(var i=0; i < this.toSendFrames_.length; i++) {
		var frame = this.toSendFrames_[i];
		this.logger_.fine(
			this.getDescription_() + ' SEND ' + cw.repr.repr(frame));
	}

	if(this.isHttpTransport_()) {
		var payload = this.flushBufferAsHttpPayload_();
		this.makeHttpRequest_(payload);
	} else if(this.transportType_ == cw.net.TransportType_.FLASH_SOCKET) {
		var frames = this.flushBufferAsEncodedFrames_();
		if(this.underlying_) {
			this.underlying_.writeFrames(frames);
		} else {
			this.makeFlashConnection_(frames);
		}
	} else {
		throw Error("flush_: Don't know what to do for this transportType: " +
			this.transportType_);
	}
};

/**
 * @param {!cw.net.SACK} sack
 * @private
 */
cw.net.ClientTransport.prototype.writeSack_ = function(sack) {
	// ClientStream doesn't keep track of which SACKs have been written to
	// which transports.  If this is the SACK we wrote last time, ignore
	// ClientStream's request.
	if(sack == this.lastSackWritten_) {
		return;
	}

	if(!this.started_ && !this.toSendFrames_.length) {
		this.writeInitialFrames_();
	}

	this.writeFrame_(new cw.net.SackFrame(sack));
	this.lastSackWritten_ = sack;
};

/**
 * Write strings in queue {@code queue} to the peer.  This does not write
 * strings that were already written to the peer over this transport.
 *
 * @param {!cw.net.Queue} queue Queue containing strings to send.
 * @param {?number} start Minimum string seqNum to consider sending, or null
 * 	to not skip any.
 * @private
 */
cw.net.ClientTransport.prototype.writeStrings_ = function(queue, start) {
	// This function behaves very badly if `start` is undefined.
	goog.asserts.assert(
		start !== undefined, "writeStrings_: Did you forget `start` argument?");

	if(!this.started_ && !this.toSendFrames_.length) {
		this.writeInitialFrames_();
	}

	var queueStart = Math.max(start, this.ourSeqNum_ + 1);
	// Even if there's a lot of stuff in the queue, write everything.
	var pairs = queue.getItems(queueStart);
	for(var i=0, len=pairs.length; i < len; i++) {
		var pair = pairs[i];
		var seqNum = /** @type {number} */ (pair[0]);
		var string = /** @type {string} */ (pair[1]);
		if(this.ourSeqNum_ == -1 || this.ourSeqNum_ + 1 != seqNum) {
			this.writeFrame_(new cw.net.SeqNumFrame(seqNum));
		}
		this.writeFrame_(new cw.net.StringFrame(string));
		this.ourSeqNum_ = seqNum;
	}
};

cw.net.ClientTransport.prototype.disposeInternal = function() {
	this.logger_.info(this.getDescription_() + " in disposeInternal.");

	cw.net.ClientTransport.superClass_.disposeInternal.call(this);

	// TODO: is this really a good place to take the end time?  Keep
	// in mind streaming XHR requests, as well as slow application code
	// (called synchronously).
	this.underlyingStopTime_ = cw.clock.getTime(this.callQueue_.clock);

	this.toSendFrames_ = [];

	this.clearRecvTimeout_();

	// transportType_ doesn't matter; they're all Disposable.
	if(this.underlying_) {
		this.underlying_.dispose();
	}
	var stream = this.stream_;
	// Break circular references faster.
	// Make sure errors are thrown if we try to make further calls on this.stream_.
	this.stream_ = null;

	stream.transportOffline_(this);
};

/**
 * Abort because we're trying to stop the browser spinner from spinning.
 * @private
 */
cw.net.ClientTransport.prototype.abortToStopSpinner_ = function() {
	goog.asserts.assert(this.isHttpTransport_(),
		"only needed for http transports; why are you doing this?");
	this.abortedForSpinner_ = true;
	this.dispose();
};

/**
 * Close this transport because it has caused our receive window to
 * overflow.  We don't want to keep the transport open because otherwise
 * the server will assume that the strings it sent over the transport
 * will eventually get ACKed.
 * @private
 */
cw.net.ClientTransport.prototype.causedRwinOverflow_ = function() {
	this.logger_.severe(this.getDescription_() + "'s peer caused rwin overflow.");
	this.dispose();
};

/**
 * Send a ResetFrame over this transport.  Remember to either `close` or
 * 	`start` the transport after you call this.
 * @param {string} reasonString Textual reason why ClientStream is resetting.
 * @param {boolean} applicationLevel Whether this reset was made by the
 * 	application.
 * @private
 */
cw.net.ClientTransport.prototype.writeReset_ = function(reasonString, applicationLevel) {
	if(!this.started_ && !this.toSendFrames_.length) {
		this.writeInitialFrames_();
	}
	var resetFrame = new cw.net.ResetFrame(reasonString, applicationLevel);
	this.writeFrame_(resetFrame);
	this.wroteResetFrame_ = true;
};

/**
 * @return {!cw.net.TransportInfo}
 */
cw.net.ClientTransport.prototype.getInfo = function() {
	return new cw.net.TransportInfo(
		/*transportNumber=*/this.transportNumber,
		/*isPrimary=*/this.becomePrimary_,
		/*streamingFromPeer=*/this.s2cStreaming,
		/*streamingToPeer=*/this.canFlushMoreThanOnce_);
};



/**
 * A transport that does not actually try to connect anywhere, but rather
 * waits for `delay` milliseconds `times` times and goes offline.
 * {@link cw.net.ClientStream} uses this when it wants to delay a connection
 * attempt.  During a period of network problems, you will see this
 * interspersed between real {@link ClientTransport}s.  This is also
 * used when ClientStream kills the loading spinner in WebKit browsers.
 *
 * @param {!cw.eventual.CallQueue} callQueue
 * @param {!cw.net.ClientStream} stream
 * @param {number} delay
 * @param {number} times
 *
 * @constructor
 * @extends {goog.Disposable}
 * @private
 */
cw.net.DoNothingTransport = function(callQueue, stream, delay, times) {
	goog.Disposable.call(this);

	/**
	 * @type {!cw.eventual.CallQueue}
	 * @private
	 */
	this.callQueue_ = callQueue;

	/**
	 * @type {cw.net.ClientStream}
	 * @private
	 */
	this.stream_ = stream;

	/**
	 * @type {number}
	 * @private
	 */
	this.delay_ = delay;

	/**
	 * @type {number}
	 * @private
	 */
	this.countdown_ = times;
};
goog.inherits(cw.net.DoNothingTransport, goog.Disposable);

/**
 * @type {boolean}
 * @private
 */
cw.net.DoNothingTransport.prototype.started_ = false;

/**
 * @type {boolean}
 * @private
 */
cw.net.DoNothingTransport.prototype.canFlushMoreThanOnce_ = false;

/**
 * @type {?number}
 * @private
 */
cw.net.DoNothingTransport.prototype.goOfflineTicket_ = null;

/**
 * The last SACK written to the peer.  Used by ClientStream.
 * @type {null}
 * @private
 */
cw.net.DoNothingTransport.prototype.lastSackWritten_ = null;

/**
 * @type {!goog.debug.Logger}
 * @protected
 */
cw.net.DoNothingTransport.prototype.logger_ =
	goog.debug.Logger.getLogger('cw.net.DoNothingTransport');

/**
 * @private
 */
cw.net.DoNothingTransport.prototype.timeoutFired_ = function() {
	this.goOfflineTicket_ = null;
	this.countdown_--;
	if(this.countdown_) {
		this.setUpTimeout_();
	} else {
		this.dispose();
	}
};

/**
 * @private
 */
cw.net.DoNothingTransport.prototype.setUpTimeout_ = function() {
	var that = this;
	goog.asserts.assert(this.goOfflineTicket_ == null,
		"DoNothingTransport already has goOfflineTicket_?");
	this.goOfflineTicket_ = this.callQueue_.clock.setTimeout(function() {
		that.timeoutFired_();
	}, this.delay_);
};

/**
 * Start wasting time.
 * @private
 */
cw.net.DoNothingTransport.prototype.flush_ = function() {
	if(this.started_ && !this.canFlushMoreThanOnce_) {
		throw Error("flush_: Can't flush more than once to DoNothingTransport.");
	}
	this.started_ = true;
	this.setUpTimeout_();
};

/**
 * @param {!Array.<string>} sb
 * @param {!Array.<*>} stack
 * @private
 */
cw.net.DoNothingTransport.prototype.__reprPush__ = function(sb, stack) {
	sb.push(
		'<DoNothingTransport delay=', String(this.delay_), '>');
};

/**
 * Note: {@link cw.net.ClientStream.restartHttpRequests_} needs this.
 * @return {boolean}
 * @private
 */
cw.net.DoNothingTransport.prototype.isHttpTransport_ = function() {
	return false;
};

/**
 * @return {string} A short description of the transport.  Used only for log
 * 	messages.
 * @private
 */
cw.net.DoNothingTransport.prototype.getDescription_ = function() {
	return "Wast. T";
};

/**
 * @return {boolean} Whether ClientStream should consider using a
 * 	{@link cw.net.DoNothingTransport} for the next transport.
 * @private
 */
cw.net.DoNothingTransport.prototype.considerDelayingNextTransport_ = function() {
	return false;
};

cw.net.DoNothingTransport.prototype.disposeInternal = function() {
	this.logger_.info(
		this.getDescription_() + " in disposeInternal.");

	cw.net.DoNothingTransport.superClass_.disposeInternal.call(this);

	if(this.goOfflineTicket_ != null) {
		this.callQueue_.clock.clearTimeout(this.goOfflineTicket_);
	}

	var stream = this.stream_;
	// Break circular references faster.
	// Make sure errors are thrown if we try to make further calls on this.stream_.
	this.stream_ = null;

	stream.transportOffline_(this);
};
