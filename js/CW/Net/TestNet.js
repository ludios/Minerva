/**
 * Tests for CW.Net
 */


// import CW.UnitTest
// import CW.URI
// import CW.Net


CW.Net.TestNet.	hasXDomainRequest = function hasXDomainRequest() {
	try {
		XDomainRequest;
		return true;
	} catch(e) {
		return false;
	}
}



CW.Class.subclass(CW.Net.TestNet, 'MockXHR').pmethods({

	__init__: function() {
		this.log = [];
		this._reset();
	},

	_reset: function() {
		this.onreadystatechange = CW.emptyFunc;
		this.responseText = "";
		this.readyState = 0;
	},

	open: function(verb, url, async) {
		this.log.push(['open', verb, url, async]);
	},

	send: function(post) {
		this.log.push(['send', post]);
	},

	abort: function() {
		this.log.push(['abort']);
		this._reset();
	}
});



CW.Class.subclass(CW.Net.TestNet, 'MockXDR').pmethods({

	__init__: function() {
		this.log = [];
		// Maybe this should be in _reset? Check real XDomainRequest behavior.
		this.timeout = 10000;

		this._reset();
	},

	_reset: function() {
		this.onerror = CW.emptyFunc;
		this.onprogress = CW.emptyFunc;
		this.onload = CW.emptyFunc;
		this.ontimeout = CW.emptyFunc;
		this.responseText = "";
		this.readyState = 0;
	},

	open: function(verb, url) {
		// XDR is always async. It doesn't have this 3rd `true' argument, but append it anyway
		// just to make things easier to test. Doing this makes the XDR mock log look
		// like the XHR mock log.
		this.log.push(['open', verb, url, true]);
	},

	send: function(post) {
		this.log.push(['send', post]);
	},

	abort: function() {
		this.log.push(['abort']);
		this._reset();
	}
});




CW.UnitTest.TestCase.subclass(CW.Net.TestNet, 'GetXHRObjectTests').methods(
	/**
	 * L{CW.Net.getXHRObject} works in general.
	 */
	function test_getXHRObject(self) {
		var object = CW.Net.getXHRObject();
		self.assert(object, 'object must be truthy');
	}
);


/**
 * Base class for testing the general logic of L{UsableXHR} xor L{UsableXDR}.
 * These tests do not make any real connections.
 */
CW.UnitTest.TestCase.subclass(CW.Net.TestNet, '_BaseUsableXHDRLogicTests').methods(

	function setUp(self) {
		self.target = CW.URI.URL(''+window.location).update('fragment', null);
	},

	// Override _setupDummies
	// Override _finishRequest

	/**
	 * We can't make another request using this C{self.xhdr}
	 * object until the current request is finished.
	 */
	function test_requestStillActive(self) {
		self._setupDummies();
		self.assertThrows(
			CW.Net.RequestStillActive,
			function() { self.xhdr.request('GET', self.target) },
			"Wait for the Deferred to fire before making another request."
		);
	},


	/**
	 * After aborting, using the same C{self.xhdr} instance to make
	 * requests still works.
	 */
	function test_abortDoesntRuinState(self) {
		self._setupDummies();
		self.xhdr.abort();
		self._finishRequest();

		// Make the second request
		self.requestD = self.xhdr.request('POST', self.target, 'second');
		self._finishRequest();

		//CW.msg(CW.UnitTest.repr(self.mock.log));
		self.assertEqual([
			['open', 'POST', self.target.getString(), true], ['send', ''], ['abort'],
			['open', 'POST', self.target.getString(), true], ['send', 'second']
		], self.mock.log);
	},


	/**
	 * The request Deferred errback fires with error L{CW.Net.RequestAborted}.
	 *
	 * We use a dummy because some browsers finish a request so fast
	 * after .request(), that .abort() becomes a no-op (notably Opera 9/10, Safari 3)
	 */
	function test_abortReason(self) {
		self._setupDummies();
		self.assertEqual(self.mock.log, [['open', 'POST', self.target.getString(), true], ['send', '']]);

		var d = self.assertFailure(self.requestD, [CW.Net.RequestAborted]);

		self.xhdr.abort();
		self._finishRequest();

		return d;
	},


	/**
	 * The C{abort} method of the XHR object is only called once, even if
	 * C{self.xhdr.abort} is called multiple times.
	 *
	 * We use a dummy because calling .abort() multiple times on a browser's
	 * XHR object doesn't raise an exception or do anything important. We still
	 * want to prevent it from happening.
	 */
	function test_abortCalledOnlyOnce(self) {
		self._setupDummies();
		self.xhdr.abort();
		self.xhdr.abort();
		self.assertEqual(self.mock.log, [['open', 'POST', self.target.getString(), true], ['send', ''], ['abort']]);
	}

);



/**
 * These tests do not make any real connections.
 */
CW.Net.TestNet._BaseUsableXHDRLogicTests.subclass(CW.Net.TestNet, 'UsableXHRLogicTests').methods(

	function _setupDummies(self) {
		self.target.update('path', '/@testres_Minerva/404/');
		self.mock = CW.Net.TestNet.MockXHR();
		self.xhdr = CW.Net.UsableXHR(window, self.mock);
		self.requestD = self.xhdr.request('POST', self.target, '');
	},


	function _finishRequest(self) {
		self.mock.readyState = 4;
		self.mock.onreadystatechange(null);
	},


	// XHR-specific tests follow

	/**
	 * The implementation clears the C{onreadystatechange} property
	 * of the XHR object after the request is _done_. This is necessary to
	 * avoid memory leaks in IE.
	 */
	function test_onreadystatechangeResetAfterFinish(self) {
		self._setupDummies();

		// Finish the request and verify that onreadystatechange was
		// reset to L{CW.emptyFunc}
		self.mock.readyState = 4;
		self.mock.responseText = 'done';
		self.mock.onreadystatechange(null);
		self.assertIdentical(CW.emptyFunc, self.mock.onreadystatechange);
	},


	/**
	 * The implementations clears the C{onreadystatechange} property
	 * of the XHR object after the request is _aborted_. This is necessary to
	 * avoid memory leaks in IE.
	 */
	function test_onreadystatechangeResetAfterAborted(self) {
		self._setupDummies();

		// Abort the request and verify that onreadystatechange was
		// reset to L{CW.emptyFunc}
		self.xhdr.abort();
		self.mock.readyState = 4;
		self.mock.responseText = 'aborted';
		self.mock.onreadystatechange(null);
		self.assertIdentical(CW.emptyFunc, self.mock.onreadystatechange);
	}

);



/**
 * Run L{UsableXHRLogicTests} except with the XDR object, even if XDomainRequest
 * is not available in this browser.
 */
CW.Net.TestNet._BaseUsableXHDRLogicTests.subclass(CW.Net.TestNet, 'UsableXDRLogicTests').methods(

	function _setupDummies(self) {
		self.target.update('path', '/@testres_Minerva/404/');
		self.mock = CW.Net.TestNet.MockXDR();
		self.xhdr = CW.Net.UsableXDR(window, function(){return self.mock});
		self.requestD = self.xhdr.request('POST', self.target);
	},


	function _finishRequest(self) {
		self.mock.readyState = 4;
		self.mock.onprogress();
		self.mock.onload();
	}
);



CW.UnitTest.TestCase.subclass(CW.Net.TestNet, 'UsableXHRRealRequestTests').methods(

	function setUp(self) {
		self.target = CW.URI.URL(''+window.location);
		self.xhdr = CW.Net.UsableXHR(window, CW.Net.getXHRObject());
	},


	function test_simpleResponseGET(self) {
		self.target.update('path', '/@testres_Minerva/SimpleResponse/?a=0');
		var d = self.xhdr.request('GET', self.target);
		d.addCallback(function(obj){
			self.assertEqual('{"you_sent_args": {"a": ["0"]}}', obj.responseText);
		});
		return d;
	},


	function test_simpleResponsePOST(self) {
		self.target.update('path', '/@testres_Minerva/SimpleResponse/');
		var d = self.xhdr.request('POST', self.target, 'hello\u00ff');
		d.addCallback(function(obj){
			self.assertEqual('{"you_posted_utf8": "hello\\u00ff"}', obj.responseText);
		});
		return d;
	},


	/**
	 * Make sure the #fragment is never sent as part of an XHR GET request.
	 * IE6-8 and Opera 10 are buggy. L{UsableXHR} works around it.
	 * If it fails to work around it, you'll see {"a": ["0#ignored1"]} instead of {"a": ["0"]}
	 */
	function test_fragmentIsIgnoredGET(self) {
		self.target.update('path', '/@testres_Minerva/SimpleResponse/?a=0').update('fragment', 'ignored1');
		var d = self.xhdr.request('GET', self.target);
		d.addCallback(function(obj){
			self.assertEqual('{"you_sent_args": {"a": ["0"]}}', obj.responseText);
		});
		return d;
	},


	/**
	 * Make sure the #fragment is never sent as part of an XHR POST request.
	 * IE6-8 and Opera 10 are buggy. L{UsableXHR} works around it.
	 * If it fails to work around it, you'll see {"a": ["0#ignored2"]} instead of {"a": ["0"]}
	 */
	function test_fragmentIsIgnoredPOST(self) {
		self.target.update('path', '/@testres_Minerva/SimpleResponse/?a=0').update('fragment', 'ignored2');
		var d = self.xhdr.request('GET', self.target);
		d.addCallback(function(obj){
			self.assertEqual('{"you_sent_args": {"a": ["0"]}}', obj.responseText);
		});
		return d;
	},


	function test_simpleReuseGET(self) {
		var responses = [];
		self.target.update('path', '/@testres_Minerva/SimpleResponse/?b=0');

		var d = self.xhdr.request('GET', self.target);

		d.addCallback(function(obj){
			responses.push(obj.responseText);
			// This mutation is okay
			var d2 = self.xhdr.request('GET', self.target.update('path', '/@testres_Minerva/SimpleResponse/?b=1'));
			d2.addCallback(function(obj2){
				responses.push(obj2.responseText);
			});
			return d2;
		});

		d.addCallback(function(){
			self.assertEqual(
				[
					'{"you_sent_args": {"b": ["0"]}}',
					'{"you_sent_args": {"b": ["1"]}}'
				],
				responses
			);
		})

		return d;
	},


	function test_simpleReusePOST(self) {
		var responses = [];
		self.target.update('path', '/@testres_Minerva/SimpleResponse/');

		var d = self.xhdr.request('POST', self.target, 'A');

		d.addCallback(function(obj){
			responses.push(obj.responseText);
			// This mutation is okay
			var d2 = self.xhdr.request('POST', self.target.update('path', '/@testres_Minerva/SimpleResponse/'), 'B');
			d2.addCallback(function(obj2){
				responses.push(obj2.responseText);
			});
			return d2;
		});

		d.addCallback(function(){
			self.assertEqual(
				[
					'{"you_posted_utf8": "A"}',
					'{"you_posted_utf8": "B"}'
				],
				responses
			);
		})

		return d;
	},


	/**
	 * C{.abort()} returns undefined.
	 * Calling C{.abort()} multiple times is okay.
	 *
	 * Note that we can't assert that an aborted request doesn't actually make
	 * it to the server. This is because some browsers send the XHR requests
	 * really fast, and are done before you call .abort().
	 */
	function test_abort(self) {
		self.target.update('path', '/@testres_Minerva/404/');
		var requestD = self.xhdr.request('POST', self.target, '');

		self.assertIdentical(undefined, self.xhdr.abort());
		self.assertIdentical(undefined, self.xhdr.abort());
		self.assertIdentical(undefined, self.xhdr.abort());

		// Note that errback won't always get fired. Sometimes it'll be callback
		// because browser couldn't abort before the request finished.
		requestD.addErrback(function(){
			return undefined;
		});

		return requestD;
	}
);


/**
 * Run L{UsableXHRRealRequestTests} except with the XDR object, if it's available in this
 * browser.
 */
CW.Net.TestNet.UsableXHRRealRequestTests.subclass(CW.Net.TestNet, 'UsableXDRRealRequestTests').methods(

	function setUp(self) {
		if(!CW.Net.TestNet.hasXDomainRequest()) {
			throw new CW.UnitTest.SkipTest("XDomainRequest is required for this test.");
		}
		self.target = CW.URI.URL(''+window.location);
		self.xhdr = CW.Net.UsableXDR(window, function(){return new XDomainRequest()});
	}
);



CW.UnitTest.TestCase.subclass(CW.Net.TestNet, 'XDRErrorsTests').methods(

	function setUp(self) {
		if(!CW.Net.TestNet.hasXDomainRequest()) {
			throw new CW.UnitTest.SkipTest("XDomainRequest is required for this test.");
		}
		self.target = CW.URI.URL(''+window.location);
		self.xdr = CW.Net.UsableXDR(window, function(){return new XDomainRequest()});
	},


	/**
	 * Requesting a page via GET that doesn't send the right Origin headers
	 * causes a L{NetworkProblem}.
	 */
	function test_networkProblemGET(self) {
		self.target.update('path', '/@testres_Minerva/NoOriginHeader/');
		var requestD = self.xdr.request('GET', self.target);
		var d = self.assertFailure(requestD, [CW.Net.NetworkProblem]);
		return d;
	},


	/**
	 * Requesting a page via GET that doesn't send the right Origin headers
	 * causes a L{NetworkProblem}.
	 */
	function test_networkProblemPOST(self) {
		self.target.update('path', '/@testres_Minerva/NoOriginHeader/');
		var requestD = self.xdr.request('POST', self.target);
		var d = self.assertFailure(requestD, [CW.Net.NetworkProblem]);
		return d;
	},


	/**
	 * Requesting something on 0.0.0.0 causes a L{NetworkProblem}.
	 */
	function test_networkProblemBadIP(self) {
		self.target.update('host', '0.0.0.0');
		var requestD = self.xdr.request('GET', self.target);
		var d = self.assertFailure(requestD, [CW.Net.NetworkProblem]);
		return d;
	}
);



CW.UnitTest.TestCase.subclass(CW.Net.TestNet, 'XHRProgressCallbackTests').methods(

	function setUp(self) {
		self.target = CW.URI.URL(''+window.location);
		self.target.update('path', '/@testres_Minerva/404/');
		self.mock = CW.Net.TestNet.MockXHR();
		// Never advance the clock, to prevent Opera from doing a call at 50ms intervals.
		self.clock = CW.UnitTest.Clock();
	},

	/**
	 * Test that when onreadystatechange happens, C{progressCallback}
	 * is called.
	 */
	function test_onreadystatechangeCallsProgress(self) {
		self.xhr = CW.Net.UsableXHR(self.clock, self.mock);
		var calls = [];
		function progressCallback(obj, position, totalSize) {
			calls.push(arguments);
		}
		self.xhr.request('GET', self.target, '', progressCallback);
		self.mock.readyState = 3;
		self.mock.responseText = null; // responseText should not be looked at
		self.mock.onreadystatechange(null);
		self.mock.onreadystatechange(null);
		self.mock.onreadystatechange(null);

		self.assertEqual(
			[
				[self.mock, null, null],
				[self.mock, null, null],
				[self.mock, null, null]
			], calls
		);
	},

	/**
	 * Test that when onprogress then onreadystatechange happens,
	 * C{progressCallback} is called with good numbers.
	 */
	function test_onprogressFillsNumbers(self) {
		self.xhr = CW.Net.UsableXHR(self.clock, self.mock);
		var calls = [];
		function progressCallback(obj, position, totalSize) {
			calls.push(arguments);
		}
		self.xhr.request('GET', self.target, '', progressCallback);
		self.mock.readyState = 3;
		self.mock.responseText = null; // responseText should not be looked at
		self.mock.onprogress({position: 1, totalSize: 10});
		self.mock.onreadystatechange(null);
		self.mock.onprogress({position: 2, totalSize: 10});
		self.mock.onreadystatechange(null);
		self.mock.onprogress({position: 3, totalSize: 10});
		self.mock.onreadystatechange(null);

		self.assertEqual(
			[
				[self.mock, 1, 10],
				[self.mock, 2, 10],
				[self.mock, 3, 10]
			], calls
		);
	},

	/**
	 * Test that when onprogress gets a crappy event with
	 * e.position === undefined, it calls C{progressCallback}
	 * with (obj, null, lastKnownTotalSize)
	 */
	function test_onprogressFirefoxBugWorkaround(self) {
		self.xhr = CW.Net.UsableXHR(self.clock, self.mock);
		var calls = [];
		function progressCallback(obj, position, totalSize) {
			calls.push(arguments);
		}
		self.xhr.request('GET', self.target, '', progressCallback);
		self.mock.readyState = 3;
		self.mock.responseText = null; // responseText should not be looked at
		self.mock.onprogress({position: 1, totalSize: 10});
		self.mock.onreadystatechange(null);
		self.mock.onprogress({}); // the crappy event
		self.mock.onprogress({position: 5, totalSize: 10});
		self.mock.onreadystatechange(null);

		self.assertEqual(
			[
				[self.mock, 1, 10],
				[self.mock, null, 10],
				[self.mock, 5, 10]
			], calls
		);
	},


	/**
	 * Zero is an acceptable totalSize.
	 */
	function test_zeroTotalSizeIsOkay(self) {
		self.xhr = CW.Net.UsableXHR(self.clock, self.mock);
		var calls = [];
		function progressCallback(obj, position, totalSize) {
			calls.push(arguments);
		}
		self.xhr.request('GET', self.target, '', progressCallback);
		self.mock.readyState = 3;
		self.mock.responseText = null; // responseText should not be looked at
		self.mock.onprogress({position: 0, totalSize: 0});
		self.mock.onreadystatechange(null);

		self.assertEqual(
			[
				[self.mock, 0, 0]
			], calls
		);
	},


	/**
	 * Undefined or negative or large `totalSize's are treated as "unknown totalSize"
	 */
	function test_invalidTotalSizes(self) {
		self.xhr = CW.Net.UsableXHR(self.clock, self.mock);
		var calls = [];
		function progressCallback(obj, position, totalSize) {
			calls.push(arguments);
		}
		self.xhr.request('GET', self.target, '', progressCallback);
		self.mock.readyState = 3;
		self.mock.responseText = null; // responseText should not be looked at
		self.mock.onreadystatechange(null);
		self.mock.onprogress({position: 1, totalSize: -1});
		self.mock.onreadystatechange(null);
		self.mock.onprogress({position: 2, totalSize: -2});
		self.mock.onreadystatechange(null);
		self.mock.onprogress({position: 3, totalSize: undefined});
		self.mock.onreadystatechange(null);
		self.mock.onprogress({position: 4, totalSize: 2147483647 + 1}); // 2**31 + 1
		self.mock.onreadystatechange(null);

		self.assertEqual(
			[
				[self.mock, null, null],
				[self.mock, 1, null],
				[self.mock, 2, null],
				[self.mock, 3, null],
				[self.mock, 4, null]
			], calls
		);
	}
);



CW.UnitTest.TestCase.subclass(CW.Net.TestNet, 'XHRProgressCallbackOperaWorkaroundTests').methods(

	function setUp(self) {
		if(!window.opera) {
			throw new CW.UnitTest.SkipTest("This workaround only applies to Opera.");
		}
		self.clock = CW.UnitTest.Clock();

		self.target = CW.URI.URL(''+window.location);
		self.target.update('path', '/@testres_Minerva/404/');
		self.mock = CW.Net.TestNet.MockXHR();

	},

	/**
	 * In Opera, if C{progressCallback} is truthy, progressCallback is
	 * called every 50ms, even if no new data has been received.
	 */
	function test_progressCallbackCreatesPoller(self) {
		self.xhr = CW.Net.UsableXHR(self.clock, self.mock);
		var calls = []
		function progressCallback(obj, position, totalSize) {
			calls.push(arguments);
		}
		self.xhr.request('GET', self.target, '', progressCallback);
		self.mock.readyState = 3;
		self.assertIdentical(0, calls.length);
		self.clock.advance(100);
		// Opera should not know the position
		self.assertEqual(
			[
				[self.mock, null, null],
				[self.mock, null, null]
			], calls
		);
	},


	/**
	 * In Opera, if C{progressCallback} is truthy, but readyState is
	 * not 3, progressCallback is not called.
	 */
	function test_progressCallbackButNotReadyState3(self) {
		self.xhr = CW.Net.UsableXHR(self.clock, self.mock);
		var calls = []
		function progressCallback(obj, position, totalSize) {
			calls.push(arguments);
		}
		self.xhr.request('GET', self.target, '', progressCallback);

		self.mock.readyState = 0;
		self.clock.advance(100);
		self.assertIdentical(0, calls.length);

		self.mock.readyState = 1;
		self.clock.advance(100);
		self.assertIdentical(0, calls.length);

		self.mock.readyState = 2;
		self.clock.advance(100);
		self.assertIdentical(0, calls.length);

		self.mock.readyState = 4;
		self.clock.advance(100);
		self.assertIdentical(0, calls.length);
	},


	/**
	 * In Opera, if C{progressCallback} is falsy, no setInterval is set.
	 */
	function test_noProgressCallbackNoPoller(self) {
		self.xhr = CW.Net.UsableXHR(self.clock, self.mock);
		self.xhr.request('GET', self.target, '', null);
		self.assertEqual(0, self.clock._countPendingEvents());
		self.mock.readyState = 3;
		self.clock.advance(100);
		self.assertEqual(0, self.clock._countPendingEvents());
	}
);




CW.UnitTest.TestCase.subclass(CW.Net.TestNet, 'XDRProgressCallbackTests').methods(

	function setUp(self) {
		if(!CW.Net.TestNet.hasXDomainRequest()) {
			throw new CW.UnitTest.SkipTest("XDomainRequest is required for this test.");
		}
		self.target = CW.URI.URL(''+window.location);
		self.target.update('path', '/@testres_Minerva/404/');
		self.mock = CW.Net.TestNet.MockXHR();
		self.clock = CW.UnitTest.Clock();
	},

	/**
	 * Test that when onprogress happens, C{progressCallback}
	 * is called.
	 */
	function test_onprogressCallsProgress(self) {
		self.xhr = CW.Net.UsableXDR(self.clock, function(){return self.mock});
		var calls = [];
		function progressCallback(obj, position, totalSize) {
			calls.push(arguments);
		}
		self.xhr.request('GET', self.target, '', progressCallback);
		// note: no usage of readyState, despite its existence
		self.mock.responseText = null; // responseText should not be looked at
		self.mock.onprogress();
		self.mock.onprogress();
		self.mock.onprogress();

		self.assertEqual(
			[
				[self.mock, null, null],
				[self.mock, null, null],
				[self.mock, null, null]
			], calls
		);
	},

	/**
	 * Test that when onload happens, C{progressCallback}
	 * is called.
	 */
	function test_onloadCallsProgress(self) {
		self.xhr = CW.Net.UsableXDR(self.clock, function(){return self.mock});
		var calls = [];
		function progressCallback(obj, position, totalSize) {
			calls.push(arguments);
		}
		self.xhr.request('GET', self.target, '', progressCallback);
		// note: no usage of readyState, despite its existence
		self.mock.responseText = null; // responseText should not be looked at
		self.mock.onprogress();
		self.mock.onprogress();
		self.mock.onload();

		self.assertEqual(
			[
				[self.mock, null, null],
				[self.mock, null, null],
				[self.mock, null, null]
			], calls
		);
	}
);
