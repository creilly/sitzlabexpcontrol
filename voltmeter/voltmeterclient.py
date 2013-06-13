from abclient import BaseClientFactory, BaseClientProtocol, getProtocol
from consoleclient import ConsoleClient, runConsoleClient, consoleCommand
from abbase import log, getDigit
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from twisted.internet import reactor
from sitz import VOLTMETER_SERVER
from time import clock

class VoltMeterClient(ConsoleClient):
        
    @consoleCommand('start','start the voltmeter')
    def startVM(self):
        return self.protocol.sendCommand('start')
    @consoleCommand('stop','stop the voltmeter')
    def stopVM(self):
        return self.protocol.sendCommand('stop')

    @consoleCommand('get voltages','gets the most recently acquired voltages')
    def getVoltages(self):
        return self.protocol.sendCommand('get-voltages')

    @inlineCallbacks
    def initializeConsoleClient(self):
        self.protocol = yield getProtocol(VOLTMETER_SERVER)
        yield self.protocol.messageSubscribe('voltages-measured',self.onVoltagesMeasured)

    def onVoltagesMeasured(self,voltages):
        print clock()

if __name__ == '__main__':
    runConsoleClient(VoltMeterClient)    
    reactor.run()
