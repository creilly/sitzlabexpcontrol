from daqmx import *
from daqmx.task import Task

from threading import RLock
from functools import partial
from copy import copy

class COTask(Task):
    def __init__(self,name=None):
        super(COTask,self).__init__(name)
        self.busy = False 
        self._hooks = []
        self.lock = RLock()
    """

    Configures a channel for pulse train generation.

    params:
    
        physicalChannel: counter address
        name: identifier for new virtual channel
        highTime: time pulse spends in logic high state
        lowTime: time pulse spends in logic low state
        idleState:
            'low': output sits in low state when not generating pulses
            'high': output sits in high state when not generating pulses
        initialDelay: delay between task start and first pulse

    """
    def createChannel(self,physicalChannel,name=None,highTime=.01,lowTime=.01,idleState='low',initialDelay=0):
        idleStates = {
            'high':constants['DAQmx_Val_High'],
            'low':constants['DAQmx_Val_Low']
        }
        daqmx(
            dll.DAQmxCreateCOPulseChanTime,
            (
                self.handle,
                physicalChannel,
                name,
                constants['DAQmx_Val_Seconds'],
                idleStates[idleState],
                c_double(initialDelay),
                c_double(lowTime),
                c_double(highTime)
            )
        )

    """

    returns timing configuration ( a two-tuple of the time that pulse spends high and low, respectively, in seconds )

    """
    def getTimingConfiguration(self):
        highTime = c_double(0.0)
        lowTime = c_double(0.0)
        # only look at first channel
        daqmx (
            dll.DAQmxGetCOPulseHighTime,
            (
                self.handle,
                None,
                byref(highTime),
            )
        )
        daqmx (
            dll.DAQmxGetCOPulseLowTime,
            (
                self.handle,
                None,
                byref(lowTime),
            )
        )
        return highTime.value, lowTime.value

    """

    write new pulse shape (time is a float in units of seconds)

    """
    def configureTiming(self,highTime,lowTime):
        with self.lock:
            if self.busy:
                self.piggyBack(partial(self.configureTiming,highTime,lowTime))
                return
            self._configureTiming(highTime,lowTime)
    def _configureTiming(self,highTime,lowTime):
        daqmx (
            dll.DAQmxSetCOPulseHighTime,
            (
                self.handle,
                None,
                c_double(highTime),
            )
        )
        daqmx (
            dll.DAQmxSetCOPulseLowTime,
            (
                self.handle,
                None,
                c_double(lowTime),
            )
        )

    """

    generates a pulse train of configurable length, does nothing if numPulses < 1

    params:
        numPulses: number of pulses to generate
        callback: callable to execute upon on task completion
    
    """
    def generatePulses(self,numPulses,callback=lambda:None):
        if numPulses is 0: 
            callback()
            return
        with self.lock:
            if self.busy:
                self.piggyBack(partial(self.generatePulses,numPulses,callback))
                return
            self._generatePulses(numPulses,callback)

    def _generatePulses(self,numPulses,callback):
        # I DONT KNOW WHAT "THREAD SAFE" IS, BUT I WOULD BET THIS ISN'T THAT.
        # A GOOD USE FOR THIS WOULD BE TO LET THE CALLBACK JUST FIRE A DEFERRED
        # THAT'S WHAT I'M GONNA DO
        def _callback(handle,status,callbackData):
            daqmx(
                dll.DAQmxStopTask,
                (
                    self.handle,
                )
            )
            # before anyone can access pulser, do the following :
            # -> set busy to False, to let the first hook know pulser is free
            # -> get list of currently scheduled hooks
            # -> execute them in order received
            # -> -> one hook may busy the pulser, leading subsequent hooks attempts to queue
            # -> if pulser still free after hooks, execute callback, otherwise queue
            with self.lock:
                self.busy = False
                hooks = copy(self._hooks)
                self._hooks = []
                for hook in hooks:
                    hook()
                if self.busy:
                    self._hooks.append(callback)
                else:
                    callback()                
            return 0

        DAQmxDoneEventCallbackPtr = CFUNCTYPE(c_int, c_void_p, c_int, c_void_p)
        c_callback = DAQmxDoneEventCallbackPtr(_callback)
        
        self.c_callback = c_callback
        
        daqmx(
            dll.DAQmxRegisterDoneEvent,
            (
                self.handle,
                0, #executed in thread
                None,
                None
            )
        )
        
        daqmx(
            dll.DAQmxRegisterDoneEvent,
            (
                self.handle,
                0, #executed in thread
                self.c_callback,
                None
            )
        )

        daqmx(
            dll.DAQmxCfgImplicitTiming,
            (
                self.handle,
                constants['DAQmx_Val_FiniteSamps'],
                c_uint64(numPulses)
            )
        )
        
        self.busy = True
        
        daqmx(
            dll.DAQmxStartTask,
            (
                self.handle,
            )
        )

    def piggyBack(self,cb):
        self._hooks.append(cb)
 
if __name__ == '__main__':
    t = COTask()
    t.createChannel('dev3/ctr0')
    print 'timing %f, %f' % t.getTimingConfiguration()
    raw_input('generate 100 pulses then change timing and generate 100 more on callback')
    def onPulsesGenerated():
        print 'first callback'
        def onPulsesGenerated():
            print 'timing %f, %f' % t.getTimingConfiguration()
            print 'second callback (all done)'
        print 'timing %f, %f' % t.getTimingConfiguration()
        t.generatePulses(100,onPulsesGenerated)
    t.generatePulses(100,callback = onPulsesGenerated)
    t.configureTiming(.002,.002)
    t.generatePulses(100)
    raw_input('waiting...')
    
