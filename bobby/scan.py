from abbase import sleep, selectFromList
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from numpy import array

'''
a scanOuput is an object that  \
implements a call 'getOutput' that returns a deferred that \
fires with the scan output

a scanInput is an object that has one method: \
setPosition(position) : returns a deferred that fires with the current position  \
when scanning object completes request
'''
#mod by stevens4 on 2013-06-08: added unpack operator on output in onStep call, this will handle measurements both with and 
#without errorbars as long as they are lists
#mod by stevens4 on 2013-06-08: merged with SmartScan object so that it now has a method 'doSmartScan', see below
class Scan:
    def __init__(self,scanInput,scanOutput,expPeaks=0,halfWidth=1):
        self.scanIn, self.scanOut = scanInput, scanOutput
        self.expPeaks, self.halfWidth = expPeaks, halfWidth
    """
    Perform a scan from position 'start' in steps of 'step' until you reach 'stop'.
    Wait 'wait' seconds before taking measurement.
    On completion of a step, 'onStep' is called with position and output, \
    and returns a deferred which returns True to continue scanning or False to abort.
    """
    
    #accepts a list of points to move the specified scanInput to and measure the scanOutput for
    @inlineCallbacks
    def doScan(self,positions,onStep):
        for position in positions:
            position = yield self.scanIn.setPosition(position)
            output = yield self.scanOut.getOutput()
            onwards = yield onStep(position,output)
    
    ''' replaced by stevens4 on 2013-06-11
    @inlineCallbacks
    def doScan(self,start,stop,step,wait,onStep):
        polarity = start < stop
        onwards = True
        position = start
        while (( position <= stop ) is polarity) and onwards:        
            position = yield self.scanIn.setPosition(position)
            yield sleep(wait)
            output = yield self.scanOut.getOutput()
            onwards = yield onStep(position,*output)
            position += step * ( 1 if polarity else -1 )
    '''
    #added by stevens4 on 2013-06-08
    #only scan around a given location (expPeaks) for some range (halfWidth) on either side of this location
    @inlineCallbacks
    def doSmartScan(self,start,stop,step,wait,onStep):
        polarity = start < stop
        onwards = True
        position = start
        while (( position <= stop ) is polarity) and onwards:        
            contained = False
            for peak in self.expPeaks:
                thisWavelength = yield self.scanIn.getWavelength()
                print thisWavelength
                contained = (thisWavelength >= peak-self.halfWidth) & (thisWavelength <= peak+self.halfWidth) or contained
            if (not contained) & (position != stop) & (position != start):
                position += step * ( 1 if polarity else -1 )
                continue
            else:
                position = yield self.scanIn.setPosition(position)
                yield sleep(wait)
                output = yield self.scanOut.getOutput()
                onwards = yield onStep(position,*output)
                position += step * ( 1 if polarity else -1 )

class StepperMotorScanInput:
    def __init__(self,stepperMotorProtocol):
        self.smp = stepperMotorProtocol

    def getPosition(self):
        return self.smp.sendCommand('get-position')

    def setPosition(self,position):
        return self.smp.sendCommand('set-position',position)

    def getWavelength(self):
        return self.smp.sendCommand('get-wavelength')
        

#mod by stevens4 on 2013-06-08: added getWavelength function so that Smart Scan can get the wavelength of the PDL for desert-avoidance
class GroupScanInput:
    def __init__(self,scanInputs,default):
        self.scanInputs = scanInputs
        self.activeScanInput = default

    def getPosition(self):
        return self.scanInputs[self.activeScanInput].getPosition()

    def setPosition(self,position):
        return self.scanInputs[self.activeScanInput].setPosition(position)
        
    def getWavelength(self):
        return self.scanInputs[self.activeScanInput].getWavelength()

#mod by stevens4 on 2013-06-08: now returns a single-element list for scan to unpack
class VoltMeterScanOutput:
    def __init__(self,voltMeterProtocol,channel):
        self.vmp = voltMeterProtocol
        self.channel = channel

    @inlineCallbacks
    def getOutput(self):
        voltages = yield self.vmp.sendCommand('get-voltages')
        returnValue([voltages] if self.channel is None else [voltages[self.channel]])

        
#subclass the VoltMeterScanOutput to compute the average AND standard dev
#of some number of specified shots (external triggers) for each datapoint 
#before returning the output.
class VoltMeterStatsScanOutput(VoltMeterScanOutput):
    def __init__(self,voltMeterProtocol,channel,shotsToAvg):
        VoltMeterScanOutput.__init__(self,voltMeterProtocol,channel)
        self.shotsToAvg = shotsToAvg

    def getOutput(self):
        d = Deferred() 
        l = {'shotsAvgd':0, 'values':[]}
        def onVoltagesMeasured(voltages):
            shotsAvgd, values = l['shotsAvgd'], l['values']
            shotsAvgd = shotsAvgd + 1
            values.append(voltages[self.channel])
            if shotsAvgd is self.shotsToAvg:
                self.vmp.messageUnsubscribe('voltages-acquired')
                valuesArray = array(values)
                valuesAvg = valuesArray.mean()
                valuesStd = valuesArray.std()
                d.callback([valuesAvg,valuesStd])
            else:
                l['shotsAvgd'] = shotsAvgd
                l['values'] = values
        self.vmp.messageSubscribe('voltages-acquired',onVoltagesMeasured)
        return d

