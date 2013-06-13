from steppermotor import StepperMotor, FakeStepperMotor

from functools import partial
from abserver import BaseWAMP, command, runServer

from twisted.internet.defer  import Deferred, inlineCallbacks, returnValue
from twisted.internet  import reactor
from twisted.internet.task import LoopingCall

import ConfigParser
import pprint

from sitz import readConfigFile, ConfigSectionMap, compose

from functools import partial

from abbase import getDigit, selectFromList, sleep

CONFIG = 'stepperMotorServerConfig.ini'

def getStepperMotor(options):
    if options["name"] in ("Fake Stepper Motor 1","Fake Stepper Motor 2"):
        return FakeStepperMotor()
    else:
        return StepperMotor(
            options["pulse_channel"],
            options["direction_channel"],
            options["counter_channel"],
            int(options["backlash"])
        )
        
def getConfig():
    return readConfigFile(CONFIG)

@inlineCallbacks
def getStepperMotorOptions(prompt='Which Server to Run?'):
    config = getConfig()
    serverKey = yield selectFromList(config.keys(),prompt)
    options = config[serverKey]
    print '\n'.join('\t%s:\t%s' % (key, value) for key, value in options.items())
    returnValue(options)

@inlineCallbacks
def getStepperMotorURL(options = None):
    if options is None:
        options = yield getStepperMotorOptions('which stepper motor?')
    returnValue('ws://%s:%s' % (options["host_machine_ip"],options["serve_on_port"]))            

# returns name, url pair
@inlineCallbacks
def getStepperMotorNameURL(prompt='select stepper motor: '):
    options = yield getStepperMotorOptions(prompt)
    returnValue( (options['name'], options['url'] ) )
        
class StepperMotorWAMP(BaseWAMP):
    UPDATE = 0.1 # duration between position notifications
    __wampname__ = 'stepper motor server'
    MESSAGES = {
        'position-changed':'notify when position changes',
        'step-rate-changed':'notify when stepping rate changes'
    }

    def initializeWAMP(self,stepperMotor):
        self.stepperMotor = stepperMotor
        BaseWAMP.initializeWAMP(self)

    @command('get-position','query position of stepper motor')
    def _getPosition(self):
        return self.getPosition()        

    def getPosition(self):
        return self.stepperMotor.getPosition()

    @command('set-position','set position of stepper motor')
    @inlineCallbacks
    def setPosition(self,position):
        d = Deferred()
        def loop(_):            
            self.dispatch('position-changed',self.getPosition())
            if not d.called:
                sleep(self.UPDATE).addCallback(loop)
        self.stepperMotor.setPosition(position,partial(d.callback,None))
        loop(None)
        yield d
        returnValue(self.getPosition())

    @command('set-step-rate')
    def setStepRate(self,stepRate):
        self.stepperMotor.setStepRate(stepRate)
        self.dispatch('step-rate-changed',stepRate)

    @command('get-step-rate')
    def getStepRate(self):
        return self.stepperMotor.getStepRate()      

@inlineCallbacks
def main():
    import sys
    if len(sys.argv) < 2: options = yield getStepperMotorOptions()
    else: options = getConfig()[sys.argv[1]]
    url = yield getStepperMotorURL(options)
    stepperMotor = getStepperMotor(options)
    StepperMotorWAMP.__wampname__ += ' ' + options['name']
    runServer(WAMP = StepperMotorWAMP, URL = url,debug = True, outputToConsole=True, args=[stepperMotor])
if __name__ == '__main__':
    main()
    reactor.run()
