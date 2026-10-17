from twisted.python.filepath import FilePath
from twisted.web import static

from minerva.mutils import htmldumps

from webmagic.untwist import BetterResource


class Index(BetterResource):
	isLeaf = True

	def __init__(self, mainSocketPort):
		import jinja2

		BetterResource.__init__(self)

		self._mainSocketPort = mainSocketPort
		self._jinja2Env = jinja2.Environment()
		self._basePath = FilePath(__file__).parent() # this is minerva/dumbtest/
		
		self._fileName = 'dumbtest.html'


	def render_GET(self, request):

		# This jinja2 stuff is for the html page, not the JavaScript
		template = self._basePath.child(self._fileName).getContent().decode('utf-8')
		dictionary = dict(htmldumps=htmldumps, mainSocketPort=self._mainSocketPort)
		rendered = self._jinja2Env.from_string(template).render(dictionary)
		return rendered.encode('utf-8')



class DumbTestPage(BetterResource):

	def __init__(self, mainSocketPort):
		BetterResource.__init__(self)

		self.putChild('', Index(mainSocketPort))
		self.putChild('app.swf', static.File(FilePath(__file__).sibling('app.swf').path))
