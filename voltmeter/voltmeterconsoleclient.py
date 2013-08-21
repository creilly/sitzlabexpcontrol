from ab.abclient import BaseClientFactory, BaseClientProtocol, getProtocol
from ab.consoleclient import ConsoleClient, runConsoleClient, consoleCommand
from ab.abbase import log, getDigit, selectFromList, getListIndex, getUserInput, getType
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from twisted.internet import reactor
from config.voltmeter import VM_SERVER_CONFIG, VM_DEBUG_SERVER_CONFIG
from time import clock
from daqmx.task.ai import AITask as AI
from functools import partial

#look for the user to pass 'debug' at runtime

import sys

DEBUG = len(sys.argv) > 1

class VoltMeterClient(ConsoleClient):
    '''    
    @consoleCommand('start','start the voltmeter')
    def startVM(self):
        return self.protocol.sendCommand('start')
    
    @consoleCommand('stop','stop the voltmeter')
    def stopVM(self):
        return self.protocol.sendCommand('stop')
    '''        
    @consoleCommand('get voltages','gets the most recently acquired voltages')
    def getVoltages(self):
        return self.protocol.sendCommand('get-voltages')

    @consoleCommand('get channel parameter','retrieves channel parameter')
    @inlineCallbacks
    def getChannelParameter(self):
        channel, parameter = yield self.selectChannelParameter()
        value = yield self.protocol.sendCommand('get-channel-parameter',channel,parameter)
        returnValue(
            zip(
                *AI.TERMINAL_CONFIGS
            )[2][
                zip(
                    *AI.TERMINAL_CONFIGS
                )[0].index(value)
            ] if parameter is AI.TERMINAL_CONFIG else value
        )

    @consoleCommand('set channel parameter','sets channel parameter')
    @inlineCallbacks
    def setChannelParameter(self):
        channel, parameter = yield self.selectChannelParameter()
        if parameter is AI.PHYSICAL_CHANNEL:
            returnValue('not yet supported')
        if parameter in (AI.MIN,AI.MAX):
            value = yield getType(float,'enter voltage: ')
        if parameter is AI.TERMINAL_CONFIG:            
            trmCfgIndex = yield getListIndex(zip(*AI.TERMINAL_CONFIGS)[2],'select configuration')
            value = zip(*self.TERMINAL_CONFIGS)[0][trmCfgIndex]
        if parameter is AI.DESCRIPTION:
            value = yield getUserInput('enter description: ')
        yield self.protocol.sendCommand('set-channel-parameter',channel,parameter,value)

    @inlineCallbacks
    def selectChannelParameter(self):
        channel = yield self.selectChannel()
        parameter = yield self.selectParameter()
        returnValue((channel,parameter))
        
    @inlineCallbacks
    def selectChannel(self):
        channels = yield self.protocol.sendCommand('get-channels')
        channel = yield selectFromList(channels,'select channel')
        returnValue(channel)
        
    @inlineCallbacks
    def selectParameter(self):
        paramIndex = yield getListIndex(zip(*AI.PARAMETERS)[1],'select parameter')
        param = zip(*AI.PARAMETERS)[0][paramIndex]
        returnValue(param)
        
    @inlineCallbacks
    def initializeConsoleClient(self):
        url = VM_SERVER_CONFIG['url'] if not DEBUG else VM_DEBUG_SERVER_CONFIG['url']
        self.protocol = yield getProtocol(url)
        def onMessage(d): print 'message: %s' % d
        self.protocol.messageSubscribe('channel-parameter-changed',onMessage)

    def onVoltagesMeasured(self,voltages):
        print clock()

if __name__ == '__main__':
    runConsoleClient(VoltMeterClient)    
    reactor.run()
