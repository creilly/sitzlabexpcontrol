from daqmx import *
from daqmx.task import Task

from threading import RLock
from functools import partial
from copy import copy

class COTask(Task):
    FINITE, CONTINUOUS = 0,1
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

    def getSampleMode(self):
        sampleMode = c_int(0)
        daqmx(
            dll.DAQmxGetSampQuantSampMode,
            (
                self.handle,
                byref(sampleMode)
            )
        )
        return {
            constants['DAQmx_Val_FiniteSamps']:self.FINITE,
            constants['DAQmx_Val_ContSamps']:self.CONTINUOUS
        }

    """

    write new pulse shape (time is a float in units of seconds)

    """
    def configureTiming(self,highTime,lowTime):
        with self.lock:
            if self.busy and self.getSampleMode() is self.FINITE:
                self.piggyBack(partial(self.configureTiming,highTime,lowTime))
            else:
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
    def generatePulses(self,numPulses=None,callback=lambda:None):
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
        if numPulses is not None:
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
                constants[
                    'DAQmx_Val_ContSamps'
                    if numPulses is None else
                    'DAQmx_Val_FiniteSamps'
                ],
                c_uint64(0 if numPulses is None else numPulses)
            )
        )
        
        self.busy = True
        
        daqmx(
            dll.DAQmxStartTask,
            (
                self.handle,
            )
        )

    def stop(self):
        daqmx(
            dll.DAQmxStopTask,
            (
                self.handle,
            )
        )

    def piggyBack(self,cb):
        self._hooks.append(cb)

class PulseWidthModulator(COTask):
    def getFrequency(self):
        return 1.0 / sum(self.getTimingConfiguration())
    def getDutyCycle(self):
        highTime, lowTime = self.getTimingConfiguration()
        return highTime / (highTime + lowTime)
    def setFrequency(self,frequency):
        dutyCycle = self.getDutyCycle()
        period = 1.0 / frequency
        self.configureTiming(
            dutyCycle * period,
            (1.0 - dutyCycle) * period
        )
    def setDutyCycle(self,dutyCycle):
        period = 1.0 / self.getFrequency()
        self.configureTiming(
            dutyCycle * period,
            (1.0 - dutyCycle) * period
        )

if __name__ == '__main__':
    from daqmx import getPhysicalChannels, getDevices, CO
    from ab.abbase import selectFromList, getType, getUserInput
    from twisted.internet import reactor, defer
    @defer.inlineCallbacks
    def main():
        t = PulseWidthModulator()
        device = yield selectFromList(
            getDevices(),
            'select device'
        )
        channel = yield selectFromList(
            getPhysicalChannels(device)[CO],
            'select physical channel'
        )
        t.createChannel(channel)
        frequency = yield getType(
            float,
            'enter frequency: '
        )
        t.setFrequency(frequency)
        dutyCycle = yield getType(
            float,
            'enter duty cycle: '
        )
        t.setDutyCycle(dutyCycle)
        yield getUserInput('press enter to start: ')
        t.generatePulses()
        while True:
            FREQ, DUTY, QUIT = 'frequency', 'duty cycle', 'quit'
            options = (FREQ,DUTY,QUIT)
            option = yield selectFromList(
                options,
                'select command'
            )
            if option is QUIT:
                break
            else:
                value = yield getType(
                    float,
                    'set new %s (%.2f): ' %
                    (
                        option,
                        getattr(
                            t,
                            {
                                FREQ:'getFrequency',
                                DUTY:'getDutyCycle'
                            }[option]
                        )()
                    )
                )
                getattr(
                    t,
                    {
                        FREQ:'setFrequency',
                        DUTY:'setDutyCycle'
                    }[option]
                )(value)            
        t.stop()
        reactor.stop()        
    main()
    reactor.run()