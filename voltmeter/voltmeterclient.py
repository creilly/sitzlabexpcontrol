from twisted.internet.defer import inlineCallbacks, Deferred, returnValue

#look for user using 'debug' option on runtime
import sys
DEBUG = len(sys.argv) > 1


class VoltMeterClient:
    VOLTAGES = 'voltages-acquired'
    def __init__(self,protocol):        
        self.protocol = protocol

    def getVoltages(self):
        return self.protocol.sendCommand('get-voltages')

    def getChannels(self):
        return self.protocol.sendCommand('get-channels')
        
    def getSamplingRate(self):
        return self.protocol.sendCommand('get-sampling-rate')
        
    def setSamplingRate(self,sRate):
        return self.protocol.sendCommand('set-sampling-rate',sRate)
        
    def getCallbackRate(self):
        return self.protocol.sendCommand('get-callback-rate')
        
    def setCallbackRate(self,cbRate):
        return self.protocol.sendCommand('set-callback-rate',cbRate)

    def addListener(self,listener):
        self.protocol.messageSubscribe(self.VOLTAGES,listener)
        
    def removeListener(self,listener=None):
        self.protocol.messageUnsubscribe(self.VOLTAGES,listener)

@inlineCallbacks
def pollVMServer(serverURL):
    from ab.abclient import getProtocol    
    protocol = yield getProtocol(serverURL)
    client = VoltMeterClient(protocol)
    vmNameList = yield client.getChannels()
    returnValue(vmNameList)


#@inlineCallbacks
def main():
    from time import sleep
    from config.voltmeter import VM_SERVER_CONFIG, VM_DEBUG_SERVER_CONFIG
    
    serverURL = VM_SERVER_CONFIG['url'] if not DEBUG else VM_DEBUG_SERVER_CONFIG['url']

    print 'connecting to: ' +str(serverURL)
    print 'these voltmeters are running:'
    vmNameList = pollVMServer(serverURL)
    
    def log(gen):
        for x in gen: print '\t'+str(x)
    vmNameList.addCallback(log)


if __name__ == '__main__':
    from twisted.internet import reactor
    main()
    reactor.run()
