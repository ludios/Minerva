/**
 * @fileoverview This file includes the relevant frame encoders and decoders
 * 	that Minerva client needs.
 */

goog.provide('cw.net.HelloFrame');
goog.provide('cw.net.StringFrame');
goog.provide('cw.net.SeqNumFrame');
goog.provide('cw.net.SackFrame');
goog.provide('cw.net.YouCloseItFrame');
goog.provide('cw.net.PaddingFrame');
goog.provide('cw.net.ResetFrame');
goog.provide('cw.net.TransportKillFrame');
goog.provide('cw.net.InvalidFrame');
goog.provide('cw.net.decodeFrameFromServer');

goog.require('goog.debug.Error');
goog.require('goog.json');
goog.require('goog.structs.Map');
goog.require('goog.string');
goog.require('goog.debug');
goog.require('goog.array');
goog.require('cw.checktype');
goog.require('cw.string');
goog.require('cw.repr');
goog.require('cw.eq');


/**
 * This is thrown when an encoded frame cannot be decoded.
 * @param {string} msg Reason why parse failed
 * @constructor
 * @extends {goog.debug.Error}
 */
cw.net.InvalidFrame = function(msg) {
	goog.debug.Error.call(this, msg);
};
goog.inherits(cw.net.InvalidFrame, goog.debug.Error);
cw.net.InvalidFrame.prototype.name = 'cw.net.InvalidFrame';


/**
 * This is thrown when an encoded hello frame cannot be decoded.
 * @param {string} msg Reason why parse failed
 * @constructor
 * @extends {cw.net.InvalidFrame}
 */
cw.net.InvalidHello = function(msg) {
	goog.debug.Error.call(this, msg);
};
goog.inherits(cw.net.InvalidHello, cw.net.InvalidFrame);
cw.net.InvalidHello.prototype.name = 'cw.net.InvalidHello';


/**
 * The largest integer that can be represented in JavaScript without
 * losing integral precision.
 * @private
 */
cw.net.LARGEST_INTEGER_ = Math.pow(2, 53);


/**
 * A number larger than the largest integer than can be represented
 * in JavaScript. Note: the ` + 1`ed number is not larger.
 * @private
 */
cw.net.LARGER_THAN_LARGEST_INTEGER_ = cw.net.LARGEST_INTEGER_ + 2;


/**
 * Hello frame properties. Keep in sync with minerva/newlink.py
 * @enum {string}
 * @private
 */
cw.net.HelloProperty_ = {
	transportNumber: 'tnum',
	protocolVersion: 'ver',
	httpFormat: 'format',
	requestNewStream: 'new',
	streamId: 'id',
	credentialsData: 'cred',
	streamingResponse: 'ming',
	needPaddingBytes: 'pad',
	maxReceiveBytes: 'maxb',
	maxOpenTime: 'maxt',
	useMyTcpAcks: 'tcpack',
	succeedsTransport: 'eeds',
	lastSackSeenByClient: 'lastack'
}


/**
 * HTTP format for the Minerva transport
 * @enum {number}
 * @private
 */
cw.net.HttpFormat_ = {
	FORMAT_XHR: 2,
	FORMAT_HTMLFILE: 3
}


/**
 * @private
 */
cw.net.AllHttpFormats_ = [
	cw.net.HttpFormat_.FORMAT_XHR,
	cw.net.HttpFormat_.FORMAT_HTMLFILE
];


/**
 * @private
 */
cw.net.ensureNonNegIntegralInt_ = function(value) {
	return cw.checktype.ensureIntInRange(value, 0, cw.net.LARGEST_INTEGER_);
}


/**
 * Convert arbitrary JSON-decoded blob of objects into a
 * {@code cw.net.HelloFrame}. Throws {@code cw.net.InvalidHello}
 * if there were errors in the blob of objects.
 *
 * This was translated from the Python code
 * {@code minerva.frames.helloDataToHelloFrame}. Major changes are:
 * 	- use of ensureIntInRange instead of ensureNonNegIntLimit
 *	- JavaScript conveniently returns undefined for missing properties, so
 * 	  we pass those through to ensure...()
 *   - We avoid `value = ensureIntInRange(value)` because unlike in Python,
 * 	  all numbers are floats anyway. In the Python code we were concerned
 *     about converting floats to ints/longs.
 *
 * @param {!goog.structs.Map} helloData a Map of a blob of objects
 * @return {!cw.net.HelloFrame}
 */
cw.net.helloDataToHelloFrame_ = function(helloData) {
	var HP = cw.net.HelloProperty_;
	var MISSING_ = {};

	var obj = new cw.net.HelloFrame();

	// credentialsData is always optional
	obj.credentialsData = helloData.get(HP.credentialsData, "");
	if(!(goog.isString(obj.credentialsData)) ||
	!(cw.net.isValidShortRestrictedString_(obj.credentialsData))) {
		throw new cw.net.InvalidHello("bad credentialsData");
	}

	var lastSackSeen = helloData.get(HP.lastSackSeenByClient, MISSING_);
	if(lastSackSeen == MISSING_ || !goog.isString(lastSackSeen)) {
		throw new cw.net.InvalidHello("lastSackSeenByClient missing or not a string");
	}
	obj.lastSackSeenByClient = cw.net.sackStringToSackFrame_(lastSackSeen);
	if(obj.lastSackSeenByClient == null) {
		throw new cw.net.InvalidHello("bad lastSackSeenByClient");
	}

	// requestNewStream is always optional. If missing or False/0, transport
	// is intended to attach to an existing stream.
	obj.requestNewStream = cw.checktype.ensureBool(helloData.get(HP.requestNewStream, false));
	if(obj.requestNewStream == null) {
		throw new cw.net.InvalidHello("bad requestNewStream");
	}

	obj.transportNumber = cw.net.ensureNonNegIntegralInt_(
		helloData.get(HP.transportNumber));
	if(obj.transportNumber == null) {
		throw new cw.net.InvalidHello("bad transportNumber");
	}

	obj.protocolVersion = helloData.get(HP.protocolVersion);
	if(obj.protocolVersion !== 2) {
		throw new cw.net.InvalidHello("bad protocolVersion");
	}

	obj.streamingResponse = cw.checktype.ensureBool(
		helloData.get(HP.streamingResponse));
	if(obj.streamingResponse == null) {
		throw new cw.net.InvalidHello("bad streamingResponse");
	}

	// Rules for streamId: must be 20-30 inclusive bytes, must not
	// contain codepoints > 127
	obj.streamId = helloData.get(HP.streamId);
	// In Python Minerva, instead of the \x00-\x7F check, we just
	// check that simplejson gave us a `str` instead of a `unicode`.
	if(!goog.isString(obj.streamId) || !/^([\x00-\x7F]{20,30})$/.test(obj.streamId)) {
		throw new cw.net.InvalidHello("bad streamId");
	}

	// succeedsTransport is always optional. If missing, the client does not
	// want to get S2C strings over this transport. If null, the client does,
	// but the transport does not succeed an existing primary transport. If a
	// number, the transport might succeed an existing primary transport.
	var eeds = helloData.get(HP.succeedsTransport, MISSING_);
	if(eeds != MISSING_) {
		// If not exactly null, it must be a non-negative integral number.
		if(eeds !== null) {
			if(cw.net.ensureNonNegIntegralInt_(eeds) == null) {
				throw new cw.net.InvalidHello("bad succeedsTransport");
			}
		}
		obj.succeedsTransport = eeds;
	}

	var httpFormat = helloData.get(HP.httpFormat, MISSING_);
	if(httpFormat != MISSING_) {
		if(!goog.array.contains(cw.net.AllHttpFormats_, httpFormat)) {
			throw new cw.net.InvalidHello("bad httpFormat");
		}
		obj.httpFormat = httpFormat;
	} else {
		obj.httpFormat = null;
	}

	// needPaddingBytes is always optional. If missing, 0.
	obj.needPaddingBytes = cw.checktype.ensureIntInRange(
		helloData.get(HP.needPaddingBytes, 0), 0, 16*1024);
	if(obj.needPaddingBytes == null) {
		throw new cw.net.InvalidHello("bad needPaddingBytes");
	}

	// maxReceiveBytes is optional and has no limit by default
	obj.maxReceiveBytes = cw.net.ensureNonNegIntegralInt_(
		helloData.get(HP.maxReceiveBytes, cw.net.LARGEST_INTEGER_));
	if(obj.maxReceiveBytes == null) {
		throw new cw.net.InvalidHello("bad maxReceiveBytes");
	}

	// maxOpenTime is optional and has no limit by default
	obj.maxOpenTime = cw.net.ensureNonNegIntegralInt_(
		helloData.get(HP.maxOpenTime, cw.net.LARGEST_INTEGER_));
	if(obj.maxOpenTime == null) {
		throw new cw.net.InvalidHello("bad maxOpenTime");
	}

	return obj;
}



/**
 * We do nothing in this constructor. Caller is responsible for setting
 * the correct properties.
 * @constructor
 */
cw.net.HelloFrame = function() {
	// TODO: add @type for each
	this.transportNumber;
	this.protocolVersion;
	this.httpFormat;
	this.requestNewStream;
	this.streamId;
	this.credentialsData;
	this.streamingResponse;
	this.needPaddingBytes;
	this.maxReceiveBytes;
	this.maxOpenTime;
	this.useMyTcpAcks;
	this.succeedsTransport;
	this.lastSackSeenByClient;
}

/**
 * Test two frames for equality.
 * @param {*} other
 * @param {!Array.<string>} messages
 * @return {boolean}
 */
cw.net.HelloFrame.prototype.equals = function(other, messages) {
	if(!(other instanceof cw.net.HelloFrame)) {
		return false;
	}

	var myProperties = cw.net.HelloFrame.makePropertyArray_(this);
	var otherProperties = cw.net.HelloFrame.makePropertyArray_(other);

	return cw.eq.equals(myProperties, otherProperties, messages);
}

/**
 * @param {!Array.<string>} sb
 */
cw.net.HelloFrame.prototype.__reprToPieces__ = function(sb) {
	// TODO: Make it actually human-readable, perhaps we need
	// an ordered HelloProperty_ list
	sb.push('<HelloFrame properties=');
	cw.repr.reprToPieces(cw.net.HelloFrame.makePropertyArray_(this), sb);
	sb.push('>');
}

/**
 * Decodes a string from an untrusted source to a {@code cw.net.HelloFrame}.
 *
 * @param {string} frameString A string that ends with "H".
 * @return {!cw.net.HelloFrame}
 */
cw.net.HelloFrame.decode = function(frameString) {
	var json = cw.string.withoutLast(frameString, 1);
	// We want to prohibit JSON that has leading or trailing whitespace
	// (like Python Minerva does), so we do this test and make a dangerous
	// inference: if it starts with "{" and ends with "}" and evals successfully,
	// there was no leading/trailing whitespace.
	var startsWithCurly = cw.string.startsWithAlt(json, "{");
	var endsWithCurly = goog.string.endsWith(json, "}");
	if(!startsWithCurly || !endsWithCurly || !goog.json.isValid_(json)) {
		throw new cw.net.InvalidHello("Dangerous JSON or doesn't end with }");
	}
	/** @preserveTry */
	try {
		var blob = eval('(' + json + ')');
	} catch(e) {
		e = goog.debug.normalizeErrorObject(e);
		throw new cw.net.InvalidHello("Un-eval'able JSON: " + e.name + ": " + e.message);
	}

	// We know it is an !Object because of the careful "{" checking above.
	return cw.net.helloDataToHelloFrame_(
		new goog.structs.Map(/** @type {!Object.<*>} */ (blob)));
}

/**
 * @private
 * @param {!cw.net.HelloFrame} helloFrame
 * @return {!Array.<*>}
 */
cw.net.HelloFrame.makePropertyArray_ = function(helloFrame) {
	return [
		helloFrame.transportNumber,
		helloFrame.protocolVersion,
		helloFrame.httpFormat,
		helloFrame.requestNewStream,
		helloFrame.streamId,
		helloFrame.credentialsData,
		helloFrame.streamingResponse,
		helloFrame.needPaddingBytes,
		helloFrame.maxReceiveBytes,
		helloFrame.maxOpenTime,
		helloFrame.useMyTcpAcks,
		helloFrame.succeedsTransport,
		helloFrame.lastSackSeenByClient
	];
}

/**
 * @return {string} Encoded frame
 */
cw.net.HelloFrame.prototype.encode = function() {
	var HP = cw.net.HelloProperty_;

	var compact = {};
	compact[HP.transportNumber] = this.transportNumber;
	compact[HP.protocolVersion] = this.protocolVersion;
	compact[HP.httpFormat] = this.httpFormat;
	compact[HP.requestNewStream] = this.requestNewStream;
	compact[HP.streamId] = this.streamId;
	compact[HP.credentialsData] = this.credentialsData;
	compact[HP.streamingResponse] = this.streamingResponse;
	compact[HP.needPaddingBytes] = this.needPaddingBytes;
	compact[HP.maxReceiveBytes] = this.maxReceiveBytes;
	compact[HP.maxOpenTime] = this.maxOpenTime;
	compact[HP.useMyTcpAcks] = this.useMyTcpAcks;
	compact[HP.succeedsTransport] = this.succeedsTransport;
	//compact[HP.lastSackSeenByClient] = this.lastSackSeenByClient;

	// TODO: require this.lastSackSeenByClient to be a "sack tuple" as defined by that typedef
	if(this.lastSackSeenByClient instanceof cw.net.SackFrame) {
		compact[HP.lastSackSeenByClient] = cw.string.withoutLast(this.lastSackSeenByClient.encode(), 1);
	} else {
		compact[HP.lastSackSeenByClient] = this.lastSackSeenByClient;
	}


	// Remove the "undefined" values; TODO: don't do this
	for(var k in compact) {
		if(compact[k] === undefined) {
			delete compact[k];
		}
	}

	return goog.json.serialize(compact) + 'H';
}

/**
 * @return {boolean} True if this HelloFrame indicates that
 *	client wants to receive strings, else false.
 */
cw.net.HelloFrame.prototype.wantsStrings = function() {
	// TODO: be safe against Object.prototype mutations?
	return this.succeedsTransport !== undefined;
}



/**
 * @param {string} string
 * @constructor
 */
cw.net.StringFrame = function(string) {
	this.string = string;
}

/**
 * Test two frames for equality.
 * @param {*} other
 * @param {!Array.<string>} messages
 * @return {boolean}
 */
cw.net.StringFrame.prototype.equals = function(other, messages) {
	return (
		other instanceof cw.net.StringFrame &&
		this.string == other.string);
}

/**
 * @param {!Array.<string>} sb
 */
cw.net.StringFrame.prototype.__reprToPieces__ = function(sb) {
	sb.push("new StringFrame(");
	cw.repr.reprToPieces(this.string, sb);
	sb.push(")");
}

/**
 * @param {string} frameString A string that ends with " ".
 * @return {!cw.net.StringFrame}
 */
cw.net.StringFrame.decode = function(frameString) {
	return new cw.net.StringFrame(frameString.substr(0, frameString.length - 1));
}

/**
 * @return {string} Encoded frame
 */
cw.net.StringFrame.prototype.encode = function() {
	return this.string + ' ';
}



/**
 * @param {number} seqNum
 * @constructor
 */
cw.net.SeqNumFrame = function(seqNum) {
	this.seqNum = seqNum;
}

/**
 * Test two frames for equality.
 * @param {*} other
 * @param {!Array.<string>} messages
 * @return {boolean}
 */
cw.net.SeqNumFrame.prototype.equals = function(other, messages) {
	return (
		other instanceof cw.net.SeqNumFrame &&
		this.seqNum == other.seqNum);
}

/**
 * @param {!Array.<string>} sb
 */
cw.net.SeqNumFrame.prototype.__reprToPieces__ = function(sb) {
	sb.push('new SeqNumFrame(', String(this.seqNum), ')');
}

/**
 * @param {string} frameString A string that ends with "N".
 * @return {!cw.net.SeqNumFrame}
 */
cw.net.SeqNumFrame.decode = function(frameString) {
	var seqNum = cw.string.strToNonNegLimit(
		cw.string.withoutLast(frameString, 1),
		cw.net.LARGEST_INTEGER_);
	if(seqNum == null) {
		throw new cw.net.InvalidFrame("bad seqNum");
	}
	return new cw.net.SeqNumFrame(seqNum);
}

/**
 * @return {string} Encoded frame
 */
cw.net.SeqNumFrame.prototype.encode = function() {
	return this.seqNum + 'N';
}



/**
 * @param {string} sackString A string containing SACK data.
 * @return {cw.net.SackFrame}
 * @private
 */
cw.net.sackStringToSackFrame_ = function(sackString) {
	var parts = sackString.split('|');

	if(parts.length != 2) {
		return null;
	}

	var ackNumber = cw.string.strToIntInRange(
		parts[1], -1, cw.net.LARGEST_INTEGER_);

	if(ackNumber == null) {
		return null;
	}

	var sackList = [];

	if(parts[0]) {
		var sackListStrs = parts[0].split(',');
		for(var i=0, len=sackListStrs.length; i < len; i++) {
			var sackNum = cw.string.strToNonNegLimit(sackListStrs[i], cw.net.LARGEST_INTEGER_);
			if(sackNum == null) {
				return null;
			}
			sackList.push(sackNum);
		}
	}

	return new cw.net.SackFrame(ackNumber, sackList);
}


/**
 * @param {number} ackNumber
 * @param {!Array.<number>} sackList
 * @constructor
 */
cw.net.SackFrame = function(ackNumber, sackList) {
	this.ackNumber = ackNumber;
	this.sackList = sackList;
}

/**
 * Test two frames for equality.
 * @param {*} other
 * @param {!Array.<string>} messages
 * @return {boolean}
 */
cw.net.SackFrame.prototype.equals = function(other, messages) {
	return (
		other instanceof cw.net.SackFrame &&
		this.ackNumber == other.ackNumber &&
		cw.eq.equals(this.sackList, other.sackList, messages));
}

/**
 * @param {!Array.<string>} sb
 */
cw.net.SackFrame.prototype.__reprToPieces__ = function(sb) {
	sb.push('new SackFrame(', String(this.ackNumber), ', ');
	cw.repr.reprToPieces(this.sackList, sb);
	sb.push(')');
}

/**
 * @param {string} frameString A string that ends with "A".
 * @return {!cw.net.SackFrame}
 */
cw.net.SackFrame.decode = function(frameString) {
	var frame = cw.net.sackStringToSackFrame_(
		cw.string.withoutLast(frameString, 1));
	if(frame == null) {
		throw new cw.net.InvalidFrame("bad sackString");
	}
	return frame;
}

/**
 * @return {string} Encoded frame
 */
cw.net.SackFrame.prototype.encode = function() {
	return this.sackList.join(',') + '|' + this.ackNumber + 'A';
}




/**
 * @constructor
 */
cw.net.YouCloseItFrame = function() {

}

/**
 * @param {!Array.<string>} sb
 */
cw.net.YouCloseItFrame.prototype.__reprToPieces__ = function(sb) {
	sb.push('new YouCloseItFrame()');
}

/**
 * Test two frames for equality.
 * @param {*} other
 * @param {!Array.<string>} messages
 * @return {boolean}
 */
cw.net.YouCloseItFrame.prototype.equals = function(other, messages) {
	return (other instanceof cw.net.YouCloseItFrame);
}

/**
 * @param {string} frameString A string that ends with "Y".
 * @return {!cw.net.YouCloseItFrame}
 */
cw.net.YouCloseItFrame.decode = function(frameString) {
	if(frameString.length != 1) {
		throw new cw.net.InvalidFrame("leading garbage");
	}
	return new cw.net.YouCloseItFrame();
}

/**
 * @return {string} Encoded frame
 */
cw.net.YouCloseItFrame.prototype.encode = function() {
	return 'Y';
}




/**
 * @param {number} numBytes How many bytes of padding
 * @constructor
 */
cw.net.PaddingFrame = function(numBytes) {
	this.numBytes = numBytes;
}

/**
 * Test two frames for equality.
 * @param {*} other
 * @param {!Array.<string>} messages
 * @return {boolean}
 */
cw.net.PaddingFrame.prototype.equals = function(other, messages) {
	return (
		other instanceof cw.net.PaddingFrame &&
		this.numBytes == other.numBytes);
}

/**
 * @param {!Array.<string>} sb
 */
cw.net.PaddingFrame.prototype.__reprToPieces__ = function(sb) {
	sb.push('new PaddingFrame(', String(this.numBytes), ')');
}

/**
 * @param {string} frameString A string that ends with "P".
 * @return {!cw.net.PaddingFrame}
 */
cw.net.PaddingFrame.decode = function(frameString) {
	return new cw.net.PaddingFrame(frameString.length - 1);
}

/**
 * @return {string} Encoded frame
 */
cw.net.PaddingFrame.prototype.encode = function() {
	var p = Array(this.numBytes);
	p.push('P');
	return p.join(' ');
}



/**
 * @param {string} string
 * @return {boolean} Return true if {@code string} has 0-255 characters,
 *	and all bytes are within inclusive range 0x20 " " - 0x7E "~".
 * @private
 */
cw.net.isValidShortRestrictedString_ = function(string) {
	return string.length <= 255 && /^([ -~]*)$/.test(string);
}


/**
 * A reset frame indicates this side has given up on the Stream.
 * A reset frame from the server implies a transport kill as well.
 *
 * @param {string} reasonString Why the Stream reset.
*	ASCII (0x20-0x7E)-only C{str}, max 255 bytes.
 * @param {boolean} applicationLevel Whether the reset was application-level
 * 	(not caused by Minerva internals).
 * @constructor
 */
cw.net.ResetFrame = function(reasonString, applicationLevel) {
	this.reasonString = reasonString;
	this.applicationLevel = applicationLevel;
}

/**
 * Test two frames for equality.
 * @param {*} other
 * @param {!Array.<string>} messages
 * @return {boolean}
 */
cw.net.ResetFrame.prototype.equals = function(other, messages) {
	return (
		other instanceof cw.net.ResetFrame &&
		this.reasonString == other.reasonString &&
		this.applicationLevel == other.applicationLevel);
}

/**
 * @param {!Array.<string>} sb
 */
cw.net.ResetFrame.prototype.__reprToPieces__ = function(sb) {
	sb.push("new ResetFrame(");
	cw.repr.reprToPieces(this.reasonString, sb);
	sb.push(", ", String(this.applicationLevel), ")");
}

/**
 * @param {string} frameString A string that ends with "!".
 * @return {!cw.net.ResetFrame}
 */
cw.net.ResetFrame.decode = function(frameString) {
	var reasonString = frameString.substr(0, frameString.length - 3);

	if(!cw.net.isValidShortRestrictedString_(reasonString)) {
		throw new cw.net.InvalidFrame("illegal bytes in reasonString");
	}

	// Either "|0" or "|1"
	var applicationLevelStr = frameString.substr(frameString.length - 3, 2);
	var applicationLevel = {'|0': false, '|1': true}[applicationLevelStr];
	if(applicationLevel == null) {
		throw new cw.net.InvalidFrame("bad applicationLevel");
	}

	return new cw.net.ResetFrame(reasonString, applicationLevel);
}

/**
 * @return {string} Encoded frame
 */
cw.net.ResetFrame.prototype.encode = function() {
	return this.reasonString + '|' + Number(this.applicationLevel) + '!';
}




/**
 * Transport kill reasons. Keep in sync with minerva/newlink.py
 *
 * @enum {string}
 */
cw.net.TransportKillReason = {
	stream_attach_failure: 'stream_attach_failure',
	acked_unsent_strings: 'acked_unsent_strings',
	invalid_frame_type_or_arguments: 'invalid_frame_type_or_arguments',
	frame_corruption: 'frame_corruption',
	rwin_overflow: 'rwin_overflow'
}

/**
 * @type {!Object.<string, !cw.net.TransportKillReason>}
 *
 * @private
 */
cw.net.AllTransportKillReasons_ = {
	'stream_attach_failure': cw.net.TransportKillReason.stream_attach_failure,
	'acked_unsent_strings': cw.net.TransportKillReason.acked_unsent_strings,
	'invalid_frame_type_or_arguments': cw.net.TransportKillReason.invalid_frame_type_or_arguments,
	'frame_corruption': cw.net.TransportKillReason.frame_corruption,
	'rwin_overflow': cw.net.TransportKillReason.rwin_overflow
};


/**
 * @param {!cw.net.TransportKillReason} reason
 *
 * @constructor
 */
cw.net.TransportKillFrame = function(reason) {
	this.reason = reason;
}

/**
 * Test two frames for equality.
 * @param {*} other
 * @param {!Array.<string>} messages
 * @return {boolean}
 */
cw.net.TransportKillFrame.prototype.equals = function(other, messages) {
	return (
		other instanceof cw.net.TransportKillFrame &&
		this.reason == other.reason);
}

/**
 * @param {!Array.<string>} sb
 */
cw.net.TransportKillFrame.prototype.__reprToPieces__ = function(sb) {
	sb.push('new TransportKillFrame(');
	cw.repr.reprToPieces(this.reason, sb);
	sb.push(')');
}

/**
 * @param {string} frameString A string that ends with "K".
 * @return {!cw.net.TransportKillFrame}
 */
cw.net.TransportKillFrame.decode = function(frameString) {
	var reason = frameString.substr(0, frameString.length - 1);
	reason = cw.net.AllTransportKillReasons_[reason];
	if(reason == null) {
		throw new cw.net.InvalidFrame("unknown kill reason: " + reason);
	}

	return new cw.net.TransportKillFrame(reason);
}

/**
 * @return {string} Encoded frame
 */
cw.net.TransportKillFrame.prototype.encode = function() {
	return this.reason + 'K';
}



/**
 * @type {(cw.net.HelloFrame|cw.net.StringFrame|cw.net.SeqNumFrame|
 * 	cw.net.SackFrame|cw.net.YouCloseItFrame|cw.net.PaddingFrame|
 * 	cw.net.ResetFrame|cw.net.TransportKillFrame)}
 */
cw.net.Frame = goog.typedef;


/**
 * Decode a frame received from a Minerva client.
 *
 * @param {string} frameString
 * @return {!cw.net.Frame} Decoded frame
 */
cw.net.decodeFrameFromClient = function(frameString) {
	if(!frameString) {
		throw new cw.net.InvalidFrame("0-length frame");
	}

	var lastByte = frameString.substr(frameString.length - 1, 1);

	// Keep this ordered by most-probable first
	if (lastByte == " ") {
		return cw.net.StringFrame.decode(frameString);
	} else if(lastByte == "A") {
		return cw.net.SackFrame.decode(frameString);
	} else if(lastByte == "N") {
		return cw.net.SeqNumFrame.decode(frameString);
	} else if(lastByte == "H") {
		return cw.net.HelloFrame.decode(frameString);
	} else if(lastByte == "!") {
		return cw.net.ResetFrame.decode(frameString);
	} else {
		throw new cw.net.InvalidFrame("Invalid frame type " + lastByte);
	}
}


/**
 * Decode a frame received from a Minerva server.
 * 
 * @param {string} frameString
 * @return {!cw.net.Frame} Decoded frame
 */
cw.net.decodeFrameFromServer = function(frameString) {
	if(!frameString) {
		throw new cw.net.InvalidFrame("0-length frame");
	}

	var lastByte = frameString.substr(frameString.length - 1, 1);

	// Keep this ordered by most-probable first
	if (lastByte == " ") {
		return cw.net.StringFrame.decode(frameString);
	} else if(lastByte == "A") {
		return cw.net.SackFrame.decode(frameString);
	} else if(lastByte == "N") {
		return cw.net.SeqNumFrame.decode(frameString);
	} else if(lastByte == "Y") {
		return cw.net.YouCloseItFrame.decode(frameString);
	} else if(lastByte == "P") {
		return cw.net.PaddingFrame.decode(frameString);
	} else if(lastByte == "!") {
		return cw.net.ResetFrame.decode(frameString);
	} else if(lastByte == "K") {
		return cw.net.TransportKillFrame.decode(frameString);
	} else {
		throw new cw.net.InvalidFrame("Invalid frame type " + lastByte);
	}
}
