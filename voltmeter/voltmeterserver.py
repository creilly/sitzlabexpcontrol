from abserver import BaseWAMP, command, runServer
from twisted.internet.defer  import Deferred, inlineCallbacks, returnValue, succeed
from twisted.internet import reactor
from abbase import selectFromList, getFloat, getUserInput
from functools import partial
import daqmx
from daqmx.task.ai import VoltMeter 
from sitz import VOLTMETER_SERVER, TEST_VOLTMETER_SERVER

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
    return succeed(('dev1/pfi0','falling'))
        
defaultVM = partial(
    VoltMeter,
    (
        {
            'physicalChannel':'dev1/ai4',
            'name':'dye power meter',
            'minVal':0.0,
            'maxVal':5.0,
            'terminalConfig':'differential'
        },
        {
            'physicalChannel':'dev1/ai7',
            'name':'xtals power meter',
            'minVal':0.0,
            'maxVal':0.1,
            'terminalConfig':'differential'
        },
        {
            'physicalChannel':'dev1/ai6',
            'name':'gated integrator',
            'minVal':0.0,
            'maxVal':10.0,
            'terminalConfig':'default'
        },
        {
            'physicalChannel':'dev1/ai5',
            'name':'thermocouple',
            'minVal':0.0,
            'maxVal':0.1,
            'terminalConfig':'default'
        }
    ) if not DEBUG else ({'physicalChannel':'alpha/ai0'},)
)

def getVoltMeter():
    vm = defaultVM()
    vm.setSamplingRate(SAMPLING_RATE)
    vm.setCallbackRate(CALLBACK_RATE)
    
@inlineCallbacks
def configureVoltMeter():
    device = yield selectFromList(daqmx.getDevices(),'select device')
    channelDicts = []
    while True:
        channelDict = {}
        aborted = False
        #HACK
        channelDict['minVal'] = 0.0
        for optionKey, getOption in (
            (
                'physicalChannel',
                partial(
                    selectFromList,
                    [None] + daqmx.getPhysicalChannels(device)[daqmx.AI],
                    'select channel'
                )
            ),
            (
                'name',
                partial(
                    getUserInput,
                    'enter name: '
                )
            ),            
            (
                'maxVal',
                partial(
                    getFloat,
                    'insert max voltage: '
                )
            ),
            (
                'terminalConfig',
                partial(
                    selectFromList,
                    (
                        'default',
                        'differential'
                    ),
                    'select terminal configuration'
                )
            )
        ):
            opt = yield getOption()
            if opt is None:
                aborted = True
                break
            channelDict[optionKey] = opt            
        if aborted:
            if channelDicts:
                quit = yield selectFromList([True,False],'end task configuration?')
                if quit:
                    break
            continue
        channelDicts.append(channelDict)
    vm = VoltMeter(channelDicts)
    samplingRate = yield getFloat('enter sampling rate: ')
    vm.setSamplingRate(samplingRate)
    callbackRate = yield getFloat('enter callback rate: ')
    vm.setCallbackRate(callbackRate)
    returnValue(vm)

if __name__ == '__main__':
    runServer(WAMP = VoltMeterWAMP,URL=URL,outputToConsole=True)
    reactor.run()
