from ab.abbase import sleep, selectFromList
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from numpy import array

'''
a scan object that simply performs the logic between a scanInput (control independent variable)
and a scanOutput (measure dependent variable(s)). It will perform any other instructions
specified by the onStep object (eg. plotting).

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
    def __init__(self,scanInput,scanOutput,onStep):
        self.scanInput, self.scanOutput, self.onStep = scanInput, scanOutput, onStep

    @inlineCallbacks
    def doScan(self,positions):
        while indepVar is not None:
            indepVar = yield self.scanInput.next()
            depVar = yield self.scanOutput.read()
            self.onStep(indepVar,depVar)
 
class listScanInput:
    def __init__(self,serverProtocol,valuesToScan):
        self.serverProtocol, self.valuesToScan = serverProtocol, valuesToScan

    #move to next value to measure at, return None if end of list 
    def next(self):
        if self.valuesToScan:
            return self.valuesToScan.pop(0)
        else:
            return None

class scanOutput:
    def __init__(self,server):
        self.server = server

    @inlineCallbacks
    def read(self):
        output = yield self.server.sendCommand('get-voltages')
        returnValue output


        
class StepperMotorScanInput(scanInput):
    def __init__(self,serverProtocol,positions):
        super(StepperMotorScanInput,self).__init__(serverProtocol,positions)
        self.smp = serverProtocol

    def next(self):
        position = super(StepperMotorScanInput,self).next()
        self.setPosition(position)
        
    def getPosition(self):
        return self.smp.sendCommand('get-position')

    def setPosition(self,position):
        return self.smp.sendCommand('set-position',position)

    def getWavelength(self):
        return self.smp.sendCommand('get-wavelength')

        
        
        
'''
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

'''