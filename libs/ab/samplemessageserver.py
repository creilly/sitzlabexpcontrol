from abserver import BaseWAMP, command, runServer

from browserclient import BrowserClient

from twisted.internet.defer  import Deferred, inlineCallbacks
from twisted.internet  import reactor
from twisted.internet.task import LoopingCall

from sitz import MESSAGE_SERVER

class MessageWAMP(BaseWAMP):
    MESSAGES = {
        'counter-updated':'dispatched when count updates'
    }
    INTERVAL = .1
    
    def initializeWAMP(self):
        self.count = 0
        self.messageTimer = LoopingCall(self.onMessageTimer)
        BaseWAMP.initializeWAMP(self)

    def onMessageTimer(self):
        self.dispatch('counter-updated',self.count)
        self.count += 1

    @command('start-timer','starts message timer')
    def startTimer(self):
        self.messageTimer.start(self.INTERVAL)

    @command('stop-timer','stops timer')
    def stopTimer(self):
        self.messageTimer.stop()

if __name__ == '__main__':
    runServer(MessageWAMP, URL = MESSAGE_SERVER, debug = True, outputToConsole = True)
    reactor.run()
