from abserver import BaseWAMP, command, runServer
from twisted.internet.defer  import Deferred, inlineCallbacks, returnValue
from twisted.internet import reactor
from abbase import selectFromList, getFloat
from functools import partial
import daqmx
from daqmx.task.ai import VoltMeter 
from sitz import VOLTMETER_SERVER, readConfigFile

URL = VOLTMETER_SERVER
SERVER_FILE = 'voltmeterServerConfig.ini'
DEVICES_FILE = 'voltmeterDevicesConfig.ini'

def readVMServerConf(serverFile=SERVER_FILE):
    #returns a dictionary of dictionaries
    serverOptions = readConfigFile(serverFile)
    return serverOptions["GlobalOptions"]

def readVMDevicesConf(devicesFile=DEVICES_FILE):
    #returns a dictionary of dictionaries
    fullOptions = readConfigFile(devicesFile)
    #map this to a list of dictionaries with the global options set for each
    listOfDicts = []
    for device in fullOptions.keys():
        thisDict = {}
        thisDict["name"] = fullOptions[device]["name"]
        thisDict["physicalChannel"] = fullOptions[device]["physical_channel"]
        thisDict["minVal"] = fullOptions[device]["min_val"]
        thisDict["maxVal"] = fullOptions[device]["max_val"]
        thisDict["terminalConfig"] = fullOptions[device]["terminal_config"]
        listOfDicts.append(thisDict)
    return listOfDicts

def getVoltmeter():
    devices = readVMConfig()
    
    
    
class VoltMeterWAMP(BaseWAMP):

    @inlineCallbacks
    def initializeWAMP(self):
        self.voltMeter = vm = yield getVoltMeter()
        vm.setCallback(self.onVoltages)
        self.voltMeter.startSampling()
        BaseWAMP.initializeWAMP(self)

    def onVoltages(self,voltages):
        self.voltages = voltages

    @command('get-voltages','returns most recently measured voltages')
    def getVoltages(self):
        return self.voltages

    @command('get-channels','get list of active channels')
    def getChannels(self):
        return self.voltMeter.getChannels()
        
if __name__ == '__main__':
    DevConf = readVMDevicesConf()
    ServConf = readVMServerConf()
    print DevConf
    print ServConf
    
    #runServer(WAMP = VoltMeterWAMP,URL=URL,debug=False)
    #reactor.run()
