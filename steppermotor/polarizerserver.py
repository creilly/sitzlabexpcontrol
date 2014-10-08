from ab.abserver import BaseWAMP, command, runServer
from ab.abclient import getProtocol
from ab.abbase import getType
from twisted.internet.defer  import Deferred, inlineCallbacks, returnValue
from twisted.internet  import reactor
from config.serverURLs import TEST_POLARIZER_SERVER, POLARIZER_SERVER, STEPPER_MOTOR_SERVER, TEST_STEPPER_MOTOR_SERVER 
from functools import partial
from steppermotorclient import ChunkedStepperMotorClient
import sys
from config.steppermotor import POL

DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'
URL = TEST_POLARIZER_SERVER if DEBUG else POLARIZER_SERVER

class PolarizerWAMP(BaseWAMP):
    __wampname__ = 'polarizer server'
    ANGLE = 0
    DEGREES_PER_STEP = - 68.0 / 10000.0
    MESSAGES = {
        'calibration-changed':'polarization calibration has changed'
    }

    @inlineCallbacks
    def initializeWAMP(self):        
        protocol = yield getProtocol(
            TEST_STEPPER_MOTOR_SERVER
            if DEBUG else
            STEPPER_MOTOR_SERVER
        )
        self.polSM = ChunkedStepperMotorClient(protocol,POL)
        angle = yield getType(float,'enter polarizer angle: ')
        self.offset = {}
        BaseWAMP.initializeWAMP(self)        
        yield self.calibrateAngle(angle)       

    @command('calibrate-angle','recalibrate polarizer angle')
    @inlineCallbacks
    def calibrateAngle(self,angle):
        position = yield self.polSM.getPosition()
        self.offset['position'] = position
        self.offset['angle'] = angle
        self.dispatch('calibration-changed',self.offset)

    @command('get-angle','get calibrated polarizer angle')
    def _getAngle(self):
        return self.polSM.getPosition().addCallback(self.getAngle)
        
    def getAngle(self,step):
        return self.DEGREES_PER_STEP*(step - self.offset['position']) + self.offset['angle']

        
    @command('set-angle','set angle')
    @inlineCallbacks
    def setAngle(self,angle):
        # find desired polarizer step, inverted form of getAngle
        targetStep = int( round(
                (angle - self.offset['angle']) / self.DEGREES_PER_STEP + self.offset['position']
            )
        )
        # set the positions all at once, and wait for them to finish
        yield self.polSM.setPosition(targetStep)
        angle = yield self._getAngle()
        returnValue(angle)
        
        
    @command('cancel-angle-set','abort most recent angle set call')
    def cancelWavelengthCall(self):
        self.polSM.cancel()

        
def main():
    runServer(WAMP = PolarizerWAMP, URL = URL, debug = True)
if __name__ == '__main__':
    main()
    reactor.run()
