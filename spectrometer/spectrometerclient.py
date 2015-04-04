from twisted.internet.defer import inlineCallbacks, returnValue
from scan import Scan
from scan.input import IntervalScanInput
from functools import partial
from sitz import compose
import sys

DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'

class SpectrometerClient:
    def __init__(self,protocol):        
        self.protocol = protocol
    
    def getWavelengths(self):
        return self.protocol.sendCommand('get-wavelengths')
        
    def getLastTime(self):
        return self.protocol.sendCommand('get-last-time')
            
    def getSpectrum(self):
        return self.protocol.sendCommand('get-latest-spectrum')
    
    def setIntegrationTime(self,newTime):
        return self.protocol.sendCommand('set-integration-time',newTime)
        
    
@inlineCallbacks
def main():
    from config.serverURLs import SPECTROMETER_SERVER, TEST_SPECTROMETER_SERVER
    from ab.abclient import getProtocol
    from twisted.internet.defer import Deferred
    
    ## connect to server
    ipAddress = TEST_SPECTROMETER_SERVER if DEBUG else SPECTROMETER_SERVER
    protocol = yield getProtocol(ipAddress)
    
    ## create a client
    client = SpectrometerClient(protocol)
    
    @inlineCallbacks
    def displayNew():
        payload = yield client.getSpectrum()
        print len(payload)

    @inlineCallbacks
    def getRange():
        range = yield client.getWavelengths()
        print len(range)
    
    @inlineCallbacks
    def getTime():
        time = yield client.getLastTime()
        print time
    
    ## get spectrum
    yield displayNew()

    yield getRange()
    
    yield getTime()
    
    
    ## quit
    reactor.stop()
 
if __name__ == '__main__':
    from twisted.internet import reactor
    main()
    reactor.run()
