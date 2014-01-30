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

PROPERTIES = 'PROPERTIES'

_command, wampmetaclass = tagger('commands')
def command(name,description='no description'):
    """
    decorator to expose decorated function as
    server command

    @param name: command identifier
    @param str: string    
    """
    def foo(bar):
        return exportRpc(name)(_command(name,description)(bar))
    return foo
    
class BaseWAMP(object):
    """
    base class for WAMP classes
    """
    __metaclass__ = wampmetaclass
    __wampname__ = 'wamp server'
    
    MESSAGES = {
        'test':'message for testing'
    }
    
    def __init__(self,factory,*args,**kwargs):
        """
        args and kwargs are passed to intializeWAMP()
        @type factory: BaseServerFactory
        """
        self.factory = factory
        self.onReady = Deferred()
        self.initializeWAMP(*args,**kwargs)
       
    @command('commands','query server for available rpc calls')
    def getCommands(self):
        """
        get list of availabled commands
        """
        return {
            command[tagger.NAME]: command[tagger.DESCRIPTION] for command in self.commands
        }

    @command('messages','query server for available message types')    
    def getMessages(self):
        """
        get list of available message types
        """
        return self.MESSAGES

    def initializeWAMP(self):
        """
        override this function to perform any setup,
        making sure to call this function afterwards
        """
        self.onReady.callback(None)
        
    def dispatch(self,name,*data):
        """
        send message to those subscribed

        @param name: message type
        @type name: string

        @param data: message payload
        """
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
    """
    start up a WAMP server

    @type WAMP: BaseWAMP

    @param URL: IP addres to host from
    @type URL: string

    @param debug: if True, prints all messages,
        including WAMP transmissions, to console.
        if False WAMP transmission aren't logged    
    @type debug: boolean
    """
    import sys
    import os
    os.system('title %s' % WAMP.__wampname__)
    Factory.protocol = Protocol
    factory = Factory(URL, debugWamp = debug)
    wamp = factory.wamp = WAMP(factory,*args,**kwargs)
    yield wamp.onReady
    log.startLogging(
        sys.stdout if outputToConsole or debug else open('serverlogs/' + WAMP.__name__ + '.log','a')
    )
    listenWS(factory)

if __name__ == '__main__':
    runServer(BaseWAMP)
    reactor.run()
