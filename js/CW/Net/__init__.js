// import CW

CW.Error.subclass(CW.Net, 'ParseError');


/**
 * A decoder that extracts frames from an object with an L{responseText}.
 * The decoder must be "pushed" by using L{receivedToByte}.
 *
 * L{responseText} is assumed to have unicode/byte equivalence.
 * No non-ASCII characters are allowed, because of our optimizations,
 * and because of browser bugs.
 */
CW.Class.subclass(CW.Net, "ResponseTextDecoder").methods(
	/**
	 * L{xObject} is an L{XMLHttpRequest} or L{XDomainRequest} object
	 * or any object with a unicode C{responseText} property.
	 *
	 * L{MAX_LENGTH} is the maximum length of a string to decode, in bytes.
	 */
	function __init__(self, xObject, MAX_LENGTH) {
		self._offset = 0;
		// Need to have at least 1 byte before doing any parsing
		self._ignoreUntil = 1;
		// Optimization hack: this acts as both a mode and a readLength
		self._modeOrReadLength = 0; // 0 means mode LENGTH, >= 1 means mode DATA
		self.xObject = xObject;
		if(!MAX_LENGTH) {
			MAX_LENGTH = 1024*1024*1024;
		}
		self.setMaxLength(MAX_LENGTH);
	},

	function setMaxLength(self, MAX_LENGTH) {
		self.MAX_LENGTH = MAX_LENGTH;
		self.MAX_LENGTH_LEN = (''+MAX_LENGTH).length;
	},

	/**
	 * Check for new data in L{xObject} and return an array of new frames.
	 * If possible, provide a number L{responseTextLength} if you know
	 * how many bytes are available in L{responseText} (but do not look at the
	 * property responseText or responseText.length yourself). Passing a too-low
	 * L{responseTextLength} will not break the decoder, as long as you call it later
	 * with a higher number. Pass C{null} for L{responseTextLength} if you do not know
	 * how many bytes are in L{responseText}.
	 *
	 * Passing a number for L{responseTextLength} helps avoid unnecessary
	 * property lookups of L{responseText}, which increases performance
	 * in Firefox, and potentially other browsers.
	 */
	function getNewFrames(self, responseTextLength) {
		if(responseTextLength !== null && responseTextLength < self._ignoreUntil) {
			// There certainly isn't enough data in L{responseText} yet, so return.
			return [];
		}

		var text = self.xObject.responseText;
		if(responseTextLength === null) {
			responseTextLength = text.length;
		}
		var strings = [];
		for(;;) {
			if(self._modeOrReadLength === 0) { // mode LENGTH
				var colon = text.indexOf(':', self._offset);
				if(colon === -1) {
					if(responseTextLength - self._offset > self.MAX_LENGTH_LEN) {
						throw new CW.Net.ParseError("length too long");
					}
					// There's not even a colon yet? Break.
					////console.log('No colon yet. Break.')
					break;
					// Unlike minerva._protocols, don't eager-fail if there are
					// non-digits; it's a waste of CPU time.
				}

				var extractedLengthStr = text.substr(self._offset, colon-self._offset);
				// Accept only positive integers with no leading zero.
				// TODO: maybe disable this check for long-time user agents with no problems
				if(!/^[1-9]\d*$/.test(extractedLengthStr)) {
					throw new CW.Net.ParseError("corrupt length: " + extractedLengthStr);
				}
				// TODO: check if `+extractedLengthStr' is faster; use it if it is.
				var readLength = parseInt(extractedLengthStr, 10);
				if(readLength > self.MAX_LENGTH) {
					throw new CW.Net.ParseError("length too long: " + readLength);
				}
				self._modeOrReadLength = readLength;
				self._offset += (''+readLength).length + 1; // + 1 to skip over the ":"
			} else { // mode DATA
				if(self._offset + self._modeOrReadLength > responseTextLength) {
					////console.log('Not enough data bytes yet. Break.');
					break;
				}
				var s = text.substr(self._offset, self._modeOrReadLength);
				self._offset += self._modeOrReadLength;
				self._modeOrReadLength = 0;
				strings.push(s);
			}
		}
		if(self._modeOrReadLength === 0) {
			// Can't ignore anything when still receiving the length
			self._ignoreUntil = responseTextLength + 1;
		} else {
			self._ignoreUntil = self._offset + self._modeOrReadLength;
		}
		////console.log('_ignoreUntil now', self._ignoreUntil);
		return strings;
	}
);
