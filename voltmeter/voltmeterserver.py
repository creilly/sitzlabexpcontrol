from ab.abserver import BaseWAMP, command, runServer
from twisted.internet.defer  import Deferred, inlineCallbacks, returnValue, succeed
from twisted.internet import reactor
from ab.abbase import selectFromList, getFloat, getUserInput
from functools import partial
import daqmx
from daqmx.task.ai import VoltMeter
from sitz import VOLTMETER_SERVER, TEST_VOLTMETER_SERVER

from config.voltmeter import VM_CONFIG

import sys
DEBUG = len(sys.argv) > 1
TRIGGERING = not DEBUG


URL = VOLTMETER_SERVER if not DEBUG else TEST_VOLTMETER_SERVER

# default rates
SAMPLING_RATE = 10000
CALLBACK_RATE = 20

class VoltMeterWAMP(BaseWAMP):

    MESSAGES = {
        'voltages-acquired':'voltages recently acquired'
    }

    @inlineCallbacks
    def initializeWAMP(self):
        self.voltMeter = vm = yield getVoltMeter()
        vm.setCallback(self.onVoltages)
        if TRIGGERING:
            getTriggerSourceEdge().addCallback(
                partial(
                    apply,
                    self.voltMeter.configureExternalTrigger
                )
            )
        vm.startSampling()
        BaseWAMP.initializeWAMP(self)

    def onVoltages(self,voltages):
        self.voltages = voltages
        self.voltMeter.startSampling() 
        self.dispatch('voltages-acquired',voltages)

    @command('get-voltages','returns most recently measured voltages')
    def getVoltages(self):
        return self.voltages

    @command('get-channels','get list of active channels')
    def getChannels(self):
        return self.voltMeter.getChannels()
    @command('get-sampling-rate')
    def getSamplingRate(self):
        return self.voltMeter.getSamplingRate()
    @command('set-sampling-rate')
    def setSamplingRate(self,rate):
        self.voltMeter.setSamplingRate(rate)
    @command('get-callback-rate')
    def getCallbackRate(self):
        return self.voltMeter.getCallbackRate()
    @command('set-callback-rate')
    def setCallbackRate(self,rate):
        self.voltMeter.setCallbackRate(rate)
     
def getTriggerSourceEdge():
    return succeed(('/dev1/pfi0','falling'))

def getVoltMeter():
    defaultVM = partial(VoltMeter, VM_CONFIG.values() 
        if not DEBUG else ({'physicalChannel':'alpha/ai0'},))
    vm = defaultVM()
    vm.setSamplingRate(SAMPLING_RATE)
    vm.setCallbackRate(CALLBACK_RATE)
    return vm
    
if __name__ == '__main__':
    runServer(WAMP = VoltMeterWAMP,debug=DEBUG,URL=URL,outputToConsole=True)
    reactor.run()
