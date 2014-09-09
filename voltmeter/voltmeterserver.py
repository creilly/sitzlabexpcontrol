from ab.abserver import BaseWAMP, command, runServer
from twisted.internet.defer  import Deferred, inlineCallbacks, returnValue, succeed
from twisted.internet import reactor
from ab.abbase import selectFromList, getFloat, getUserInput
from functools import partial
import daqmx
from daqmx.task.ai import VoltMeter

from config.voltmeter import VM_CONFIG, VM_SERVER_CONFIG, VM_DEBUG_SERVER_CONFIG, VM_DEBUG_CONFIG
from config.filecreation import LOGS_DIR

import os

import pickle

import sys
DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'

TRIGGERING = not DEBUG

URL = (VM_SERVER_CONFIG if not DEBUG else VM_DEBUG_SERVER_CONFIG)['url']
CALLBACK_RATE = 15.0

CONFIG_FILENAME = 'vm_settings_config.cfg'
CONFIG_FILEPATH = os.path.join(LOGS_DIR,CONFIG_FILENAME)


class VoltMeterWAMP(BaseWAMP):    
    MESSAGES = {
        'voltages-acquired':'voltages recently acquired',
        'channel-parameter-changed':'user changed channel parameter'
    }
    VOLTAGE,COUNT,TOTAL,DEFERRED,CHANNEL = 0,1,2,3,4
    @inlineCallbacks
    def initializeWAMP(self):
        self.voltMeter = vm = yield getVoltMeter()
        self.updateLogFile()

        vm.setCallback(self._onVoltages)
        self.d = Deferred()
        self.d.addCallback(self.onVoltages)

        self.requests = []
        
        vm.setCallbackRate(CALLBACK_RATE)
        if TRIGGERING:
            getTriggerSourceEdge().addCallback(
                partial(
                    apply,
                    self.voltMeter.configureExternalTrigger
                )
            )
        vm.startSampling()
        BaseWAMP.initializeWAMP(self)

    def _onVoltages(self,voltages):
        self.d.callback(voltages)

    def onVoltages(self,voltages):
        self.voltages = voltages
        self.voltMeter.startSampling()
        self.dispatch('voltages-acquired',voltages)
        self.d = Deferred()
        self.d.addCallback(self.onVoltages)
        for request in list(self.requests):
            request[self.VOLTAGE] += voltages[request[self.CHANNEL]] / float(request[self.TOTAL])
            request[self.COUNT] += 1
            if request[self.COUNT] is request[self.TOTAL]:
                self.requests.remove(request)
                request[self.DEFERRED].callback(request[self.VOLTAGE])

    @command('get-voltages','returns most recently measured voltages')
    def getVoltages(self):
        return self.voltages

    @command('get-n-voltages','get average of next n samples')
    def getNVoltages(self,channel,total):
        voltage = 0.
        count = 0
        total = total
        deferred = Deferred()
        self.requests.append(
            {
                self.VOLTAGE:voltage,
                self.CHANNEL:channel,
                self.COUNT:count,
                self.TOTAL:total,
                self.DEFERRED:deferred                
            }
        )
        return deferred

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
        
    @command('get-channel-parameter')
    def getChannelParameter(self,channel,parameter):
        return self.voltMeter.getChannelParameter(str(channel),parameter)
        
    @command('set-channel-parameter')
    def setChannelParameter(self,channel,parameter,value):
        self.voltMeter.setChannelParameter(str(channel),parameter,value)
        self.dispatch('channel-parameter-changed',(channel,parameter,value))
        self.updateLogFile()

    def updateLogFile(self):
        with open(CONFIG_FILEPATH,'w') as config_file:
            config_file.write(
                pickle.dumps(
                    {
                        channel:{
                            param:self.getChannelParameter(channel,param)
                            for param in zip(*VoltMeter.PARAMETERS)[0]
                        }
                        for channel in self.getChannels()
                    }
                )
            )
     
def getTriggerSourceEdge():
    return succeed(
        (
            VM_SERVER_CONFIG['trigChannel'],
            VM_SERVER_CONFIG['trigEdge']
        )
    )

@inlineCallbacks
def getVoltMeter():
    if os.path.isfile(CONFIG_FILEPATH):
        with open(CONFIG_FILEPATH,'r') as config_file:
            config_dict = pickle.loads(config_file.read())
        returnValue(
            VoltMeter(
                config_dict.values()
            )
        )
    else:        
        device = yield selectFromList(daqmx.getDevices(),'select a device')
        returnValue(
            VoltMeter(
                (
                    {VoltMeter.PHYSICAL_CHANNEL:channel,VoltMeter.VOLTAGE_RANGE:VoltMeter.V0_05}
                    for channel in
                    daqmx.getPhysicalChannels(device)[daqmx.AI]
                )
            )
        )
    
if __name__ == '__main__':
    runServer(WAMP=VoltMeterWAMP,debug=False,URL=URL,outputToConsole=True)
    reactor.run()
