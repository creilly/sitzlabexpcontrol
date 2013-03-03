from sitz import SitzException, _decode_dict
from websocketserver import WebSocketServer, command, message, runServer
import os, json, tornado, datetime, sys

from rover import *
        
class RoverServer(WebSocketServer):
    STATE_FILE = "ROVER_STATE.DAT"
    LOG_FILE = "ROVER_LOG.DAT"
    MAX_ELEMENTS = 100

    _messages = [
        'samples',
        'change'        
    ]
    
    def initialize(self):
        daqmx.start()
        self.openLogFile()
        self.log('starting')
        self.openStateFile()
        self.loadState()
        self.timer = tornado.ioloop.PeriodicCallback(self.onTimer,100)
        self.timer.start()

    def terminate(self):
        daqmx.stop()
        self.writeState()
        self.closeStateFile()
        self.log('closing')
        self.closeLogFile()

    def openLogFile(self):
        self.logFile = open(self.LOG_FILE,'a')

    def closeLogFile(self):
        self.logFile.close()

    def log(self,message):
        message = '%s: %s\n' % (datetime.datetime.now(),message)
        print '\n' + message + '\n'
        self.logFile.write(message)

    def openStateFile(self):
        self.stateFile = open(self.STATE_FILE,'r+')

    def closeStateFile(self):
        self.stateFile.close()

    def loadState(self):
        stateStr = self.stateFile.read()
        if not stateStr:
            self.state = RoverState.emptyState()
            self.writeState()            
        else:
            self.state = RoverState(json.loads(stateStr,object_hook=_decode_dict))        
        for switch in self.state.switch.elements().values():
            self.setProperty('switch',switch.id,'fail',False)
            self.writeComputed(switch)

    def writeState(self):
        self.stateFile.seek(0)
        self.stateFile.truncate(0)
        self.stateFile.write(
            json.dumps(
                self.state.toDict(),
                sort_keys = True,
                indent = 2,
                separators = (',',': ')
            )
        )
        
    def onTimer(self):
        samples = self.getSamples()
        self.sendMessage('samples',samples)
        sys.stdout.flush()
        sys.stdout.write('\r' + str(samples))
        switches = self.state.switch.elements()
        for interlock in self.state.interlock.elements().values():
            switch = switches[interlock.switch]
            if not switch.fail:
                if switch.mode and switch.interlock:
                    if not interlock.defeated:
                        if ((samples[interlock.sensor]>interlock.threshold) is interlock.polarity):
                            self.setProperty('switch',switch.id,'fail',True)

    def writeComputed(self,switch):
        self.writeSwitch(switch,switch.getComputed())

    def writeSwitch(self,switch,state):
        switch.write(state)
        self.log('switch state wrote: switch %s state %s' % (switch.id, state))

    def getSamples(self):
        return {sensor.id: sensor.readSample() for sensor in self.state.sensor.elements().values()}
    
    @command('set property')
    def _setProperty(self,socket,proplist,value):
        self.setProperty(proplist,value)

    def setProperty(self,element,id,prop,value):
        setattr(getattr(getattr(self.state,element),id),prop,value)
        self.log('attribute set: %s -> %s -> %s = %s' % (element,id,prop,value))
        if element is 'switch':
            self.writeComputed(self.state.switch.elements()[id])

    @command('get state')
    def getState(self,socket):
        return self.state.toDict()

    # def getUniqueID(self):
    #     ids = [element.id for element in self.switch + self.sensor + self.interlock]
    #     i = 0
    #     while True:
    #         if i == MAX_ELEMENTS: raise SitzException('max number of elements exceeded')
    #         if str(i) not in ids: return str(i)
    #         i += 1


runServer(RoverServer(),8888)