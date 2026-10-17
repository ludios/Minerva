"""
Minerva is a robust Comet server built on Twisted (with a JavaScript client
built on Closure Library).  It gives web applications a socket-like stream of
strings, over HTTP long-polling, HTTP streaming, or Flash sockets.

See `minerva.tutorial` for small runnable examples, and `minerva.site` for the
development server.
"""

from importlib.metadata import version

# Lazy (PEP 810), so that `import minerva` doesn't import Twisted until you use
# one of these.
lazy from minerva.interfaces import (
    QANProtocol,
    StringFactory,
    StringProtocol,
    TransportCreatedListener,
    TransportDestroyedListener,
)
lazy from minerva.protocols import QANProtocolWrapper, SubprotocolFactory
lazy from minerva.qan import KnownError, QANHelper, QuestionFailed, UnknownError
lazy from minerva.stream import (
    NoSuchStream,
    ServerStream,
    StreamAlreadyExists,
    StreamTracker,
)
lazy from minerva.transport import ServerTransportFactory, TransportInfo
lazy from minerva.web import WebPort

__version__ = version("Minerva")

__all__ = [
    "KnownError",
    "NoSuchStream",
    "QANHelper",
    "QANProtocol",
    "QANProtocolWrapper",
    "QuestionFailed",
    "ServerStream",
    "ServerTransportFactory",
    "StreamAlreadyExists",
    "StreamTracker",
    "StringFactory",
    "StringProtocol",
    "SubprotocolFactory",
    "TransportCreatedListener",
    "TransportDestroyedListener",
    "TransportInfo",
    "UnknownError",
    "WebPort",
    "__version__",
]
