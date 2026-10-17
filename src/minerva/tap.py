"""
This is used by the Minerva twistd plugin minerva_site.

This entire file is private; you should not need to import it.  If you need
a similar twistd plugin, copy the code.
"""

from __future__ import with_statement

import os

from twisted.python import usage, log
from twisted.python.filepath import FilePath
from twisted.application import service, strports

from webmagic.filecache import FileCache

from minerva import minerva_site, mutils


_defaultClosureLibrary = FilePath(__file__).parent().parent().sibling("closure-library").path
assert isinstance(_defaultClosureLibrary, str), type(_defaultClosureLibrary)

class Options(usage.Options):
	"""
	Define the options accepted by the I{twistd minerva_site} plugin.
	"""
	synopsis = "[minerva_site options]"

	optParameters = [
		mutils.optParameterHttpServer("http", "t"),
		mutils.optParameterMinervaSocket("minerva", "m"),
		mutils.optParameterDomain("domain", "d"),

		["closure-library", "c", _defaultClosureLibrary,
			'Path to closure-library'],
	]

	optFlags = [
		["no-tracebacks", "n", "Don't display tracebacks on the public interfaces."],
	]

	longdesc = """\
This starts the Minerva test server (minerva_site), from which you can
run the client-side unit tests in a browser, and use some Minerva testing
tools.""" + mutils.strportsInfo()

	def __init__(self):
		usage.Options.__init__(self)
		self['http'] = []
		self['minerva'] = []
	

	def opt_http(self, option):
		self['http'].append(option)


	def opt_minerva(self, option):
		self['minerva'].append(option)


	def postOptions(self):
		usage.Options.postOptions(self)
		if not self['http'] and not self['minerva']:
			raise usage.UsageError("You probably want to start at least 1 http server or 1 minerva server.")



def makeService(config):
	from twisted.internet import reactor, task

	multi = service.MultiService()

	domain = config['domain']
	mutils.maybeWarnAboutDomain(reactor, domain)

	closureLibrary = FilePath(config['closure-library'])
	mutils.maybeWarnAboutClosureLibrary(reactor, closureLibrary)

	socketPorts = []
	for minervaStrport in config['minerva']:
		_, _args, _ = strports.parse(minervaStrport, object())
		socketPorts.append(_args[0])

	doReloading = bool(int(os.environ.get('PYRELOADING', '0')))
	fileCache = FileCache(lambda: reactor.seconds(), 0.1 if doReloading else -1)
	stf, httpSite = minerva_site.makeMinervaAndHttp(
		reactor, fileCache, socketPorts, domain, closureLibrary)
	httpSite.displayTracebacks = not config["no-tracebacks"]

	for httpStrport in config['http']:
		httpServer = strports.service(httpStrport, httpSite)
		httpServer.setServiceParent(multi)

	for minervaStrport in config['minerva']:
		minervaServer = strports.service(minervaStrport, stf)
		minervaServer.setServiceParent(multi)

	if doReloading:
		mutils.enablePyquitter(reactor)

	return multi
