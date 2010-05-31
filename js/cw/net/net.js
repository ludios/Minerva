/**
 * @fileoverview Minerva client and related functionality
 */

goog.provide('cw.net.WhoReset');
goog.provide('cw.net.IMinervaProtocol');
goog.provide('cw.net.Stream');

goog.require('goog.string');
goog.require('cw.net.Queue');



// Informal interfaces:
// IWindowTime is an object with methods setTimeout, clearTimeout, setInterval, clearInterval



/**
 * Endpoint types
 * @enum {number}
 */
cw.net.EndpointType = {
	HTTP: 1,
	HTTPS: 2,
	WS: 3, // WebSocket
	WSS: 4, // WebSocket Secure
	TCP: 5 // Flash Socket, also hypothetically Silverlight, Java, and other things that allow TCP connections.
};


/**
 * Implement this interface for your "endpoint locator" object.
 *
 * @interface
 */
cw.net.IEndpointLocator = function() {

}

// XXX TODO: this API feels wrong. What if there are multiple available endpoints
// for an EndpointType? Remember: endpoints may change during runtime,
// and at initial page load, we may want to connect to everything to see what
// we can connect to.

/**
 * @param {!cw.net.EndpointType} type The type of endpoint
 *
 * @return {?Array.<!(string|Object)>} The endpoint (with
 * 	credentials) that Minerva client should connect to.
 *
 *	Return an array of [the endpoint URL, credentialsData], or, if no
 * 	endpoint is suitable, return `null`.
 *
 * 	the endpoint URL: If `type` is `cw.net.EndpointType.{HTTP,HTTPS,WS,WSS}`, the
 * 	full URL with an appropriate scheme (`http://` or `https://` or `ws://` or `ws://`).
 * 	If `type` is `cw.net.EndpointType.TCP`, a URL that looks like "tcp://hostname:port"
 * 	(both `hostname` and the `port` number are required.)
 *
 * 	credentialsData: `Object`, which may be looked at by Minerva server's
 * 	firewall. Cannot be an `Array`, or anything but `Object`.
 */
cw.net.IEndpointLocator.prototype.locate = function(type) {

}


// TODO: need some kind of interface to allow applications to control
// timeout behavior. Control timeout for individual HTTP/WebSocket/Flash Socket transports?

// If application wants to timeout Stream on the client-side,


/**
 * The Minerva-level protocol version.
 *
 * @type {number}
 */
cw.net.protocolVersion_ = 2;


/**
 * @enum {number}
 */
cw.net.WhoReset = {
	server_minerva: 1,
	server_app: 2,
	client_minerva: 3,
	client_app: 4
}


// Note: a tk_stream_attach_failure, or tk_acked_unsent_boxes, or tk_invalid_frame_type_or_arguments from server
// should be treated as an internal reset (client_minerva).



/**
 * (copied from minerva/newlink.py)
 *
 * An interface for frame-based communication that abstracts
 * away the Comet logic and transports.
 *
 * Your Minerva protocols should implement this.
 *
 * Note: if you call stream.reset, some (or all) of the boxes you
 * have recently sent may be lost. If you need a proper close, use
 * your own boxes to determine that it is safe to close, then call reset.
 *
 * Note: the stream never ends due to inactivity (there
 * are no timeouts in Stream). If you want to end the stream,
 * call stream.reset(u"reason why")
 *
 * I'm analogous to {@code twisted.internet.interfaces.IProtocol}
 *
 * @interface
 */
cw.net.IMinervaProtocol = function() {

}

/**
 * Called when this stream has just started.
 *
 * You'll want to keep the stream around with {@code this.stream = stream}.
 *
 * @param {!cw.net.Stream} stream the Stream that was just started.
 */
cw.net.IMinervaProtocol.prototype.streamStarted = function(stream) {

}

/**
 * Called when this stream has ended.
 *
 * @param {!cw.net.WhoReset} whoReset Who reset the stream?
 * @param {string} reasonString The reason why stream has reset.
 */
cw.net.IMinervaProtocol.prototype.streamReset = function(whoReset, reasonString) {

}

/**
 * Called whenever box(es) are received.
 *
 * @param {!Array.<*>} boxes The received boxes.
 */
cw.net.IMinervaProtocol.prototype.stringsReceived = function(boxes) {

}



/**
 * Implemented by Minerva transports. You shouldn't need this.
 *
 * @private
 * @interface
 *
 * TODO: all transports must be Disposable?
 */
cw.net.IMinervaTransport = function() {

}
// lastBoxSent attribute?

/**
 * Write boxes in queue `queue` to the peer.
 * This never writes boxes that were already written to the peer over this transport
 * (because all transports are TCP-reliable).
 *
 * @param {!cw.net.Queue} queue
 */
cw.net.IMinervaTransport.prototype.writeStrings_ = function(queue) { // No 'start' argument unlike newlink.py

}

/**
 * Close this transport. Usually happens if the transport is no longer
 * useful.
 */
cw.net.IMinervaTransport.prototype.closeGently_ = function() {

}

/**
 * The stream that this transport is related to is resetting. Transport
 * must notify peer of the reset.
 *
 * @param {string} reasonString A plain-English reason why the stream is resetting
 */
cw.net.IMinervaTransport.prototype.reset_ = function(reasonString) {

}



/**
 * @param {!Object} clock Something that provides IWindowTime. TODO XXX use CallQueue instead?
 * @param {!Object} protocol
 * @param {!Object} locator
 *
 * @constructor
 *
 * TODO: make Stream a Disposable and add dispose methods?
 */
cw.net.Stream = function(clock, protocol, locator) {
	this.clock_ = clock;
	this.protocol_ = protocol;
	this.locator_ = locator;
	this.streamId_ = goog.string.getRandomString() + goog.string.getRandomString(); // usually 25 or 26 characters
}

/**
 *  Counter to uniquely identify the transports in this Stream
 * @type {number}
 */
cw.net.Stream.prototype.transportCount_ = -1;

/**
 * The primary transport (getting S2C boxes)
 * @type {Object}
 */
cw.net.Stream.prototype.primaryTransport_ = null;


/**
 * Send boxes `boxes` to the peer.
 *
 * @param {!Array.<*>} boxes Boxes to send.
 *
 */
cw.net.Stream.prototype.sendStrings_ = function(boxes) {
	1/0
}

/**
 * Reset (disconnect) with reason `reasonString`.
 *
 * @param {string} reasonString Reason why resetting the stream
 */
cw.net.Stream.prototype.reset_ = function(reasonString) {
	1/0
}

/**
 * Called by transports to tell me that it has received boxes.
 *
 * @param {!Object} transport The transport that received these boxes.
 * @param {Array.<*>} boxes In-order boxes that transport has received.
 */
cw.net.Stream.prototype.stringsReceived_ = function(transport, boxes) {
	1/0
}

/**
 * Called by transports to tell me that server has received at least some of
 * our C2S boxes.
 *
 * @param {!Array.<*>} sackInfo
 */
cw.net.Stream.prototype.sackReceived_ = function(sackInfo) {
	1/0
}

// notifyFinish?
// producers?
