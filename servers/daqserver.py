from websocketserver import WebSocketServer, command, runServer

from ctypes import *

dll = windll.LoadLibrary("nicaiu.dll")

BUF_SIZE = 10000

TIMEOUT = 5.0

def parseStringList(stringList, delim = ', '):
    return stringList.split(delim) if stringList else []

class AnalogInputTask(object):
    
    def __init__(self,name,create=True):
        
        self.name = name
        handle = c_int(0)

        if create:
            dll.DAQmxCreateTask(name, byref(handle))
        else:
            dll.DAQmxLoadTask(name, byref(handle))

        self.handle = handle.value

    def createChannel(self,
                      physicalChannelName,
                      virtualChannelName,
                      terminalConfig = -1,
                      minVal = -10.0,
                      maxVal = 10.0,
                      units = 10348,
                      customScaleName = None):
        dll.DAQmxCreateAIVoltageChan(self.handle,
                                     physicalChannelName,
                                     virtualChannelName,
                                     terminalConfig,
                                     c_double(minVal),
                                     c_double(maxVal),
                                     units,
                                     customScaleName)
        
    def getChannels(self):
        channels = create_string_buffer(BUF_SIZE)
        dll.DAQmxGetTaskChannels(self.handle,channels,BUF_SIZE)
        return parseStringList(channels.value)

    def readSamples(self, numSamples = 1, timeout = TIMEOUT, fillMode = 0):
        numChannels = len(self.getChannels())
        arraySizeInSamps = numSamples * numChannels
        readArray = (c_double * arraySizeInSamps)()
        sampsPerChanRead = c_int(0)
        dll.DAQmxReadAnalogF64(self.handle,
                               numSamples,
                               c_double(timeout),
                               fillMode,
                               readArray,
                               arraySizeInSamps, 
                               byref(sampsPerChanRead),
                               None)
        samples = []
        if (fillMode is 0):
            samples = [ readArray[(i * numSamples):( ( i + 1 ) * numSamples )] for i in range(numChannels)]
        else:
            samples = [ [readArray[j * numChannels + i] for j in range(numSamples)] for i in range(numChannels) ]
        return samples

    def readSample(self, timeout = TIMEOUT):
        numChannels = len(self.getChannels())
        value = c_double()
        dll.DAQmxReadAnalogScalarF64(self.handle, c_double(TIMEOUT), byref(value), None)
        return value.value

class DAQServer(WebSocketServer):

    def initialize(self):
        self.tasks = {}

    def terminate(self):
        print 'shutting down'
        while self.tasks:
            task = self.tasks.keys()[0]
            print 'removing task: ', task
            self.removeTask(task)

    @command('devices')
    def getDevices(self,socket):
        devices = create_string_buffer(BUF_SIZE)
        dll.DAQmxGetSysDevNames(devices,BUF_SIZE)
        return parseStringList(devices.value)

    @command('create task')
    def createTask(self,socket,name):
        if name in self.tasks:
            return {'error':'name "%s" already taken' % name}
        self.tasks[name] = AnalogInputTask(name)

    @command('tasks')
    def getTasks(self,socket):
        return self.tasks.keys()

    @command('load task')
    def loadTask(self,socket,name):
        self.tasks[name] = AnalogInputTask(name, create=False)

    @command('saved tasks')
    def getSavedTasks(self,socket):
        data = create_string_buffer(BUF_SIZE)
        dll.DAQmxGetSysTasks(data,BUF_SIZE)
        return parseStringList(data.value)
        
    @command('clear task')
    def clearTask(self,socket,task):
        self.removeTask(task)

    def removeTask(self,task):
        dll.DAQmxClearTask(self.tasks.pop(task).handle)
    
    @command('create channel')
    def createChannel(self,socket,task,physicalChannel,name):
        if name in self.tasks[task].getChannels():
            self.error(socket, 'already virtual channel with this name')
            return
        self.tasks[task].createChannel(physicalChannel,name)

    @command('virtual channels')
    def getVirtualChannels(self,socket,task):
        return self.tasks[task].getChannels()

    @command('physical channels')
    def getPhysicalChannels(self,socket,device):
        channels = create_string_buffer(BUF_SIZE)
        dll.DAQmxGetDevAIPhysicalChans(device,channels,BUF_SIZE)
        return [channel.split('/')[-1] for channel in parseStringList(channels.value)]

    @command('read sample')
    def readSample(self,socket,task):
        return self.tasks[task].readSample()

    @command('read samples')
    def readSamples(self,socket,task,numSamples):
        return self.tasks[task].readSamples(numSamples)
        
if __name__ == "__main__":
    runServer(DAQServer(),8888) 

