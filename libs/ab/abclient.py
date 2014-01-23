from twisted.internet.defer import Deferred
from autobahn.wamp import WampClientFactory, WampClientProtocol
from autobahn.websocket import connectWS 
from abbase import uriFromCommand, uriFromMessage
        
class BaseClientProtocol(WampClientProtocol):
    """
    base class for client connections
    """
    def sendCommand(self,command,*args):
        """
        send command of type I{command} with args        
        """
        return self.call(uriFromCommand(command), *args)
    def messageSubscribe(self,message,handler):
        """
        @param message: message type to subscribe to
        @type message: string

        @param handler: callable f(*args) to which message
            payload is delivered
        """
        message = uriFromMessage(message)
        if message not in self._messages:
            d = self.subscribe(message,self._onMessage)
        else:
            d = None
        self._messages.setdefault(message,[]).append(handler)
        return d
        
    def messageUnsubscribe(self,message,handler=None):
        message = uriFromMessage(message)
        handlers = self._messages[message]
        if handler:
            handlers.remove(handler)
        if not (handler and handlers):
            del self._messages[message]
            return self.unsubscribe(message)
    def onSessionOpen(self):
        self._messages = {}
        if hasattr(self.factory,'_get_prot'):
            self.factory._get_prot.callback(self)
    def _onMessage(self,message,data):
        handlers = self._messages[message]
        for handler in handlers:
            handler(data)
class BaseClientFactory(WampClientFactory):
    protocol = BaseClientProtocol
    def getProtocol(self):
        d = self._get_prot = Deferred()
        connectWS(self)
        return d 
    def connectionFailed(self):
        self._get_prot.errback(Exception('connection failed'))
        return WampClientFactory.connectionFailed(self)
def getProtocol(url):
    """
    get a client connection to the specified server

    @param url: server IP address
    @type url: string

    @returns: Deferred instance that, upon
        success, returns client connection instance
    """
    return BaseClientFactory(url).getProtocol()
    

