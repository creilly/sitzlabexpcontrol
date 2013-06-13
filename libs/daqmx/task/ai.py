from daqmx import *
from daqmx.task import Task
from functools import partial

def schedule(f):
    def g(self,*args,**kwargs):
        if self.acquiring:
            def h():
                f(self,*args,**kwargs)
            def newCB(oldCB,samples):
                h()
                oldCB(samples)
            self.callback = partial(newCB,self.callback)
        else:
            f(self,*args,**kwargs)
    return g
class AITask(Task):
    # Default values
    # samplingRate = 1000.0
    # callbackRate = 1.0
    def __init__(
            self,
            channelDicts,            
            name = None
    ):
        Task.__init__(self,name)

        self.callback = None
        self.acquiring = False

        def callback(handle,eType,samples,callbackData):
            samples = self.readSamples()
            self.stopSampling()
            if self.callback is not None: self.callback(samples)
            return 0

        DAQmxDoneEventCallbackPtr = CFUNCTYPE(c_int, c_void_p, c_int, c_uint32, c_void_p)
        c_callback = DAQmxDoneEventCallbackPtr(callback)
        self.c_callback = c_callback

        daqmx(
            dll.DAQmxRegisterDoneEvent,
            (
                self.handle,
                0,
                self.c_callback,
                None
            )
        )        

        for channelDict in channelDicts:
            self.createChannel(**channelDict)

        daqmx(
            dll.DAQmxSetSampTimingType,
            (
                self.handle,
                constants['DAQmx_Val_SampClk']
            )
        )
        daqmx(
            dll.DAQmxSetSampQuantSampMode,
            (
                self.handle,
                constants['DAQmx_Val_FiniteSamps']
            )
        )

        self.callbackRate = self.getCallbackRate()
        
    def createChannel(
            self,
            physicalChannel,
            name = None,
            terminalConfig = 'default',
            minVal = -10.0,
            maxVal = 10.0
    ):
        terminalConfigs = {
            'default': constants['DAQmx_Val_Cfg_Default'], # At run time, NI-DAQmx chooses the default terminal configuration for the channel. 
            'rse': constants['DAQmx_Val_RSE'], # Referenced single-ended mode  
            'nrse': constants['DAQmx_Val_NRSE'], # Non-referenced single-ended mode  
            'differential': constants['DAQmx_Val_Diff'], # Differential mode  
            'pseudo-differential': constants['DAQmx_Val_PseudoDiff'], #Pseudodifferential mode  
        }
        daqmx(
            dll.DAQmxCreateAIVoltageChan,
            (
                self.handle,
                physicalChannel,
                name,
                terminalConfigs[terminalConfig],
                c_double(minVal),
                c_double(maxVal),
                constants['DAQmx_Val_Volts'],
                None
            )
        )
    @schedule    
    def setSamplingRate(self,samplingRate):
        daqmx(
            dll.DAQmxSetSampClkRate,
            (
                self.handle,
                c_double(float(len(self.getChannels())) * samplingRate)
            )
        )
        self._setSamplesPerChannel()
            
    def getSamplingRate(self):
        samplingRate = c_double(0)
        daqmx(
            dll.DAQmxGetSampClkRate,
            (
                self.handle,
                byref(samplingRate)
            )
        )
        return samplingRate.value / float(len(self.getChannels()))
    
    @schedule
    def setCallbackRate(self,callbackRate):
        self.callbackRate = callbackRate
        self._setSamplesPerChannel()

    def getCallbackRate(self):
        return self.getSamplingRate() / self.getSamplesPerChannel()

    def _setSamplesPerChannel(self):
        daqmx(
            dll.DAQmxSetSampQuantSampPerChan,
            (
                self.handle,
                c_uint64(
                    len(self.getChannels()) * int(self.getSamplingRate() / self.callbackRate)
                )
            )
        )

    def getSamplesPerChannel(self):
        samplesPerChannel = c_uint64(0)
        daqmx(
            dll.DAQmxGetSampQuantSampPerChan,
            (
                self.handle,
                byref(samplesPerChannel)
            )
        )
        return int( samplesPerChannel.value / float(len(self.getChannels())) )
            
    @schedule
    def configureExternalTrigger(self, trigSrc, trigEdge='rising'):
        trigEdgeTypes = {
            'rising': constants['DAQmx_Val_Rising'], # look up the DAQmx constant code for the rising edge.  see daqmx\daqmxconstants*
            'falling': constants['DAQmx_Val_Falling'], # look up the DAQmx constant code for the fall edge.  
        }
        daqmx(
            dll.DAQmxCfgDigEdgeStartTrig,
            (
                self.handle,
                trigSrc,
                trigEdgeTypes[trigEdge]
            )
        )
        
    @schedule  
    def setCallback(self,callback): 
        self.callback = callback
           
    def startSampling(self):

        if self.acquiring: raise SitzException('startSampling requested with task already acquiring')
        
        self.acquiring = True

        daqmx(
            dll.DAQmxStartTask,
            (
                self.handle,
            )
        )

    def stopSampling(self):

        if not self.acquiring: raise SitzException('stopSampling requested when task was not sampling')

        daqmx(
            dll.DAQmxStopTask,
            (
                self.handle,
            )
        )

        self.acquiring = False

    def readSamples(self):
        bufSize = c_uint32(0)
        daqmx(
            dll.DAQmxGetBufInputBufSize,
            (
                self.handle,
                byref(bufSize)
            )
        )
        bufSize = bufSize.value        
        samples = numpy.zeros(bufSize)
        samplesRead = c_int(0)
        daqmx(
            dll.DAQmxReadAnalogF64,
            (
                self.handle,
                constants['DAQmx_Val_Auto'],
                c_double(TIMEOUT), 
                constants['DAQmx_Val_GroupByChannel'],
                samples.ctypes.data_as(POINTER(c_double)), 
                bufSize,                
                byref(samplesRead), 
                None
            )
        )
        samplesRead = samplesRead.value
        channels = self.getChannels()
        byChannel = numpy.reshape(samples[:len(channels) * samplesRead],(len(channels),samplesRead))
        return {channel: data for channel, data in zip(channels,byChannel)}
        

    # def __enter__(self):        
        # self._acquiring = self.acquiring
        # if self._acquiring:
            # self.stopSampling()            
        # return self

    # def __exit__(self,t,v,tb):
        # if self._acquiring and not self.acquiring:
            # self.startSampling()
        # elif self.acquiring and not self._acquiring:
            # self.stopSampling()

class VoltMeter(AITask):
    def __init__(
            self,
            channelDicts,
            name = None
    ):
        AITask.__init__(
            self,
            channelDicts,            
            name
        )
        self.voltMeterCallback = lambda _: None
        AITask.setCallback(self,self.onSamples)

    def setCallback(self,callback):
        self.voltMeterCallback = callback

    def onSamples(self,samples):
        self.voltMeterCallback(
            {
                channel: numpy.average(data) for channel, data in samples.items()
            }
        )    
        
if __name__ == '__main__':
    t = AITask(
        (
            {
                'physicalChannel':'dev1/ai5'
            },
            {
                'physicalChannel':'dev1/ai7'
            }
        )
    )
    t.setSamplingRate(1.0)
    t.setCallbackRate(.33)
    t.configureExternalTrigger('/dev1/PFI0','falling')
    t.count = 0
    def cb(samples):
        t.count += 1
        print t.count, samples
        t.startSampling()
    t.setCallback(cb)
    t.startSampling()
    raw_input('waiting...\n')
    t.clearTask()