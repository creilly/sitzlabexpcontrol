from twisted.internet.defer  import inlineCallbacks, returnValue
from ab.abbase import selectFromList, getFloat, getUserInput
from functools import partial
import daqmx
from daqmx.task.ai import VoltMeter


@inlineCallbacks
def configureVoltMeter():
    device = yield selectFromList(daqmx.getDevices(),'select device')
    channelDicts = []
    while True:
        channelDict = {}
        aborted = False
        #HACK
        channelDict['minVal'] = 0.0
        for optionKey, getOption in (
            (
                'physicalChannel',
                partial(
                    selectFromList,
                    [None] + daqmx.getPhysicalChannels(device)[daqmx.AI],
                    'select channel'
                )
            ),
            (
                'name',
                partial(
                    getUserInput,
                    'enter name: '
                )
            ),            
            (
                'maxVal',
                partial(
                    getFloat,
                    'insert max voltage: '
                )
            ),
            (
                'terminalConfig',
                partial(
                    selectFromList,
                    (
                        'default',
                        'differential'
                    ),
                    'select terminal configuration'
                )
            )
        ):
            opt = yield getOption()
            if opt is None:
                aborted = True
                break
            channelDict[optionKey] = opt            
        if aborted:
            if channelDicts:
                quit = yield selectFromList([True,False],'end task configuration?')
                if quit:
                    break
            continue
        channelDicts.append(channelDict)
    vm = VoltMeter(channelDicts)
    samplingRate = yield getFloat('enter sampling rate: ')
    vm.setSamplingRate(samplingRate)
    callbackRate = yield getFloat('enter callback rate: ')
    vm.setCallbackRate(callbackRate)
    returnValue(vm)