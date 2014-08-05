from sitz import SitzException
from ctypes import *
from daqmxconstants import constants

import numpy

dll = windll.LoadLibrary("nicaiu.dll")
"""handle to NI DAQmx c library"""

BUF_SIZE = 100000
"""size of string buffers for daqmx calls"""

TIMEOUT = 5.0

SUCCESS = 0
"""DAQmx return code for successful function call"""

# call a DAQmx function with arglist and raise a SitzException if error
def daqmx(f,args):
    """
    execute the DAQmx function f with specified args
    and raise exception with error description if
    return code indicates failure.
    
    @param f: DAQmx function from L{dll} to be called
        e.g. C{dll.DAQmxGetSysDevNames}
    @type f: C func        

    @param args: tuple of C data types to be
        passed to f.
    @type args: tuple

    @returns: C{None}    
    """
    result = f(*args)
    if result != SUCCESS:
        error = create_string_buffer(BUF_SIZE)
        dll.DAQmxGetErrorString(result,error,BUF_SIZE)
        raise SitzException(error.value)

def getDevices():
    """
    returns list of device identifiers

    @returns: list
    """
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
"""id for analog input task type"""
DO = 1
"""id for digital output task type"""
CI = 2
"""id for counter input task type"""
CO = 3
"""id for counter output task type"""
AO = 4
"""id for analog output task type"""

TASK_TYPES = {
    AI:'analog input',
    DO:'digital output',
    CI:'counter input',
    CO:'counter output',
    AO:'analog output'
}
"""dictionary associating readable names with task type ids"""

def getPhysicalChannels(device):
    """
    return a list physical channels,
    organized by task type, available
    on the specified device

    @param device: device identifier (e.g. I{dev0})
    @type device: string

    @returns: dictionary. a list of physical
        channels for each task type
        are accessed by passing the
        associated task type id to
        the dictionary.    
    """
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
                    CO:'DAQmxGetDevCOPhysicalChans',
                    AO:'DAQmxGetDevAOPhysicalChans'
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
