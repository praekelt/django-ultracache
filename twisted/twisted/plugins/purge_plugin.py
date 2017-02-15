from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

import purge


class Options(usage.Options):
    optParameters = [
        ["config", "c", "", "Optional config file"],
    ]


class PurgeServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "purge"
    description = """Subscribe to RabbitMQ fanout exchange called purgatory \
and send purge instruction to a reverse caching proxy."""
    options = Options

    def makeService(self, options):
        return purge.makeService(options)


serviceMaker = PurgeServiceMaker()
