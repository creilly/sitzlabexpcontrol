from sitz import SitzException
from ctypes import *
from daqmxconstants import constants

import numpy

dll = windll.LoadLibrary("nicaiu.dll")

BUF_SIZE = 100000

TIMEOUT = 5.0

SUCCESS = 0

# call a DAQmx function with arglist and raise a SitzException if error
def daqmx(f,args):
    result = f(*args)
    if result != SUCCESS:
        error = create_string_buffer(BUF_SIZE)
        dll.DAQmxGetErrorString(result,error,BUF_SIZE)
        raise SitzException(error.value)

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

AI = 0
DO = 1
CI = 2
CO = 3

TASK_TYPES = {
    AI:'analog input',
    DO:'digital output',
    CI:'counter input',
    CO:'counter output'
}

def getPhysicalChannels(device):
    d = {}
    for taskType in TASK_TYPES.keys():
        channels = create_string_buffer(BUF_SIZE)
        daqmx(
            getattr(
                dll,
                {
                    AI:'DAQmxGetDevAIPhysicalChans',
                    DO:'DAQmxGetDevDOLines',
                    CI:'DAQmxGetDevCIPhysicalChans',
                    CO:'DAQmxGetDevCOPhysicalChans'
                }[taskType]
            ),
            (
                device,
                channels,
                BUF_SIZE
            )
        )
        d[taskType] = parseStringList(channels.value)
    return d

def parseStringList(stringList):
    return stringList.split(', ') if stringList else []

if __name__ == '__main__':
    for device in getDevices():
        print device
        for taskType, channels in getPhysicalChannels(device).items():
            print '\t' + TASK_TYPES[taskType]
            for channel in channels:
                print '\t\t' + channel
