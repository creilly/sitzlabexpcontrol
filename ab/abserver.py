from twisted.internet import reactor
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.python import log

from autobahn.websocket import listenWS
from autobahn.wamp import exportRpc, \
    WampServerFactory, \
    WampServerProtocol

from functools import partial

from sitz import tagger, SITZ_RPC_URI

from abbase import uriFromMessage
from abclient import getProtocol
from sitz import INSPECTOR_SERVER

PROPERTIES = 'PROPERTIES'

_command, wampmetaclass = tagger('commands')
def command(name,description='no description'):
    def foo(bar):
        return exportRpc(name)(_command(name,description)(bar))
    return foo
    
class BaseWAMP(object):
    __metaclass__ = wampmetaclass
    __wampname__ = 'wamp server'
    
    MESSAGES = {
        'test':'message for testing'
    }
    
    def __init__(self,factory,*args,**kwargs):
        self.factory = factory
        self.onReady = Deferred()
        self.initializeWAMP(*args,**kwargs)
       
    @command('commands','query server for available rpc calls')
    def getCommands(self):
        return {
            command[tagger.NAME]: command[tagger.DESCRIPTION] for command in self.commands
        }

    @command('messages','query server for available messages')
    def getMessages(self):
        return self.MESSAGES

    def initializeWAMP(self):
        self.onReady.callback(None)
        
    def dispatch(self,name,*data):
        self.factory.dispatch(uriFromMessage(name),*data)
 
class BaseServerProtocol(WampServerProtocol):
    def onSessionOpen(self):
        self.registerForRpc(self.factory.wamp, SITZ_RPC_URI)
        for message in self.factory.wamp.MESSAGES.keys():
            self.registerForPubSub(uriFromMessage(message))

class BaseServerFactory(WampServerFactory): pass

@inlineCallbacks
def runServer(
        WAMP,
        URL,
        Protocol = BaseServerProtocol,
        Factory = BaseServerFactory,
        debug = False,
        outputToConsole = False,
        args = [],
        kwargs = {}
):
    import sys
    import os
    os.system('title %s' % WAMP.__wampname__)
    Factory.protocol = Protocol
    factory = Factory(URL, debugWamp = debug)
    wamp = factory.wamp = WAMP(factory,*args,**kwargs)
    yield wamp.onReady
    log.startLogging(
        sys.stdout if outputToConsole else open('serverlogs/' + WAMP.__name__ + '.log','a')
    )
    listenWS(factory)
    # try:
    #     inspector = yield getProtocol(INSPECTOR_SERVER)
    #     inspector.sendCommand('register',URL,WAMP.__wampname__)
    #     def stopFactory(hook):
    #         inspector.sendCommand('unregister',URL)
    #         print 'sent unregister command'
    #         hook()
    #     inspector.factory.stopFactory = partial(stopFactory,inspector.factory.stopFactory)
    #     factory.stopFactory = partial(stopFactory,factory.stopFactory)
    # except Exception, e:
    #     print 'not registered with inspector server (%s)' % e.message
if __name__ == '__main__':
    runServer(BaseWAMP)
    reactor.run()
