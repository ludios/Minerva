/**
 * @fileoverview Bluesky stream demo: shows a live sample of public Bluesky
 * posts.  The server side is minerva/demos/bskystream.py.
 *
 * This replaced DemosMinerva's LiveJournal stream demo (ljstream.js).
 */

goog.provide('bskystream');

goog.require('goog.debug.DivConsole');
goog.require('goog.debug.Logger');
goog.require('goog.debug.LogManager');
goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.events.EventType');
goog.require('goog.style');
goog.require('goog.ui.Component.EventType');
goog.require('goog.ui.CustomButton');
goog.require('cw.eventual');
goog.require('cw.json');
goog.require('cw.net.ClientStream');
goog.require('cw.net.IStringProtocol');
goog.require('cw.net.HttpStreamingMode');
goog.require('cw.net.demo.getEndpointByQueryArgs');
goog.require('cw.repr');



bskystream.logger = goog.debug.Logger.getLogger('bskystream.logger');


window.onerror = function(msg, url, lineNumber) {
	bskystream.logger.severe('window.onerror: message: ' + cw.repr.repr(msg) +
		'\nURL: ' + url + '\nLine Number: ' + lineNumber);
};

/**
 * @implements {cw.net.IStringProtocol}
 * @constructor
 */
bskystream.BskyClientProtocol = function() {
};

bskystream.BskyClientProtocol.prototype.streamStarted = function(stream) {
	this.stream_ = stream;
	this.stream_.sendString('subprotocol:bskystream');
	this.sendPreferences();
};

bskystream.BskyClientProtocol.prototype.streamReset = function(reasonString, applicationLevel) {
	bskystream.logger.info(
		'streamReset: reasonString=' + cw.repr.repr(reasonString) +
		', applicationLevel=' + applicationLevel);
	bskystream.appendImportantMessage('Disconnected from server.  Try reloading this page.');
	bskystream.lastProto = null;
};

/**
 * @param {string} s
 */
bskystream.BskyClientProtocol.prototype.stringReceived = function(s) {
	var payload = cw.json.parse(s);
	var msgType = payload[0];
	var body = payload[1];

	if(msgType == "NewPost") {
		bskystream.appendPost(body);
	} else {
		bskystream.logger.warning('Strange message from server: ' +
			cw.repr.repr(payload));
	}
};

bskystream.BskyClientProtocol.prototype.sendPreferences = function() {
	var language = bskystream.getLanguage();
	bskystream.logger.info('Sending preferences to server: language=' +
		cw.repr.repr(language));
	this.stream_.sendString(cw.json.asciify(
		["SetPreferences", {"language": language}]
	));
};

/**
 * @param {string} reason
 */
bskystream.BskyClientProtocol.prototype.reset = function(reason) {
	bskystream.logger.info('resetting with reason: ' + reason);
	this.stream_.reset(reason);
};

/**
 * @type {?bskystream.BskyClientProtocol}
 */
bskystream.lastProto = null;


bskystream.callQueue = new cw.eventual.CallQueue(goog.global['window']);


/**
 * @param {string} message
 */
bskystream.appendImportantMessage = function(message) {
	var d = goog.dom.createDom;
	bskystream.appendRow(d('span', {'class': 'important-message'}, message));
};


bskystream.idleFired = function() {
	if(!bskystream.lastProto) {
		return;
	}
	bskystream.resetStream("idle timeout fired");
	bskystream.lastProto = null;

	bskystream.appendImportantMessage(
		"No key/mouse activity, stopping stream to save " +
		"everyone's bandwidth.");
};


/**
 * @type {?number}
 */
bskystream.idleTimeout = null;

/**
 * @param {*} ev
 */
bskystream.activityDetected = function(ev) {
	if(bskystream.idleTimeout != null) {
		bskystream.callQueue.clock.clearTimeout(bskystream.idleTimeout);
	}

	// Only need a timeout if we have an active Stream
	if(bskystream.lastProto) {
		bskystream.idleTimeout = bskystream.callQueue.clock.setTimeout(
			bskystream.idleFired, 600 * 1000);
	}
};


/**
 * @type {!Array.<!goog.events.EventType>}
 */
bskystream.activityEvents = [
	goog.events.EventType.CLICK,
	goog.events.EventType.FOCUS,
	goog.events.EventType.KEYDOWN,
	goog.events.EventType.KEYPRESS];
bskystream.clickListen = goog.events.listen(
	window, bskystream.activityEvents, bskystream.activityDetected, true);


/**
 * @type {!goog.dom.DomHelper}
 */
bskystream.domHelper = new goog.dom.DomHelper();


/**
 * @param {!Element} el
 * @return {boolean} Whether the bottom of {@code el} is in (or above) the
 * 	viewport.
 */
bskystream.bottomIsInViewport = function(el) {
	var bottom = goog.style.getPageOffsetTop(el) + el.offsetHeight;
	var viewportBottom = goog.dom.getDocumentScroll().y +
		bskystream.domHelper.getViewportSize().height;
	return bottom <= viewportBottom;
};


/**
 * The most posts (and messages) to keep on the page.
 * @type {number}
 */
bskystream.maxRows = 1000;


/**
 * @type {number}
 */
bskystream.rowsAdded = 0;


/**
 * @type {boolean}
 */
bskystream.automaticScroll = true;


/**
 * @param {!Element} element
 */
bskystream.appendRow = function(element) {
	var className = 'row-' + (bskystream.rowsAdded % 2 == 0 ? 'even' : 'odd');
	var rowDiv = goog.dom.createDom('div', {'class': className}, element);

	var container = goog.dom.getElement('bskystream-container');
	container.appendChild(rowDiv);
	bskystream.rowsAdded += 1;
	while(container.childNodes.length > bskystream.maxRows) {
		container.removeChild(container.firstChild);
	}

	if(bskystream.automaticScroll && !bskystream.bottomIsInViewport(rowDiv)) {
		rowDiv.scrollIntoView(false);
	}
};


bskystream.clearRows = function() {
	goog.dom.removeChildren(goog.dom.getElement('bskystream-container'));
};


/**
 * @param {!Object} post A post from the server, with url, handle, text,
 * 	langs, and media.
 */
bskystream.appendPost = function(post) {
	var d = goog.dom.createDom;
	var row = d('span', {},
		d('a', {'href': post['url'], 'class': 'post-author', 'target': '_blank',
			'rel': 'noopener noreferrer'}, '@' + post['handle']),
		' ',
		d('span', {'class': 'post-text'}, post['text']));
	if(post['media']) {
		goog.dom.append(row, ' ',
			d('span', {'class': 'post-media'}, '[' + post['media'] + ']'));
	}
	if(post['langs'].length) {
		goog.dom.append(row, ' ',
			d('span', {'class': 'post-langs'}, post['langs'].join(', ')));
	}
	bskystream.appendRow(row);
};


bskystream.startStream = function() {
	var streamPolicy = new cw.net.demo.DemoStreamPolicy();
	bskystream.lastProto = new bskystream.BskyClientProtocol();
	bskystream.activityDetected(null);
	var endpoint = cw.net.demo.getEndpointByQueryArgs(bskystream.callQueue);
	var stream = new cw.net.ClientStream(
		endpoint, streamPolicy, bskystream.callQueue);
	stream.bindToProtocol(bskystream.lastProto);
	stream.start();
};


/**
 * @param {string} reason
 */
bskystream.resetStream = function(reason) {
	bskystream.lastProto.reset(reason);
};


/**
 * @return {?string} The language to show posts in, or null for all.
 */
bskystream.getLanguage = function() {
	var select = /** @type {!HTMLSelectElement} */ (goog.dom.getElement('language'));
	return select.value || null;
};


bskystream.fitContainerUnderHeader = function() {
	goog.dom.getElement('bskystream-container').style.marginTop =
		goog.dom.getElement('demo-header').offsetHeight + 'px';
};


bskystream.setupView = function() {
	goog.events.listen(goog.dom.getElement('language'),
		goog.events.EventType.CHANGE,
		function(e) {
			if(bskystream.lastProto) {
				bskystream.lastProto.sendPreferences();
			}
		}
	);

	goog.events.listen(goog.dom.getElement('automatic_scroll'),
		goog.events.EventType.CLICK,
		function(e) {
			bskystream.automaticScroll = e.target.checked;
		}
	);

	var clearPostsButton = new goog.ui.CustomButton('Clear posts');
	clearPostsButton.addClassName('clear-posts-button');
	clearPostsButton.render(goog.dom.getElement('prefs'));
	goog.events.listen(clearPostsButton, goog.ui.Component.EventType.ACTION,
		function() {
			bskystream.clearRows();
			window.scrollTo(0, 0);
		});

	// The header is fixed, and its height depends on the window's width.
	bskystream.fitContainerUnderHeader();
	goog.events.listen(window, goog.events.EventType.RESIZE,
		bskystream.fitContainerUnderHeader);
};


bskystream.setupLogging = function() {
	if(cw.net.demo.isLoggingEnabled()) {
		goog.debug.LogManager.getRoot().setLevel(goog.debug.Logger.Level.ALL);
		var divConsole = new goog.debug.DivConsole(goog.dom.getElement('log'));
		divConsole.setCapturing(true);
	} else {
		goog.debug.LogManager.getRoot().setLevel(goog.debug.Logger.Level.OFF);
	}
	bskystream.logger.info('Logger works.');
};


bskystream.init = function() {
	bskystream.setupLogging();
	bskystream.setupView();
	bskystream.startStream();
};


goog.exportSymbol('__bskystream_init', bskystream.init);
