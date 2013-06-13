from abclient import getProtocol
from abbase import log
from consoleclient import ConsoleClient, runConsoleClient, consoleCommand
from sitz import MESSAGE_SERVER
from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor

class MessageClient(ConsoleClient):
    
    @inlineCallbacks
    def initializeConsoleClient(self):
        self.counter = 0
        self.protocol = yield getProtocol(MESSAGE_SERVER)

    @consoleCommand('subscribe')
    def subscribeToMessage(self):
        return self.protocol.messageSubscribe('counter-updated',self.onCounterUpdated)

    @consoleCommand('unsubscribe')
    def unsubscribeFromMessage(self):
        return self.protocol.messageUnsubscribe('counter-updated')

    def onCounterUpdated(self,data):
        self.counter += 1

    @consoleCommand('start','starts message timer')
    def startTimer(self):
        return self.protocol.sendCommand('start-timer')
        
    @consoleCommand('stop','stops message timer')
    def stopTimer(self):
        return self.protocol.sendCommand('stop-timer')

    @consoleCommand('get count','retrieve number of messages received')
    def getCount(self):
        return self.counter

if __name__ == '__main__':
    runConsoleClient(MessageClient)
    reactor.run()
