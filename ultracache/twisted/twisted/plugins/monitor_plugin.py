from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

import monitor


class Options(usage.Options):
    optParameters = [
        ["config", "c", "config.yaml", "Optional config file"],
    ]


class MonitorServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "monitor"
    description = "Monitor RabbitMQ fanout exchange called echidna"
    options = Options

    def makeService(self, options):
        return monitor.makeService()


serviceMaker = MonitorServiceMaker()
