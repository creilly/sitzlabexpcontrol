from ab.abserver import BaseWAMP, command, runServer
from ab.abclient import getProtocol
from ab.abbase import getType
from twisted.internet.defer  import Deferred, inlineCallbacks, returnValue
from twisted.internet  import reactor
from sitz import WAVELENGTH_SERVER, STEPPER_MOTOR_SERVER, TEST_STEPPER_MOTOR_SERVER 
from functools import partial
from steppermotorclient import StepperMotorClient, ChunkedStepperMotorClient
from tracking.crystalcalibrator import KDPCrystalCalibrator, BBOCrystalCalibrator
import sys
from config.steppermotor import PDL, KDP, BBO

DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'

STEPPER_MOTOR_KEYS = (PDL,KDP,BBO)

class WavelengthWAMP(BaseWAMP):

    __wampname__ = 'wavelength server'

    STEP = 0
    WAVELENGTH = 1
    
    WAVELENGTHS_PER_STEP = 1.0 / 42.0
    
    MESSAGES = {
        'calibration-changed':'laser (SURF) calibration has changed',
        'tracking-changed':'tracking state was toggled'
    }

    @inlineCallbacks
    def initializeWAMP(self):        
        self.tracking = False
        protocol = yield getProtocol(
            TEST_STEPPER_MOTOR_SERVER
            if DEBUG else
            STEPPER_MOTOR_SERVER
        )
        stepperMotors = self.stepperMotors = {
            id:ChunkedStepperMotorClient(protocol,id)
            for id in
            STEPPER_MOTOR_KEYS
        }
        calibrators = self.calibrators = {
            id:Calibrator() for id, Calibrator in (
                (KDP,KDPCrystalCalibrator),
                (BBO,BBOCrystalCalibrator)
            )
        }        
        self.offsets = {}        
        BaseWAMP.initializeWAMP(self)
        wavelength = 24210.5 #yield getType(float,'enter surf wavelength: ')
        yield self.calibrateWavelength(wavelength)        

    @command('calibrate-wavelength','recalibrate SURF wavelength')
    @inlineCallbacks
    def calibrateWavelength(self,wavelength):
        step = yield self.stepperMotors[PDL].getPosition()
        self.offsets[self.STEP] = step
        self.offsets[self.WAVELENGTH] = wavelength
        self.dispatch('calibration-changed',self.isTracking())

    @command('calibrate-crystal','set tuned position for crystal')
    @inlineCallbacks
    def calibrateCrystal(self,id):
        pdlPosition = yield self.stepperMotors[PDL].getPosition()
        crystalPosition = yield self.stepperMotors[id].getPosition()
        self.calibrators[id].calibrateCrystal((pdlPosition,crystalPosition))

    @command('get-wavelength','get calibrated SURF wavelength')
    def _getWavelength(self):
        return self.stepperMotors[PDL].getPosition().addCallback(self.getWavelength)

    def getWavelength(self,step):
        return self.WAVELENGTHS_PER_STEP * (step - self.offsets[self.STEP]) + self.offsets[self.WAVELENGTH]

    def getStep(self,wavelength):
        return int(
            round(
                (wavelength - self.offsets[self.WAVELENGTH]) / self.WAVELENGTHS_PER_STEP + self.offsets[self.STEP]
            )
        )

    @command('set-wavelength','set wavelength and track crystals if tracking')
    @inlineCallbacks
    def setWavelength(self,wavelength):
        # find desired PDL step
        step = self.getStep(wavelength)
        # at least set pdl to desired wavelength
        positions = {
            PDL:step
        }
        # if tracking, calculate crystal positions too
        if self.tracking:
            positions.update(
                {
                    id:calibrator.getPosition(step)
                    for id,calibrator in
                    self.calibrators.items()
                }
            )
        # set the positions all at once, and wait for them to finish
        for d in [
            self.stepperMotors[id].setPosition(position)
            for id, position in
            positions.items()
        ]:
            yield d

    @command('cancel-wavelength-set','abort most recent wavelength set call')
    def cancelWavelengthCall(self):
        for stepperMotor in self.stepperMotors.values():
            stepperMotor.cancel()

    @command('toggle-tracking','toggle tracking mode')
    @inlineCallbacks
    def toggleTracking(self):
        self.tracking = not self.tracking
        self.dispatch('tracking-changed',self.tracking)
        if self.tracking:
            wavelength = yield self._getWavelength()
            self.setWavelength(wavelength)
            
    @command('is-tracking')
    def isTracking(self):
        return self.tracking
        
def main():
    runServer(WAMP = WavelengthWAMP, URL = WAVELENGTH_SERVER, debug = DEBUG)
if __name__ == '__main__':
    main()
    reactor.run()