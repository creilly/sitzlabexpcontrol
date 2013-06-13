from steppermotorclient import StepperMotorClient, PDLClient
from crystalcalibrator import KDPCrystalCalibrator, BBOCrystalCalibrator, TestCrystalCalibrator
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from twisted.internet import reactor
import steppermotorserver
from abclient import getProtocol
from abbase import getUserInput, getType

TRACK_PERIOD = .3
SLEEP = .5 # once tracking, wait SLEEP seconds between calls

# MUST YIELD INIT BEFORE USING
class TrackingClient(StepperMotorClient):
    KDP = 0
    BBO = 1
    TEST = 2
    CONFIG = {
        KDP:(KDPCrystalCalibrator,'KDP','PDL'),
        BBO:(BBOCrystalCalibrator,'BBO','PDL'),
        TEST:(TestCrystalCalibrator,'TestStepperMotor','TestStepperMotor2')
    }
    @classmethod
    @inlineCallbacks
    def getTrackingClient(cls,crystalKey):
        smConfig = steppermotorserver.getConfig()
        Calibrator, crystalConfigKey, wavelengthConfigKey = cls.CONFIG[crystalKey]
        crystalProtocol = yield getProtocol(
            smConfig[crystalConfigKey]['url']
        )
        wavelengthProtocol = yield getProtocol(
            smConfig[wavelengthConfigKey]['url']
        )
        calibrator = Calibrator()        
        returnValue(
            cls(
                crystalProtocol,
                wavelengthProtocol,
                calibrator
            )
        )
    def __init__(self,cp,wp,calibrator):
        StepperMotorClient.__init__(self,cp)
        self.wavelengthClient = PDLClient(wp)
        self.calibrator = calibrator

    @inlineCallbacks
    def track(self):
        wavelength = yield self.wavelengthClient.getPosition()
        desired = self.calibrator.getPosition(wavelength)
        current = yield self.getPosition()
        rate = yield self.getStepRate()
        delta = desired - current        
        max = int( TRACK_PERIOD * rate )
        if abs(delta) > max:
            delta = max if delta > 0 else -1 * max

        if delta is not 0:
            yield self.setPosition(current + delta)
            yield self.track()

    @inlineCallbacks
    def _track(self):
        yield self.track()        
        self.trackingDeferred = d = Deferred()
        clients = (self,self.wavelengthClient)
        for client in clients:
            client.setPositionListener(d.callback)
        def cb(status):
            for client in clients:
                client.removePositionListener(d.callback)
            if status is not None:
                self._track()
        d.addCallback(cb)
        
    def startTracking(self):
        self._track()

    def stopTracking(self):
        self.trackingDeferred.callback(None)
        
    @inlineCallbacks
    def calibrateWavelength(self):
        beta_bar_prime = yield self.wavelengthClient.getWavelength()
        alpha_bar = yield self.wavelengthClient.getPosition()
        self.calibrator.calibrateDye((alpha_bar,beta_bar_prime))

    @inlineCallbacks
    def calibrateCrystal(self):
        alpha_tilde = yield self.wavelengthClient.getPosition()
        delta_tilde = yield self.getPosition()
        self.calibrator.calibrateCrystal((alpha_tilde,delta_tilde))
        
@inlineCallbacks
def main():
    from abserver import runServer
    import subprocess
    stepperMotors = ('TestStepperMotor','TestStepperMotor2')
    client = yield TrackingClient.getTrackingClient(TrackingClient.TEST)
    yield client.calibrateWavelength()
    yield client.calibrateCrystal()
    yield client.startTracking()
    yield getUserInput('press enter to stop tracking and quit: ')
    yield client.stopTracking()
    reactor.stop()
    
if __name__ == '__main__':
    main()
    reactor.run()