from daqmx import *
from daqmx.task import Task

"""

Only works for one channel

"""
class AOTask(Task):
    
    """

    Configures a channel for analog writing

    params:

        physicalChannel: DAQmx indentifier for analog line
        name: indentifier for new virtual channel    

    """
    def createChannel(
            self,
            physicalChannel,
            name=None,
            minVal=0.0,
            maxVal=10.0
    ):
        daqmx(
            dll.DAQmxCreateAOVoltageChan,
            (
                self.handle,
                physicalChannel,
                name,
                c_double(minVal),
                c_double(maxVal),
                constants['DAQmx_Val_Volts'],
                None
            )
        )

    """

    params:

        voltage: new voltage to set

    """
    def writeVoltage( self, voltage ):
        daqmx(
            dll.DAQmxWriteAnalogScalarF64,
            (
                self.handle,
                True,
                c_double(TIMEOUT),
                c_double(voltage),
                None
            )
        )

if __name__ == '__main__':
    t = AOTask()
    t.createChannel('alpha/ao1')
    raw_input('write 4.5')
    t.writeVoltage(4.5)
    t.clearTask()
