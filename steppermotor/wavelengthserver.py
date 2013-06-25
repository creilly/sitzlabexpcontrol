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

DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'

PDL = '2'

class WavelengthWAMP(BaseWAMP):

    __wampname__ = 'wavelength server'

    STEP = 0    
    WAVELENGTH = 1
    
    WAVELENGTHS_PER_STEP = 1.0 / 42.0

    CALIBRATION_CHANGED = 'calibration-changed'

    MESSAGES = {
        CALIBRATION_CHANGED: 'notifies when calibration is changed'
    }
    @inlineCallbacks
    def initializeWAMP(self):
        protocol = yield getProtocol(
            TEST_STEPPER_MOTOR_SERVER
            if DEBUG else
            STEPPER_MOTOR_SERVER
        )
        stepperMotor = StepperMotorClient(protocol,PDL)
        wavelength = yield getType(float,'enter surf wavelength: ')
        step = self.step = yield stepperMotor.getPosition()
        self.offsets = {
            self.WAVELENGTH: wavelength,
            self.STEP: step
        }
        yield stepperMotor.addListener(stepperMotor.POSITION,partial(setattr,self,'step'))
        ## complete initialization
        BaseWAMP.initializeWAMP(self)

    @command('get-wavelength','get SURF position corresponding to specified step')
    def getWavelength(self,step):
        return self.WAVELENGTHS_PER_STEP * (step - self.offsets[self.STEP]) + self.offsets[self.WAVELENGTH]

    @command('set-wavelength','recalibrate SURF wavelength')
    def setWavelength(self,wavelength):
        self.offsets[self.STEP] = self.step
        self.offsets[self.wavelength] = wavelength
        self.dispatch(self.CALIBRATION_CHANGED)

def main():
    runServer(WAMP = WavelengthWAMP, URL = WAVELENGTH_SERVER, debug = DEBUG)
if __name__ == '__main__':
    main()
    reactor.run()