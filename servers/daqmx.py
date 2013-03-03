from sitz import SitzException
from ctypes import *

dll = windll.LoadLibrary("nicaiu.dll")

BUF_SIZE = 10000

TIMEOUT = 5.0

SUCCESS = 0

# call a DAQmx function with arglist and raise a SitzException if error
def daqmx(f,args):
    result = f(*args)
    if result != SUCCESS:
        error = create_string_buffer(BUF_SIZE)
        dll.DAQmxGetErrorString(result,error,BUF_SIZE)
        raise SitzException(error.value)

def start():
    pass

def stop():
    while(tasks):
        clearTask(tasks.keys()[0])

tasks = {}

def createAITask(name):
    tasks[name] = AITask(name)
    
def createDOTask(name):
    tasks[name] = DOTask(name)

def getTask(task):
    try:
        return tasks[task]
    except KeyError:
        raise SitzException('no task by that name')

def getTasks():
    return tasks.keys()

def clearTask(task):
    daqmx(
        dll.DAQmxClearTask,
        (
            tasks.pop(task).handle,
        )
    )
    print 'cleared task: %s' % task
    

def getDevices():
    devices = create_string_buffer(BUF_SIZE)
    daqmx(
        dll.DAQmxGetSysDevNames,
        (
            devices,
            BUF_SIZE
        )
    )
    return parseStringList(devices.value)

def getPhysicalChannels(device):
    channels = create_string_buffer(BUF_SIZE)
    daqmx(
        dll.DAQmxGetDevAIPhysicalChans,
        (
            device,
            channels,
            BUF_SIZE
        )
    )
    return [channel.split('/')[-1]
            for channel in
            parseStringList(channels.value)]

class Task(object):
    def __init__(self,name):
        
        self.name = name
        handle = c_int(0)
        daqmx(
            dll.DAQmxCreateTask,
            (
                name,
                byref(handle)
            )
        )
        self.handle = handle.value

    def getChannels(self):
        channels = create_string_buffer(BUF_SIZE)
        daqmx(
            dll.DAQmxGetTaskChannels,
            (
                self.handle,
                channels,
                BUF_SIZE
            )
        )
        return parseStringList(channels.value)

class AITask(Task):    

    def createChannel(self,
                      physicalChannelName,
                      virtualChannelName,
                      terminalConfig = -1,
                      minVal = -10.0,
                      maxVal = 10.0,
                      units = 10348,
                      customScaleName = None):
        daqmx(
            dll.DAQmxCreateAIVoltageChan,
            (
                self.handle,
                physicalChannelName,
                virtualChannelName,
                terminalConfig,
                c_double(minVal),
                c_double(maxVal),
                units,
                customScaleName
            )
        )

    # def readSamples(self, numSamples = 1, timeout = TIMEOUT, fillMode = 0):
    #     numChannels = len(self.getChannels())
    #     arraySizeInSamps = numSamples * numChannels
    #     readArray = (c_double * arraySizeInSamps)()
    #     sampsPerChanRead = c_int(0)
    #     daqmx(
    #         dll.DAQmxReadAnalogF64,
    #         (
    #             self.handle,
    #             numSamples,
    #             c_double(timeout),
    #             fillMode,
    #             readArray,
    #             arraySizeInSamps, 
    #             byref(sampsPerChanRead),
    #             None
    #         )
    #     )
    #     samples = []
    #     if (fillMode is 0):
    #         samples = [ readArray[(i * numSamples):( ( i + 1 ) * numSamples )] for i in range(numChannels)]
    #     else:
    #         samples = [ [readArray[j * numChannels + i] for j in range(numSamples)] for i in range(numChannels) ]
    #     return samples

    def readSample(self, timeout = TIMEOUT):
        numChannels = len(self.getChannels())
        value = c_double()
        daqmx(
            dll.DAQmxReadAnalogScalarF64,
            (
                self.handle,
                c_double(TIMEOUT),
                byref(value),
                None
            )
        )
        return value.value

class DOTask(Task):

    def createChannel( self, physicalChannel, name, grouping = True ):
        daqmx(
            dll.DAQmxCreateDOChan,
            (
                self.handle,
                physicalChannel,
                name,
                grouping
            )
        )
        self.exponent = int(physicalChannel.split('line')[-1]) ##HACK

    def writeState( self, state ):
        daqmx(
            dll.DAQmxWriteDigitalScalarU32,
            (
                self.handle,
                True,
                c_double(TIMEOUT),
                int(state) * 2 ** self.exponent, ##HACK
                None
            )
        )

def parseStringList(stringList, delim = ', '):
    return stringList.split(delim) if stringList else []
