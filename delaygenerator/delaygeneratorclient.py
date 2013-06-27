from twisted.internet.defer import inlineCallbacks
from ab.abbase import getFloat

class DelayGeneratorClient:
    def __init__(self,protocol):        
        self.protocol = protocol

    def getDelays(self):
        return self.protocol.sendCommand('get-delays')
        
    def setDelay(self,dgName,delay):
        return self.protocol.sendCommand('set-delay',dgName,delay)

    def setDelayListener(self,listener):
        self.protocol.messageSubscribe('delay-changed',listener)

    def removePositionListener(self,listener = None):
        self.protocol.messageUnsubscribe('delay-changed',listener)

@inlineCallbacks
def main():
    from ab.abclient import getProtocol    
    from ab.abbase import selectFromList
    from config.delaygenerator import DG_CONFIG
    import config.delaygenerator as dgKeys

    serverOptions = DG_CONFIG[dgKeys.GLOBAL]
    serverURL = serverOptions["url"]
    protocol = yield getProtocol(serverURL)
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
