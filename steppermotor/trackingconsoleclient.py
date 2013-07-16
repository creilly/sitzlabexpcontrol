from ab.abclient import getProtocol
from ab.consoleclient import ConsoleClient, runConsoleClient, consoleCommand
from ab.abbase import getType
from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor
import sys
from sitz import WAVELENGTH_SERVER

class TrackingConsoleClient(ConsoleClient):
    __ccname__ = 'tracking client'    
    def __init__(self,protocol):
        self.protocol = protocol
        ConsoleClient.__init__(self)
    @consoleCommand('calibrate wavelength','correct the calibration of surf wavelength')
    @inlineCallbacks
    def calibrateWavelength(self):
        wavelength = yield getType(float,'enter current surf dial reading: ')
        yield self.protocol.sendCommand('calibrate-wavelength',wavelength)

@inlineCallbacks
def main():
    protocol = yield getProtocol(WAVELENGTH_SERVER)
    runConsoleClient(TrackingConsoleClient,protocol)

if __name__ == '__main__':
    main()
    reactor.run()
