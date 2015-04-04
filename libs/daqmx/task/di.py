from daqmx import *
from daqmx.task import Task
class DITask(Task):
    
    """

    Configures a channel for digital reading

    params:

        physicalChannel: DAQmx indentifier for digital line
    name: indentifier for new virtual channel

    """
    def createChannel( self, physicalChannel, name=None ):
        daqmx(
            dll.DAQmxCreateDIChan,
            (
                self.handle,
                physicalChannel,
                name,
                constants['DAQmx_Val_ChanForAllLines']
            )
        )
        self.exponent = int(physicalChannel.split('line')[-1]) ##HACK

    """

    Reads the state of the digital line

    """
    def readState( self ):
        state = c_uint32(0)
        daqmx(
            dll.DAQmxReadDigitalScalarU32,
            (
                self.handle,
                c_double(TIMEOUT),
                byref(state),
                None
            )
        )
        return bool(state.value)

if __name__ == '__main__':
    t = DITask()
    t.createChannel('dev3/port0/line31')
    raw_input('read state')
    print t.readState()
