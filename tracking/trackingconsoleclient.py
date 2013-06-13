from abclient import getProtocol
from consoleclient import ConsoleClient, runConsoleClient, consoleCommand
from abbase import log, getType, sleep
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import reactor
from steppermotorserver import getConfig
from steppermotorclient import StepperMotorClient

class TrackingConsoleClient(StepperMotorClient):
    
    __ccname__ = 'crystal tracking client'

    TRACK_PERIOD = .3
    SLEEP = .5 # once tracking, wait .5 seconds between calls

    @inlineCallbacks
    def initializeConsoleClient(self):
        yield StepperMotorClient.initializeConsoleClient(self)
        self.tracking = False
        yield self.calibrateWavelength()

    @consoleCommand('calibrate dye laser','calibrate tracker with SURF wavelength')
    def calibrateWavelength(self):
        return getType(
            float,
            'enter SURF wavelength (something around 24000.0): '
        ).addCallback(
            self.client.calibrateWavelength
        )
        
    @consoleCommand('calibrate crystal','indicate current position as tuned')
    @inlineCallbacks
    def calibrateCyrstal(self):
        alpha_tilde = yield self.client.getWavelength()
        delta_tilde = yield self.client.getPosition()
        self.client.calibrator.calibrateCrystal((alpha_tilde,delta_tilde))

    @consoleCommand('get wavelength','get pdl position')
    def _getWavelength(self):
        return self.client.getWavelength()

    @consoleCommand('start tracking')
    def startTracking(self):
        self.loop()

    @inlineCallbacks
    def loop(self):
        while self.tracking:
            yield self.client.track()

    @consoleCommand('stop tracking')
    def stopTracking(self):
        self.tracking = False

@inlineCallbacks
def main():
    from abbase import getListIndex
    from trackingclient import TrackingClient
    crystalKeys, crystalNames = zip(
        *{
            TrackingClient.KDP:'KDP',
            TrackingClient.BBO:'BBO'
        }.items()
    )
    crystalIndex = yield getLisIndex(crystalNames, 'select a crystal to track')
    crystalKey = crystalKeys[crystalIndex]
    TrackingConsoleClient.__ccname__ = '(%s) tracking client' % crystalNames[crystalIndex]
    tc = TrackingClient(crystalKey)
    yield tc.initTrackingClient() # need to init() this object before using
    runConsoleClient(
        TrackingConsoleClient,
        tc
    )
if __name__ == '__main__':
    main()
    reactor.run()

