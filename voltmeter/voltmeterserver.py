from ab.abserver import BaseWAMP, command, runServer
from twisted.internet.defer  import Deferred, inlineCallbacks, returnValue, succeed
from twisted.internet import reactor
from ab.abbase import selectFromList, getFloat, getUserInput
from functools import partial
import daqmx
from daqmx.task.ai import VoltMeter
from sitz import VOLTMETER_SERVER, TEST_VOLTMETER_SERVER, compose

from config.voltmeter import VM_CONFIG, VM_SERVER_CONFIG, VM_DEBUG_SERVER_CONFIG, VM_DEBUG_CONFIG

import os

import pickle

import sys
DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'

TRIGGERING = not DEBUG

URL = (VM_SERVER_CONFIG if not DEBUG else VM_DEBUG_SERVER_CONFIG)['url']
CALLBACK_RATE = 15.0

CONFIG_DIR = 'Z:\\creilly\\sitzlabexpcontrol\\voltmeter\\config'

config_filename = None

class VoltMeterWAMP(BaseWAMP):    
    MESSAGES = {
        'voltages-acquired':'voltages recently acquired',
        'channel-parameter-changed':'user changed channel parameter'
    }
    @inlineCallbacks
    def initializeWAMP(self):
        self.voltMeter = vm = yield getVoltMeter()
        self.updateLogFile()
        vm.setCallback(self.onVoltages)
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
        
    @command('get-channel-parameter')
    def getChannelParameter(self,channel,parameter):
        return self.voltMeter.getChannelParameter(str(channel),parameter)
        
    @command('set-channel-parameter')
    def setChannelParameter(self,channel,parameter,value):
        self.voltMeter.setChannelParameter(str(channel),parameter,value)
        self.dispatch('channel-parameter-changed',(channel,parameter,value))
        self.updateLogFile()

    def updateLogFile(self):
        global config_filename
        with open(os.path.join(CONFIG_DIR,config_filename),'w') as config_file:
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
    config_files = filter(
        compose(
            os.path.isfile,
            partial(
                os.path.join,
                CONFIG_DIR
            )            
        ),
        os.listdir(CONFIG_DIR)
    )
    global config_filename 
    selection = yield selectFromList([None] + config_files,'select a config file')
    if selection:
        config_filename = selection
        with open(os.path.join(CONFIG_DIR,config_filename),'r') as config_file:
            config_dict = pickle.loads(config_file.read())
        returnValue(
            VoltMeter(
                config_dict.values()
            )
        )
    else:        
        config_filename = yield getUserInput('enter new config name')
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
