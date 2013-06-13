from twisted.internet.defer import Deferred
from autobahn.wamp import WampClientFactory, WampClientProtocol
from autobahn.websocket import connectWS 
from abbase import uriFromCommand, uriFromMessage
        
class BaseClientProtocol(WampClientProtocol):
    def sendCommand(self,command,*args):
        return self.call(uriFromCommand(command), *args)
    def messageSubscribe(self,message,handler):
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
    return BaseClientFactory(url).getProtocol()
    

