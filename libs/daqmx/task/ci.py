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
    def createChannel(self, physicalChannel, name=None, initialCount=0, polarity='external', edge='rising'):
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

    reads current count

    returns: current count    

    """
    def readCounts(self):
        counts = c_uint32(0);
        daqmx(
            dll.DAQmxReadCounterScalarU32,
            (
                self.handle,
                c_double(TIMEOUT),
                byref(counts),
                None
            )
        )
        return c_int32(counts.value).value

if __name__ == '__main__':
    t = CITask()
    t.createChannel('dev3/ctr3')
    t.start()
    raw_input('counting...(press enter):')
    print t.readCounts()
    t.stop()

