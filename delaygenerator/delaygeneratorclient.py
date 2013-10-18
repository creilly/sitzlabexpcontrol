from twisted.internet.defer import inlineCallbacks

from sitz import DELAY_GENERATOR_SERVER, DEBUG_DELAY_GENERATOR_SERVER

from sitz import printDict

import sys
DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'
print 'debug: %s' % DEBUG

#instantiate this class to have access to methods that make calls to the server
#this is how you make all interactions with the server
class DelayGeneratorClient:
    def __init__(self,protocol):        
        self.protocol = protocol

    def getDelays(self):
        return self.protocol.sendCommand('get-delays')
        
    def setDelay(self,dgName,delay):
        return self.protocol.sendCommand('set-delay',dgName,delay)

    def setDelayListener(self,listener):
        self.protocol.messageSubscribe('delay-changed',listener)

    def removeDelayListener(self,listener = None):
        self.protocol.messageUnsubscribe('delay-changed',listener)
        
@inlineCallbacks
def main():
    from ab.abclient import getProtocol    
    from ab.abbase import selectFromList, getFloat

    protocol = yield getProtocol(
        DELAY_GENERATOR_SERVER
        if not DEBUG else
        DEBUG_DELAY_GENERATOR_SERVER
    )

    client = DelayGeneratorClient(protocol)
    
    delay = yield client.getDelays()
    dgNameList = delay.keys()
    dgNameList.append('Done')
    
    while True:
        delay = yield client.getDelays()
        print 'current settings:'
        for key,val in delay.items():
            print '\t %s: %s' % (key,val)
        
        dgToMod = yield selectFromList(dgNameList,"Which delay generator to adjust?")
        if dgToMod == "Done": break
        delayVal = yield getFloat(prompt="Enter a new delay (in ns):")
        client.setDelay(dgToMod,delayVal)

    print 'shutting down'
    reactor.stop()

if __name__ == '__main__':
    from twisted.internet import reactor
    main()
    reactor.run()
