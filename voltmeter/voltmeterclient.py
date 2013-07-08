from twisted.internet.defer import inlineCallbacks, Deferred

#look for user using 'debug' option on runtime
import sys
DEBUG = len(sys.argv) > 1


class VoltMeterClient:
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


def getList(url):
    from ab.abclient import getProtocol    
    d = Deferred()
    protocol = yield getProtocol(url)
    client = VoltMeterClient(protocol)
    vmNameList = client.getChannels()
    d.addCallback(vmNameList)
    ReturnValue(d)
    
def log(gen):
    print 'these voltmeters are running:'
    for x in gen: print '\t'+str(x)
    
        
        
@inlineCallbacks
def main():
    from ab.abclient import getProtocol    
    from config.voltmeter import VM_SERVER_CONFIG, VM_DEBUG_SERVER_CONFIG
   
    serverURL = VM_SERVER_CONFIG['url'] if not DEBUG else VM_DEBUG_SERVER_CONFIG['url']
    print 'connecting to: ' +str(serverURL)
    '''
    protocol = yield getProtocol(serverURL)
    client = VoltMeterClient(protocol)
    
    vmNameList = yield client.getChannels()
    '''
    obj = getList(serverURL)
    obj.addCallback(log)
    
    '''
    print 'these voltmeters are running:'
    for vm in vmNameList: print '\t'+str(vm)
    '''
    reactor.stop()

if __name__ == '__main__':
    from twisted.internet import reactor
    main()
    reactor.run()
