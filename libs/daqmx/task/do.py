from daqmx import *
from daqmx.task import Task
class DOTask(Task):
    
    """

    Configures a channel for digital writing

    params:

        physicalChannel: DAQmx indentifier for digital line
    name: indentifier for new virtual channel

    """
    def createChannel( self, physicalChannel, name=None ):
        daqmx(
            dll.DAQmxCreateDOChan,
            (
                self.handle,
                physicalChannel,
                name,
                constants['DAQmx_Val_ChanForAllLines']
            )
        )
        self.exponent = int(physicalChannel.split('line')[-1]) ##HACK

    """

    Sets the state of the digital line

    params:

        state: state to write

    """
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

if __name__ == '__main__':
    t = DOTask()
    t.createChannel('dev3/port0/line31')
    raw_input('write true')
    t.writeState(True)
    raw_input('write false')
