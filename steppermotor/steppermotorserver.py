from steppermotor import PulseGeneratorStepperMotor, DigitalLineStepperMotor, FakeStepperMotor
from ab.abserver import BaseWAMP, command, runServer
from twisted.internet.defer  import Deferred, inlineCallbacks, returnValue
from twisted.internet  import reactor
from sitz import readConfigFile, STEPPER_MOTOR_SERVER, TEST_STEPPER_MOTOR_SERVER
from functools import partial
from ab.abbase import sleep
import sys
from os import path
from config.steppermotor import SM_CONFIG

DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'
    
class StepperMotorWAMP(BaseWAMP):
    
    UPDATE = .1 # duration between position notifications
    __wampname__ = 'stepper motor server'
    MESSAGES = {
        'position-changed':'notify when position changes',
        'step-rate-changed':'notify when stepping rate changes',
        'enable-status-changed':'notify when enabled or disabled'
    }

    def initializeWAMP(self):
        config = self.config = SM_CONFIG
        ## construct a dictionary of steppermotor objects
        self.sms = {}
        for id, options in config.items():
            if DEBUG:
                self.sms[id] = FakeStepperMotor()
            elif options['pulse_channel'].find('ctr') is -1:
                print 'adding '+str(id)+' as a digital output sm'
                self.sms[id] = DigitalLineStepperMotor(
                    options['pulse_channel'],
                    options['counter_channel'],
                    options['direction_channel'],
                    step_rate = options['step_rate'],
                    backlash = options['backlash'],
                    log_file = options['log_file'],
                    enable_channel = options['enable_channel']
                )
            else:
                print 'adding '+str(id)+' as a counter output sm'
                self.sms[id] = PulseGeneratorStepperMotor(
                    options['pulse_channel'],
                    options['counter_channel'],
                    options['direction_channel'],
                    step_rate = options['step_rate'],
                    backlash = options['backlash'],
                    log_file = options['log_file'],
                    enable_channel = options['enable_channel']
                )
            
               
        ## complete initialization
        BaseWAMP.initializeWAMP(self)

    @command('get-enable-status','query enable status of stepper motor')
    def getEnableState(self,sm):
        return self.sms[sm].getEnableStatus()
    
    '''
    @command('set-enable-status','set enable status of stepper motor')
    def setEnableState(self,sm,status):
        self.sms[sm].setEnableStatus(status)
        newState = self.sms[sm].getEnableStatus()
        self.dispatch('enable-status-changed', (sm,newState))
    '''
    
    @command('toggle-status','flip the enabled status of stepper motor')
    def toggleStatus(self,sm):
        self.sms[sm].toggleStatus()
        newState = self.sms[sm].getEnableStatus()
        self.dispatch('enable-status-changed', (sm,newState))

    @command('get-position','query position of stepper motor')
    def getPosition(self,sm):
        return self.sms[sm].getPosition()

    @command('set-position','set position of stepper motor')
    @inlineCallbacks
    def setPosition(self,sm,position):
        ## initialize deferred that will fire at end of stepping journey
        d = Deferred()
        ## function that is called periodically to update listeners on journey progress
        done = False
        def loop(_):
            self.dispatch(
                'position-changed',
                (
                    sm,
                    self.getPosition(sm)
                )
            )
            if not done:
                sleep(self.UPDATE).addCallback(loop)
        ## start journey
        self.sms[sm].setPosition(position,partial(d.callback,None))
        ## start updates
        loop(None)
        ## wait until journey done
        yield d
        done = True
        ## return ending position
        returnValue(self.getPosition(sm))

    @command('set-step-rate')
    def setStepRate(self,sm,stepRate):
        self.sms[sm].setStepRate(stepRate)
        self.dispatch(
            'step-rate-changed',
            (
                sm,
                stepRate
            )
        )

    @command('get-step-rate')
    def getStepRate(self,sm):
        return self.sms[sm].getStepRate()

    @command('get-configuration','retrieve dictionary of sm server configuration')
    def getConfig(self):
        return self.config

def main():
    runServer(WAMP = StepperMotorWAMP, URL = STEPPER_MOTOR_SERVER if not DEBUG else TEST_STEPPER_MOTOR_SERVER,debug = False,outputToConsole=True)
if __name__ == '__main__':
    main()
    reactor.run()
