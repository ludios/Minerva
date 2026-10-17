from twisted.python.filepath import FilePath

from webmagic.untwist import BetterResource
from minerva.mutils import MinervaBootstrap


class ChatAppPage(BetterResource):

	def __init__(self, fileCache, domain, mainSocketPort):
		BetterResource.__init__(self)

		templateFile = FilePath(__file__).sibling('chatapp.html')
		self.putChild('', MinervaBootstrap(fileCache, templateFile,
			dict(domain=domain, dev_mode=True, mainSocketPort=mainSocketPort)))
