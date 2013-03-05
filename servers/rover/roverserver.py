from sitz import SitzException, _decode_dict
from websocketserver import WebSocketServer, command, message, runServer
import os, json, tornado, datetime, sys, tornado.web, tornado.template

from rover import *

class RoverHTML(tornado.web.RequestHandler):
    def get(self):
        TEMPLATE = 'www/rover.html'
        with open(TEMPLATE,'r') as templateFile:
            template = tornado.template.Template(templateFile.read())
        self.write(template.generate(state = self.application.state.toDict()))
        
class RoverServer(WebSocketServer):
    STATE_FILE = "ROVER_STATE.DAT"
    LOG_FILE = "ROVER_LOG.DAT"
    MAX_ELEMENTS = 100

    _handlers = [(r'/rover.html',RoverHTML)]

    _messages = [
        'samples',
        'change',
        'write'
    ]
    
    def __init__(self):
        super(RoverServer,self).__init__(static_path='www')
    
    def initialize(self):
        daqmx.start()
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

    def log(self,message):
        with file(self.LOG_FILE, 'r') as original: data = original.read()
        message = '%s: %s' % (datetime.datetime.now(),message)
        print '\n' + message
        with file(self.LOG_FILE, 'w') as modified: modified.write(message + '\n' + data)

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
                            self.log('threshold crossed: switch %s sensor %s interlock %s threshold %s' % (interlock.switch,interlock.sensor,interlock.id,str(interlock.threshold)))
                            self.setProperty('switch',switch.id,'fail',True)

    def writeComputed(self,switch):
        self.writeSwitch(switch,switch.getComputed())

    def writeSwitch(self,switch,state):
        switch.write(state)
        self.log('switch state wrote: switch %s state %s' % (switch.id, state))
        self.sendMessage('write',{'switch':switch.id,'state':state})

    def getSamples(self):
        return {sensor.id: sensor.readSample() for sensor in self.state.sensor.elements().values()}
    
    @command('set property')
    def _setProperty(self,socket,element,id,property,value):
        self.setProperty(element,id,property,value)

    def setProperty(self,element,id,prop,value):
        setattr(getattr(getattr(self.state,element),id),prop,value)
        self.log('attribute set: %s -> %s -> %s = %s' % (element,id,prop,value))
        self.sendMessage(
            'change',
            {
                'element':element,
                'id':id,
                'property':prop,
                'value':value
            }
        )
        if element == 'switch':
            self.writeComputed(self.state.switch.elements()[id])

    @command('get state')
    def getState(self,socket):
        return self.state.toDict()

    @command('get computed')
    def getComputed(self,socket,switch):
        return self.state.switch.elements()[switch].getComputed()

    # def getUniqueID(self):
    #     ids = [element.id for element in self.switch + self.sensor + self.interlock]
    #     i = 0
    #     while True:
    #         if i == MAX_ELEMENTS: raise SitzException('max number of elements exceeded')
    #         if str(i) not in ids: return str(i)
    #         i += 1

runServer(RoverServer(),8888)