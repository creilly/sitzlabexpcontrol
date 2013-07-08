from ab.abclient import BaseClientFactory, BaseClientProtocol, getProtocol
from ab.consoleclient import ConsoleClient, runConsoleClient, consoleCommand
from ab.abbase import log, getDigit
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from twisted.internet import reactor
from config.voltmeter import VM_SERVER_CONFIG, VM_DEBUG_SERVER_CONFIG
from time import clock

#look for the user to pass 'debug' at runtime
import sys
DEBUG = len(sys.argv) > 1


class VoltMeterClient(ConsoleClient):
    '''    
    @consoleCommand('start','start the voltmeter')
    def startVM(self):
        return self.protocol.sendCommand('start')
    
    @consoleCommand('stop','stop the voltmeter')
    def stopVM(self):
        return self.protocol.sendCommand('stop')
    '''
        
    @consoleCommand('get voltages','gets the most recently acquired voltages')
    def getVoltages(self):
        return self.protocol.sendCommand('get-voltages')

    @inlineCallbacks
    def initializeConsoleClient(self):
        url = VM_SERVER_CONFIG['url'] if not DEBUG else VM_DEBUG_SERVER_CONFIG['url']
        self.protocol = yield getProtocol(url)
        yield self.protocol.messageSubscribe('voltages-measured',self.onVoltagesMeasured)

    def onVoltagesMeasured(self,voltages):
        print clock()

if __name__ == '__main__':
    runConsoleClient(VoltMeterClient)    
    reactor.run()
