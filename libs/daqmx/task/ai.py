from daqmx import *
from daqmx.task import Task
from functools import partial

def schedule(f):
    def g(self,*args,**kwargs):
        if self.acquiring:
            def h():
                f(self,*args,**kwargs)
            def newCB(oldCB,samples):
                try:
                    h()
                except SitzException, e:
                    print str(e)
                self.callback = oldCB
                oldCB(samples)                
            self.callback = partial(newCB,self.callback)
        else:
            f(self,*args,**kwargs)
    return g

class AITask(Task):
    PHYSICAL_CHANNEL,NAME,TERMINAL_CONFIG,MIN,MAX,DESCRIPTION=0,1,2,3,4,5
    PARAMETERS = (
        (DESCRIPTION,'description'),
        (PHYSICAL_CHANNEL,'physical channel'),
        (MIN,'minimum voltage'),
        (MAX,'maximum voltage'),
        (TERMINAL_CONFIG,'terminal configuration')
    )
    TERM_DEFAULT,TERM_RSE,TERM_NRSE,TERM_DIFF,TERM_PSEUDO_DIFF=0,1,2,3,4
    TERMINAL_CONFIGS = (
        (
            TERM_DEFAULT,
            constants['DAQmx_Val_Cfg_Default'], # At run time, NI-DAQmx chooses the default terminal configuration for the channel.
            'default'
        ),     
        (
            TERM_RSE,
            constants['DAQmx_Val_RSE'], # Referenced single-ended mode
            'referenced single ended'
        ),
        (
            TERM_NRSE,
            constants['DAQmx_Val_NRSE'], # Non-referenced single-ended mode
            'nonreferenced single ended'
        ),        
        (
            TERM_DIFF,
            constants['DAQmx_Val_Diff'], # Differential mode
            'differential'
        ),
        (
            TERM_PSEUDO_DIFF,
            constants['DAQmx_Val_PseudoDiff'], #Pseudodifferential mode
            'pseudodifferential'
        )        
    )
    def __init__(self,channelDicts):
        Task.__init__(self)

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
            self.createChannel(channelDict)
            
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
        sampClkMaxRate = c_double()
        daqmx(
            dll.DAQmxGetSampClkMaxRate,
            (
                self.handle,
                byref(sampClkMaxRate)
            )
        )
        daqmx(
            dll.DAQmxSetSampClkRate,
            (
                self.handle,
                sampClkMaxRate
            )
        )
        
    def createChannel(self,channelDict):
        daqmx(
            dll.DAQmxCreateAIVoltageChan,
            (
                self.handle,
                channelDict[self.PHYSICAL_CHANNEL],
                channelDict.get(self.NAME,None),
                zip(*self.TERMINAL_CONFIGS)[1][
                    zip(*self.TERMINAL_CONFIGS)[0].index(
                        channelDict.get(
                            self.TERMINAL_CONFIG,
                            self.TERM_DEFAULT
                        )
                    )
                ],
                c_double(channelDict.get(self.MIN,-10.0)),
                c_double(channelDict.get(self.MAX,10.0)),
                constants['DAQmx_Val_Volts'],
                None
            )
        )
        if self.DESCRIPTION in channelDict:
            self.setChannelDescription(
                channelDict.get(self.NAME,channelDict[self.PHYSICAL_CHANNEL]),
                channelDict[self.DESCRIPTION]
            )
        
    @schedule    
    def setSamplingRate(self,samplingRate):
        daqmx(
            dll.DAQmxSetSampClkRate,
            (
                self.handle,
                c_double(samplingRate)
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
        return samplingRate.value
    
    @schedule
    def setCallbackRate(self,callbackRate):
        samplesPerChannel = int(self.getSamplingRate() / callbackRate)
        self._setSamplesPerChannel(samplesPerChannel)

    def getCallbackRate(self):
        return self.getSamplingRate() / self.getSamplesPerChannel()

    def _setSamplesPerChannel(self,samplesPerChannel):
        daqmx(
            dll.DAQmxSetSampQuantSampPerChan,
            (
                self.handle,
                c_uint64(
                    samplesPerChannel
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
        return samplesPerChannel.value
            
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
        
    PARAM_METHOD_MAP = {
        PHYSICAL_CHANNEL:'PhysicalChannel',
        TERMINAL_CONFIG:'TerminalConfig',
        MIN:'Min',
        MAX:'Max',
        DESCRIPTION:'Description'
    }
    
    def getChannelParameter(self,channel,parameter):
        return getattr(
            self,
            'getChannel' + self.PARAM_METHOD_MAP[parameter]
        )(channel)

    def setChannelParameter(self,channel,parameter,value):
        return getattr(
            self,
            'setChannel' + self.PARAM_METHOD_MAP[parameter]
        )(channel,value)

    def getChannelDescription(self,channel):
        description = ( c_char * BUF_SIZE )()
        daqmx(
            dll.DAQmxGetChanDescr,
            (
                self.handle,
                channel,
                description,
                BUF_SIZE
            )
        )
        return description.value
        
    @schedule
    def setChannelDescription(self,channel,description):
        daqmx(
            dll.DAQmxSetChanDescr,
            (
                self.handle,
                channel,
                str(description),
            )
        )

    def getChannelPhysicalChannel(self,channel):
        physicalChannel = create_string_buffer(BUF_SIZE)
        daqmx(
            dll.DAQmxGetPhysicalChanName,
            (
                self.handle,
                channel,
                physicalChannel,
                BUF_SIZE
            )
        )
        return physicalChannel.value
        
    @schedule
    def setChannelPhysicalChannel(self,channel,physicalChannel):
        daqmx(
            dll.DAQmxSetPhysicalChanName,
            (
                self.handle,
                channel,
                physicalChannel,
            )
        )

    def getChannelMin(self,channel):
        min = c_double()
        daqmx(
            dll.DAQmxGetAIMin,
            (
                self.handle,
                channel,
                byref(min)
            )
        )
        return min.value

    @schedule
    def setChannelMin(self,channel,min):
        daqmx(
            dll.DAQmxSetAIMin,
            (
                self.handle,
                channel,
                c_double(min),
            )
        )
    def getChannelMax(self,channel):
        max = c_double()
        daqmx(
            dll.DAQmxGetAIMax,
            (
                self.handle,
                channel,
                byref(max)
            )
        )
        return max.value

    @schedule        
    def setChannelMax(self,channel,max):
        daqmx(
            dll.DAQmxSetAIMax,
            (
                self.handle,
                channel,
                c_double(max),
            )
        )
        
    def getChannelTerminalConfig(self,channel):
        terminalConfig = c_int32()
        daqmx(
            dll.DAQmxGetAITermCfg,
            (
                self.handle,
                channel,
                byref(terminalConfig)
            )
        )
        return zip(*self.TERMINAL_CONFIGS)[0][
            zip(*self.TERMINAL_CONFIGS)[1].index(
                terminalConfig.value
            )
        ]

    @schedule        
    def setChannelTerminalConfig(self,channel,terminalConfig):
        daqmx(
            dll.DAQmxSetAITermCfg,
            (
                self.handle,
                channel,
                zip(*self.TERMINAL_CONFIGS)[1][
                    zip(*self.TERMINAL_CONFIGS)[0].index(
                        terminalConfig
                    )
                ]
            )
        )

class VoltMeter(AITask):
    def __init__(self,channelDicts):
        AITask.__init__(self,channelDicts)
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
    t = VoltMeter(
        (
            {
                VoltMeter.PHYSICAL_CHANNEL:'gamma/ai0'
            },
        )
    )

    t.setCallbackRate(2.0)
    def cb(data):
        print data
        t.startSampling()

    t.setCallback(cb)
    t.startSampling()

    raw_input('get params')
    for param in (
        getParam(t.getChannels()[0]) for getParam in (
            getattr(t,paramName) for paramName in (
                'getChannel' + par for par in (
                    'PhysicalChannel',
                    'TerminalConfig',
                    'Min',
                    'Max'
                )
            )
        )
    ): print param

    raw_input('set new params')
    for param in (
        getParam(t.getChannels()[0],value) for getParam,value in zip(
            (
                getattr(t,paramName) for paramName in (
                    'setChannel' + par for par in (
                        'TerminalConfig',
                        'Min',
                        'Max'
                    )
                )
            ),
            (
                t.TERM_RSE,
                -.1,
                .1
            )
        )
    ): print param

    raw_input('get new params')
    for param in (
        getParam(t.getChannels()[0]) for getParam in (
            getattr(t,paramName) for paramName in (
                'getChannel' + par for par in (
                    'PhysicalChannel',
                    'TerminalConfig',
                    'Min',
                    'Max'
                )
            )
        )
    ): print param

    raw_input('end test')
    t.stopSampling()
    t.clearTask()