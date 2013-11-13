#instantiate this class to have access to methods that make calls to the server
#this is how you make all interactions with the server
class DelayGeneratorClient:
    def __init__(self,protocol):        
        self.protocol = protocol

    def getDelays(self):
        return self.protocol.sendCommand('get-delays')

    def setDelay(self,dgName,delay):
        return self.protocol.sendCommand('set-delay',dgName,delay)

    def setPartnerDelay(self,dgName,delay):
        return self.protocol.sendCommand('set-partnered-delay',dgName,delay)
        
    def setDelayListener(self,listener):
        self.protocol.messageSubscribe('delay-changed',listener)

    def removeDelayListener(self,listener = None):
        self.protocol.messageUnsubscribe('delay-changed',listener)
        
from twisted.internet.defer import inlineCallbacks        
@inlineCallbacks
def main():
    from ab.abclient import getProtocol    
    from ab.abbase import selectFromList, getFloat
    from sitz import DELAY_GENERATOR_SERVER, TEST_DELAY_GENERATOR_SERVER
    from sitz import printDict
    import sys
    DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'

    protocol = yield getProtocol(
        DELAY_GENERATOR_SERVER
        if not DEBUG else
        DEBUG_DELAY_GENERATOR_SERVER
    )

    client = DelayGeneratorClient(protocol)
    
    delay = yield client.getDelays()
    dgNameList = delay.keys()
    activeDGs = {}
    for dg in dgNameList:
        if DEBUG: 
            activeDGs[dg] = DEBUG_DG_CONFIG[dg]
        else:
            activeDGs[dg] = DG_CONFIG[dg]
    dgNameList.insert(0,'Refresh')
    dgNameList.append('Done')
    
    while True:
        delay = yield client.getDelays()
        print 'current settings:'
        for key,val in delay.items():
            print '\t %s: %s' % (key,val)
        
        dgToMod = yield selectFromList(dgNameList,"Which delay generator to adjust?")
        if dgToMod == "Refresh": continue
        if dgToMod == "Done": break
        delayVal = yield getFloat(prompt="Enter a new delay (in ns):")
        if activeDGs[dgToMod]['partner'] is not None:
            print 'this delay has a partner. the partner will automatically adjust unless you override.'
            override = raw_input("override? (y/n)")
            if override == 'Y' or override == 'y': client.setDelay(dgToMod,delayVal)
            else:
                print 'setting partnered delay'
                client.setPartnerDelay(dgToMod,delayVal)

    print 'shutting down'
    reactor.stop()

if __name__ == '__main__':
    from twisted.internet import reactor
    main()
    reactor.run()
