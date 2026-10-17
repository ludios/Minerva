"""
Minerva-related things that make it easy to use Minerva on your website
or in your twistd plugin, but are not absolutely necessary.
"""

import sys
import textwrap
from functools import partial

from twisted.python import log

import simplejson
from simplejson import decoder as dec

from webmagic.untwist import BetterResource
from webmagic.pathmanip import getCacheBrokenHref

from securetypes import securedict

_postImportVars = vars().keys()


def htmldumps(*args, **kwargs):
	"""
	Like L{simplejson.dumps}, but backslash every '/' to prevent
	an HTML closing tag from closing a script.
	"""
	return simplejson.dumps(*args, **kwargs).replace('/', r'\/')


class StrictDecodeError(Exception):
	pass



def _raiseDecodeError(obj):
	raise StrictDecodeError(
		"NaN, Infinity, and -Infinity are forbidden")


strictDecoder = simplejson.decoder.JSONDecoder(
	parse_constant=_raiseDecodeError,
	object_pairs_hook=securedict)


def _intOrNone(v):
	try:
		return int(v)
	except ValueError:
		return None


def _isDecodeBuggy():
	"""
	Returns C{True} if simplejson has this bug:
	http://code.google.com/p/simplejson/issues/detail?id=85

	This returns True if the simplejson is buggy, even if speedups
	are currently disabled.
	"""
	# The bug was fixed in r236 @ https://code.google.com/p/simplejson/source/list
	# and 2.1.2 was released shortly after.
	return tuple(_intOrNone(x) for x in simplejson.__version__.split('.')) < (2, 1, 2)

_decodeBuggy = _isDecodeBuggy()


def strictSecureDecodeJson(s):
	"""
	Decode JSON-containing bytestring `s`, forbidding any whitespace or
	trailing bytes.  JSON objects are decoded to L{securedict}s instead of
	L{dict}s.  NaN, Infinity, and -Infinity are rejected because they are
	not part of the JSON spec.

	If any problems are found, L{JSONDecodeError} is raised.
	"""
	decoded, at = strictDecoder.raw_decode(s)
	# The off-by-one bug affects only the pure Python decoder, not speedups.
	# Note that applications may toggle speedups at runtime with
	# simplejson._toggle_speedups()
	if _decodeBuggy and dec.scanstring is dec.py_scanstring:
		at += 1
	if at != len(s):
		raise StrictDecodeError(
			"Expected to reach the end of the string but %d bytes "
			"remained" % (len(s) - at,))
	return decoded


class ConflictingTemplateVars(Exception):
	pass



class MinervaBootstrap(BetterResource):
	"""
	Deprecated resource used by chatapp and DemosMinerva.  Don't use.
	"""
	isLeaf = True

	def __init__(self, fileCache, templateFile, dictionary):
		"""
		C{fileCache} is a L{webmagic.filecache.FileCache}.
		C{templateFile} is a L{FilePath} representing the jinja2 template to
			use.  The latest file contents are cached forever, even if you
			delete your references to the L{MinervaBootstrap}.
		C{dictionary} is a C{dict} whose keys are passed to the template.
			If this is mutated, new requests will have the new dictionary
			contents.
		"""
		BetterResource.__init__(self)
		self._fileCache = fileCache
		self._templateFile = templateFile
		self._dictionary = dictionary


	def render_GET(self, request):
		from minerva.mserver import _contentToTemplate

		# chatapp needs this
		try:
			standaloneClient = bool(int(request.args['standaloneClient'][0]))
		except (KeyError, IndexError, ValueError):
			standaloneClient = False

		# This jinja2 stuff is for the html page, not the JavaScript
		template, _ = self._fileCache.getContent(
			self._templateFile.path, transform=_contentToTemplate)

		bootstrapDict = {}
		bootstrapDict['htmldumps'] = htmldumps
		bootstrapDict['cacheBreakLink'] =  partial(
			getCacheBrokenHref, self._fileCache, request)
		bootstrapDict['standaloneClient'] = standaloneClient

		dictionary = self._dictionary.copy()
		for k, v in bootstrapDict.iteritems():
			if k in dictionary:
				raise ConflictingTemplateVars(
					"Key %r is already in dictionary: %r.  "
					"Don't use this key name because %s uses it." % (
						k, dictionary, self.__class__.__name__))
			dictionary[k] = v

		rendered = template.render(dictionary)
		return rendered.encode('utf-8')


def optParameterHttpServer(longName, shortName):
	"""
	Returns a list that you can use in your L{usage.Options}'s
	C{optParameters} list.
	"""
	return [longName, shortName, None,
		"strports description for the HTTP server. "
		"Example: 'tcp:80:interface=127.0.0.1'. "
		"Repeat this option for multiple servers."]


def optParameterMinervaSocket(longName, shortName):
	"""
	Returns a list that you can use in your L{usage.Options}'s
	C{optParameters} list.
	"""
	return [longName, shortName, None,
		"strports description for Minerva server's socket listener. "
		"Example: 'ssl:444:privateKey=privateAndPublic.pem:interface=0'. "
		"Repeat this option for multiple servers."]


def optParameterDomain(longName, shortName):
	"""
	Returns a list that you can use in your L{usage.Options}'s
	C{optParameters} list.
	"""
	# Automatically setting document.document based on a GET
	# parameter or by looking at parent's URL is insecure (because
	# some browsers will allow setting document.domain to 'com',
	# for example.)  We require that the document.domain be
	# manually specified.
	return [longName, shortName, None, "The domain to set document.domain " +
		"values to.  Do not include the port number.  If this option is " +
		"not specified, Minerva over HTTP might work simultaneously " +
		"in just one or two tabs."]


def strportsInfo():
	"""
	Returns a string that you can use in your L{usage.Options}'s
	C{longdesc}.
	"""
	return """\n\nFor strports examples, see
http://twistedmatrix.com/documents/9.0.0/api/twisted.application.strports.html
or the source code for twisted.application.strports."""


def maybeWarnAboutDomain(reactor, domain):
	"""
	If C{domain} is falsy, log a warning.  This is useful in C{makeService}
	functions in tap files.
	"""
	if not domain:
		reactor.callWhenRunning(log.msg,
			"Warning: \n" + "\n".join(textwrap.wrap(
				"--domain not specified.  Browser clients will "
				"connect only to the default hostname; they will not "
				"use subdomains to bypass per-hostname connection "
				"limits.  Minerva over HTTP might work simultaneously "
				"in just one or two tabs.  Additional connections may "
				"stall erratically.", 70)) + "\n")


def maybeWarnAboutClosureLibrary(reactor, closureLibrary):
	"""
	If C{closureLibrary} does not contain closure-library.  This is useful in
	C{makeService} functions in tap files.
	"""
	if not closureLibrary.isdir() or \
	not closureLibrary.child('closure').child('goog').child('base.js').isfile():
		reactor.callWhenRunning(log.msg,
			"Warning: \n" + "\n".join(textwrap.wrap(
				"Could not find Closure Library: %r is not a directory "
				"or is missing closure/goog/base.js.  Many pages on "
				"minerva_site will be broken.  Fix this by "
				"downloading Closure Library and specifying a "
				"path with --closure-library="
				"..." % (closureLibrary,), 70)) + "\n")


def enablePyquitter(reactor, interval=2.5):
	"""
	Hackish Pyquitter integration.  This is useful in C{makeService}
	functions in tap files.

	@return: (the ChangeDetector, the LoopingCall)
	"""
	print 'Enabling reloader.'
	from twisted.internet import task
	from pyquitter import detector

	cd = detector.ChangeDetector(
		lambda: reactor.callWhenRunning(reactor.stop),
		logCallable=log.msg)

	looping = task.LoopingCall(cd.poll)
	looping.start(interval, now=True)

	return cd, looping


try: from refbinder.api import bindRecursive
except ImportError: pass
else: bindRecursive(sys.modules[__name__], _postImportVars)
