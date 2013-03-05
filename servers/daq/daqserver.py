from websocketserver import WebSocketServer, command, runServer
from sitz import SitzException

import daqmx

class DAQServer(WebSocketServer):

    def initialize(self):
        daqmx.start()

    def terminate(self):
        daqmx.stop()

    @command('devices')
    def getDevices(self,socket):
        return daqmx.getDevices()
        
    @command('create ai task')
    def createAITask(self,socket,name):
        daqmx.createAITask(name)
        
    @command('create do task')
    def createDOTask(self,socket,name):        
        daqmx.createDOTask(name)
        
    @command('tasks')
    def getTasks(self,socket):
        return daqmx.getTasks()
        
    @command('clear task')
    def clearTask(self,socket,task):
        daqmx.clearTask(task)
    
    @command('create channel')
    def createChannel(self,socket,task,physicalChannel,name):
        daqmx.getTask(task).createChannel(physicalChannel,name)

    @command('virtual channels')
    def getVirtualChannels(self,socket,task):
        return daqmx.getTask(task).getChannels()

    @command('physical channels')
    def getPhysicalChannels(self,socket,device):
        return daqmx.getPhysicalChannels(device)
        
    @command('read sample')
    def readSample(self,socket,task):
        return daqmx.getTask(task).readSample()

    @command('write state')
    def writeState(self,socket,task,state):
        daqmx.getTask(task).writeState(state)
        
if __name__ == "__main__":
    runServer(DAQServer(),8888) 

