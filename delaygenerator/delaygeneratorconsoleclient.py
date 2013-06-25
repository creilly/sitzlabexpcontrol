from ab.abclient import getProtocol
from ab.consoleclient import ConsoleClient, runConsoleClient, consoleCommand
from ab.abbase import log, getType, selectFromList
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from twisted.internet import reactor
from delaygeneratorserver import getConfig
from delaygeneratorclient import DelayGeneratorClient

class DelayGeneratorConsoleClient(ConsoleClient):
    __ccname__ = 'delay generator client'    
    def __init__(self,client):
        self.client = client
        ConsoleClient.__init__(self)
    
    @consoleCommand('get delay','query the delays on all delay generators')
    def getDelay(self):
        return self.client.getDelays()

    @consoleCommand('set delay','sets the delay on requested delay generator')
    @inlineCallbacks
    def setDelay(self):
        dgDict = yield self.getDelay()
        dgName = yield selectFromList(dgDict.keys(),'which delay to change?')
        delay = yield getType(float,'input delay: ')
        yield self.client.setDelay(dgName,delay)



@inlineCallbacks
def main():
    serverOptions, dgOptions = getConfig()
    url = serverOptions["url"]
    
    DelayGeneratorConsoleClient.__ccname__ = 'delay generator client'
    protocol = yield getProtocol(url)
    dgc = DelayGeneratorClient(protocol)
    runConsoleClient(
        DelayGeneratorConsoleClient,
        dgc
    )
if __name__ == '__main__':
    main()
    reactor.run()
