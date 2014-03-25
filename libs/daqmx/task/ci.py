from daqmx import *
from daqmx.task import Task

class CITask(Task):
    
    """

    configures a channel for counting

    params:

        physicalChannel: DAQmx idenitifier for counter
    name: identifier for new virtual channel
    initialCount: where to begin counting
    polarity:
    'up': count up
    'down': count down
    'external': count direction determined by digital line on counter
    edge:
    'rising': trigger on rising edge
    'falling': trigger on falling edge
    

    """
    deviceName = None
    offset = 0
    
    def createChannel(self, physicalChannel, name=None, initialCount=0, polarity='external', edge='rising'):
        deviceName = physicalChannel.split('/')[0]
        if not deviceName: deviceName = physicalChannel.split('/')[1] #avoid leading slash if user included it
        
        size = c_uint32(0)
        daqmx(
            dll.DAQmxGetDevCIMaxSize,
            (
                deviceName, 
                byref(size)
            )
        )
        self.size = size.value
        
        if self.size != 32: 
            self.offset = initialCount
            initialCount = 0
        
        polarities = {
            'up':constants['DAQmx_Val_CountUp'],
            'down':constants['DAQmx_Val_CountDown'],
            'external':constants['DAQmx_Val_ExtControlled']
        }
        edges = {
            'rising':constants['DAQmx_Val_Rising'],
            'falling':constants['DAQmx_Val_Falling'],
        }
        daqmx(
            dll.DAQmxCreateCICountEdgesChan,
            (
                self.handle,
                physicalChannel,
                name,
                edges[edge],
                initialCount,
                polarities[polarity]
            )
        )

    """

    start counting
pp
    """
    def start(self):
        daqmx(
            dll.DAQmxStartTask,
            (
                self.handle,
            )
        )

    """

    stop counting

    """
    def stop(self):
        daqmx(
            dll.DAQmxStopTask,
            (
                self.handle,
            )
        )
    """
    
    reads the counter size of the first virtual channel in bits
    
    returns the counter size
    
    """
    def getSize(self):
        return self.size
    """

    reads current count

    returns: current count    

    """
    
    @staticmethod
    def twos_comp(val, bits):
        """compute the 2's compliment of int value val"""
        if( (val&(1<<(bits-1))) != 0 ):
            val = val - (1<<bits)
        return val
        
    def readCounts(self):
        counts = c_int32(0);
        daqmx(
            dll.DAQmxReadCounterScalarU32,
            (
                self.handle,
                c_double(TIMEOUT),
                byref(counts),
                None
            )
        )
        if self.getSize() == 32: return c_int32(counts.value).value 
        else: 
            adjustedVal = self.twos_comp(counts.value,self.getSize()) + self.offset
            return adjustedVal

if __name__ == '__main__':
    t = CITask()
    t.createChannel('dev3/ctr3')
    t.start()
    raw_input('counting...(press enter):')
    print t.readCounts()
    t.stop()

