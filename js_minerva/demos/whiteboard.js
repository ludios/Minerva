/**
 * @fileoverview Whiteboard demo.  The server side is
 * minerva/demos/whiteboard.py.
 */

goog.provide('whiteboard');

goog.require('goog.asserts');
goog.require('goog.color');
goog.require('goog.debug.DivConsole');
goog.require('goog.debug.Logger');
goog.require('goog.debug.LogManager');
goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.events.Event');
goog.require('goog.events.EventType');
goog.require('goog.events.BrowserEvent');
goog.require('goog.graphics');
goog.require('goog.math');
goog.require('goog.style');
goog.require('goog.net.cookies');
goog.require('goog.ui.Component.EventType');
goog.require('goog.ui.CustomButton');
goog.require('goog.ui.ColorPalette');
goog.require('goog.Uri');
goog.require('cw.eventual');
goog.require('cw.string');
goog.require('cw.json');
goog.require('cw.net.ClientStream');
goog.require('cw.net.IStringProtocol');
goog.require('cw.net.HttpStreamingMode');
goog.require('cw.net.demo.getEndpointByQueryArgs');
goog.require('cw.repr');


whiteboard.logger = goog.debug.Logger.getLogger('whiteboard.logger');


window.onerror = function(msg, url, lineNumber) {
	whiteboard.logger.severe('window.onerror: message: ' + cw.repr.repr(msg) +
		'\nURL: ' + url + '\nLine Number: ' + lineNumber)
};

/**
 * @implements {cw.net.IStringProtocol}
 * @constructor
 */
whiteboard.WhiteboardProtocol = function() {
};

whiteboard.WhiteboardProtocol.prototype.streamStarted = function(stream) {
	this.stream_ = stream;
	this.stream_.sendString('subprotocol:whiteboard');
};

whiteboard.WhiteboardProtocol.prototype.streamReset = function(reasonString, applicationLevel) {
	whiteboard.logger.info(
		'streamReset: reasonString=' + cw.repr.repr(reasonString) +
		', applicationLevel=' + applicationLevel);
	var d = goog.dom.createDom;
	goog.dom.append(/** @type {!Element} */ (goog.dom.getElement('demo-header')), ' ',
		d('b', {}, d('a', {'href': String(window.location)}, '[DISCONNECTED] - RELOAD')));
	whiteboard.lastProto = null;
};

/**
 * @param {string} s
 */
whiteboard.WhiteboardProtocol.prototype.handleString_ = function(s) {
	function fail() {
		whiteboard.logger.severe('Could not handle string: ' + cw.repr.repr(s));
	}

	// TODO: handle errors?
	var payload = cw.json.parse(s);
	var msgType = payload[0];
	var body = payload[1];

	if(msgType == "Point") {
		// TODO: handle errors?
		var point = body;
		whiteboard.drawCircleAt(point['x'], point['y'], point['color']);
	} else if(msgType == "ClearBoard") {
		whiteboard.clearMyBoard();
	} else {
		whiteboard.logger.warning('Strange message from server: ' +
			cw.repr.repr(payload));
	}
};

// TODO: add back "suspend drawing" / "resume drawing" by implementing
// two new commands.  Need suspend because CanvasGraphics is slow to
// redraw - exhbits O(N^2) behavior, at least in Mobile WebKit.  See graphics.js.

/**
 * @param {string} s
 */
whiteboard.WhiteboardProtocol.prototype.stringReceived = function(s) {
	this.handleString_(s);
};

/**
 * @param {string} reason
 */
whiteboard.WhiteboardProtocol.prototype.reset = function(reason) {
	whiteboard.logger.info('resetting with reason: ' + reason);
	this.stream_.reset(reason);
};

/**
 * @param {number} x
 * @param {number} y
 */
whiteboard.WhiteboardProtocol.prototype.sendCircle = function(x, y, color) {
	whiteboard.logger.info('Telling server about circle at: ' +
		x + ', ' + y + ' with color ' + color);
	this.stream_.sendString(cw.json.asciify(
		["Point", {"x": x, "y": y, "color": color}]
	));
};

/**
 * Tell the server to clear the board.
 */
whiteboard.WhiteboardProtocol.prototype.sendClearBoard = function() {
	whiteboard.logger.info('Telling server to clear the board.');
	this.stream_.sendString(cw.json.asciify(
		["ClearBoard", null]
	));
};



/**
 * @type {?whiteboard.WhiteboardProtocol}
 */
whiteboard.lastProto = null;


whiteboard.callQueue = new cw.eventual.CallQueue(goog.global['window']);


whiteboard.idleFired = function() {
	if(!whiteboard.lastProto) {
		return;
	}
	whiteboard.resetStream("idle timeout fired");
	whiteboard.lastProto = null;
};


/**
 * @type {?number}
 */
whiteboard.idleTimeout = null;

/**
 * @param {*} ev
 */
whiteboard.activityDetected = function(ev) {
	if(whiteboard.idleTimeout != null) {
		whiteboard.callQueue.clock.clearTimeout(whiteboard.idleTimeout);
	}

	// Only need a timeout if we have an active Stream
	if(whiteboard.lastProto) {
		whiteboard.idleTimeout = whiteboard.callQueue.clock.setTimeout(
			whiteboard.idleFired, 3600 * 24 * 3 * 1000);
	}
};


/**
 * @type {!Array.<!goog.events.EventType>}
 */
whiteboard.activityEvents = [
	goog.events.EventType.CLICK,
	goog.events.EventType.FOCUS,
	goog.events.EventType.KEYDOWN,
	goog.events.EventType.KEYPRESS];
whiteboard.clickListen = goog.events.listen(
	window, whiteboard.activityEvents, whiteboard.activityDetected, true);


whiteboard.startStream = function() {
	var streamPolicy = new cw.net.demo.DemoStreamPolicy();
	whiteboard.lastProto = new whiteboard.WhiteboardProtocol();
	whiteboard.activityDetected(null);
	var endpoint = cw.net.demo.getEndpointByQueryArgs(whiteboard.callQueue);
	var stream = new cw.net.ClientStream(
		 endpoint, streamPolicy, whiteboard.callQueue);
	stream.bindToProtocol(whiteboard.lastProto);
	stream.start();
};


/**
 * @param {string} reason
 */
whiteboard.resetStream = function(reason) {
	whiteboard.lastProto.reset(reason);
};


whiteboard.reconnectStream = function() {
	if(whiteboard.lastProto) {
		whiteboard.lastProto.reset('because user clicked reconnect button');
	}
	whiteboard.startStream();
};


whiteboard.drawRandomStuff = function() {
	var fill = new goog.graphics.SolidFill('yellow');
	var stroke = new goog.graphics.Stroke(2, 'green');
	//var rectElement = whiteboard.lastDrawArea.drawRect(30, 10, 100, 80, stroke, fill);
};


whiteboard.drawCircleAt = function(x, y, color) {
	var fill = new goog.graphics.SolidFill(color);
	var stroke = new goog.graphics.Stroke(1, 'black');
	var circleElement = whiteboard.lastDrawArea.drawCircle(x, y, 5, stroke, fill);
};


/**
 * The board's size in pixels, as in minerva/demos/whiteboard.py.
 * @type {number}
 * @const
 */
whiteboard.WIDTH = 800;

/**
 * @type {number}
 * @const
 */
whiteboard.HEIGHT = 600;


whiteboard.clearMyBoard = function() {
	whiteboard.lastDrawArea.dispose();
	whiteboard.setupDrawArea();
};


whiteboard.clearBoard = function() {
	whiteboard.clearMyBoard();
	whiteboard.lastProto.sendClearBoard();
};


whiteboard.handleClick = function(ev) {
	var patchedEv = new goog.events.BrowserEvent(ev);
	// Browsers may report fractional coordinates (on zoomed pages, say),
	// and rounding one in the board's last half pixel would leave the board.
	var x = goog.math.clamp(Math.round(patchedEv.offsetX), 0, whiteboard.WIDTH - 1);
	var y = goog.math.clamp(Math.round(patchedEv.offsetY), 0, whiteboard.HEIGHT - 1);
	whiteboard.drawCircleAt(x, y, whiteboard.currentColor);
	whiteboard.lastProto.sendCircle(x, y, whiteboard.currentColor);
};


whiteboard.setupDrawArea = function() {
	var graphics = goog.graphics.createGraphics(whiteboard.WIDTH, whiteboard.HEIGHT);
	whiteboard._drawAreaDiv = goog.dom.getElement('drawArea');
	graphics.render(whiteboard._drawAreaDiv);
	whiteboard.lastDrawArea = graphics;
};


whiteboard.setupDrawAreaOverlay = function() {
	var overlay = goog.dom.getElement('drawAreaOverlay');
	goog.style.setUnselectable(overlay, true);
	goog.events.listen(overlay, goog.events.EventType.CLICK,
		whiteboard.handleClick, false);
};


whiteboard.defaultColor = '#E06666';


/**
 * @param {{target: !goog.ui.ColorPalette}} ev
 */
whiteboard.onColorEvent = function(ev) {
	var palette = ev.target;
	var color = palette.getSelectedColor();
	if(!color) {
		color = whiteboard.defaultColor;
	}
	whiteboard.currentColor = color;
	goog.net.cookies.set('whiteboard_defaultColor', color);
	goog.style.setStyle(goog.dom.getElement('whiteboard-cp-value'),
		'background-color', color);
	var whiteboardCpValue = goog.dom.getElement('whiteboard-cp-value');
	whiteboardCpValue.title = color;

	var colorHex = goog.color.parse(color).hex;
	goog.dom.setTextContent(whiteboardCpValue, colorHex);

	var rgb = goog.color.hexToRgb(colorHex);
	var lighter = goog.color.rgbArrayToHex(goog.color.lighten(rgb, 0.45));
	goog.style.setStyle(whiteboardCpValue, 'color', lighter);
};


/**
 * @param {!Array.<string>} colors
 * @param {number} width
 * @return {!goog.ui.ColorPalette}
 */
whiteboard.createColorPalette = function(colors, width) {
	var cp = new goog.ui.ColorPalette(colors);
	cp.setSize(width); // If we only set the columns, the rows are calculated.
	cp.render(goog.dom.getElement('whiteboard-cp'));
	goog.events.listen(cp, goog.ui.Component.EventType.ACTION, whiteboard.onColorEvent);
	return cp;
};


whiteboard.setupControls = function() {
	var leftControlsDiv = /** @type {!HTMLElement} */(
		goog.dom.getElement('whiteboard-controls-left'));
	var rightControlsDiv = /** @type {!HTMLElement} */(
		goog.dom.getElement('whiteboard-controls-right'));

	//var text = goog.dom.createDom('div', {'class': 'goog-inline-block pick-a-color'}, 'Pick a color:');
	//goog.dom.append(leftControlsDiv, text);

	var whiteboardCp = goog.dom.createDom('div',
		{'class': 'goog-inline-block', 'id': 'whiteboard-cp'});
	goog.dom.append(leftControlsDiv, whiteboardCp);

	var whiteboardCpValue = goog.dom.createDom('div',
		{'class': 'goog-inline-block', 'id': 'whiteboard-cp-value'});
	goog.dom.append(leftControlsDiv, whiteboardCpValue);

	// The colors are from closure/goog/demos/palette.html
	var palette = whiteboard.createColorPalette([
		'#EA9999', '#F9CB9C', '#FFE599', '#B6D7A8',
		'#A2C4C9', '#9FC5E8', '#B4A7D6', '#D5A6BD',
		'#E06666', '#F6B26B', '#FFD966', '#93C47D',
		'#76A5AF', '#6FA8DC', '#8E7CC3', '#C27BA0',
		'#CC0000', '#E69138', '#F1C232', '#6AA84F',
		'#45818E', '#3D85C6', '#674EA7', '#A64D79'
	], 8);

	palette.setSelectedColor(whiteboard.defaultColor);
	// Fire a fake "event" because the above doesn't.
	whiteboard.onColorEvent({target: palette});


	var resetBoardButton = new goog.ui.CustomButton('Clear board');
	resetBoardButton.addClassName('clear-board-button');
	resetBoardButton.render(rightControlsDiv);

	goog.events.listen(resetBoardButton, goog.ui.Component.EventType.ACTION,
		whiteboard.clearBoard);
};


whiteboard.setupColor = function() {
	var c = goog.net.cookies.get('whiteboard_defaultColor');
	// The server accepts only #RRGGBB colors.
	if(c && /^#[0-9a-f]{6}$/i.test(c)) {
		whiteboard.defaultColor = c;
	}
	whiteboard.currentColor = whiteboard.defaultColor;
};


whiteboard.setupLogging = function() {
	whiteboard._queryData = new goog.Uri(document.location).getQueryData();
	whiteboard.useLogging = Boolean(Number(whiteboard._queryData.get('logging', '0')));

	if(whiteboard.useLogging) {
		goog.debug.LogManager.getRoot().setLevel(goog.debug.Logger.Level.ALL);
		var logDiv = document.getElementById('log');
		var divConsole = new goog.debug.DivConsole(logDiv);
		divConsole.setCapturing(true);
	} else {
		goog.debug.LogManager.getRoot().setLevel(goog.debug.Logger.Level.OFF);
	}

	whiteboard.logger.info('Logger works.');
};


whiteboard.init = function() {
	whiteboard.setupLogging();
	whiteboard.setupColor();
	whiteboard.setupControls();
	whiteboard.setupDrawAreaOverlay();
	whiteboard.setupDrawArea();
	whiteboard.drawRandomStuff();
	whiteboard.startStream();
};


goog.exportSymbol('__whiteboard_init', whiteboard.init);
