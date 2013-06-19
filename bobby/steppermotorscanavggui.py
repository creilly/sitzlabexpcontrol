import sys
from PySide import QtGui
from twisted.internet.defer import inlineCallbacks, returnValue, succeed, Deferred
from abclient import getProtocol
from sitz import VOLTMETER_SERVER
from steppermotorserver import getStepperMotorNameURL
from functools import partial
from abbase import selectFromList, getDigit, getFloat, sleep
from scan import VoltMeterScanOutput, Scan, VoltMeterStatsScanOutput
import pyqtgraph as pg
import numpy as np

'''
these functions are now defunct; there is a PDLserver that has built-in functions called
get-wavelength and set-wavelength. see pdlserver.py.
def PDLDialConvert(pdlCtr):
    return (pdlCtr/42.) + ZERO
    
def PDLCtrConvert(pdlDial):
    return (pdlDial-ZERO)*42.

def PDLZeroSet(currCtr,currDial):
    newZero = currDial - (1./42.)*currCtr
    return newZero    
'''

'''now defunct. replaced by: VoltMeterStatsScanOutput. see: scan.py.
#subclass the VoltMeterScanOutput to average some number of
#specified shots (external triggers) for each datapoint before
#returning the output.
class VoltMeterAvgdScanOutput(VoltMeterScanOutput):
    def __init__(self,voltMeterProtocol,channel,shotsToAvg):
        VoltMeterScanOutput.__init__(self,voltMeterProtocol,channel)
        self.shotsToAvg = shotsToAvg

    def getOutput(self):
        d = Deferred() 
        l = {'shotsAvgd':0, 'total':0}
        def onVoltagesMeasured(voltages):
            shotsAvgd, total = l['shotsAvgd'], l['total']
            shotsAvgd = shotsAvgd + 1
            total = voltages[self.channel] + total
            if shotsAvgd is self.shotsToAvg:
                self.vmp.messageUnsubscribe('voltages-acquired')
                d.callback(total/shotsAvgd)
            else:
                l['shotsAvgd'] = shotsAvgd
                l['total'] = total
        self.vmp.messageSubscribe('voltages-acquired',onVoltagesMeasured)
        return d
'''


'''
mod by stevens 4 on 2013-06-08:
this is now defunct. i have merged this content with that of steppermotorscangui

#subclass the StepperMotorScanWidget so that you can add a spinbox for
#setting the number of shots to average
class AvgdStepperMotorScanWidget(StepperMotorScanWidget):
    def __init__(self,scanInput,scanOutput):
        StepperMotorScanWidget.__init__(self,scanInput,scanOutput)
        name, min, max, default = 'shotsToAvg',1,1000,scanOutput.shotsToAvg #scanOutput.shotsToAvg
        spin = QtGui.QSpinBox()
        spin.setMinimum(min)
        spin.setMaximum(max)
        spin.setValue(default)
        self.layout().itemAt(1).insertRow(0, 'shots to average', spin)
        spin.valueChanged.connect(partial(setattr, scanOutput, 'shotsToAvg'))
        self.scanToggled.connect(spin.setDisabled)
        
        self.yerr = []
        
    #this alternate onStep function assumes you are using VoltMeterStatsScanOutput as your output function
    #which returns a list for power where the 0th entry is the average and the 1st is the standard deviation
    def onStep(self,position,power,std=0):
        #self.x.append(PDLDialConvert(position))
        self.x.append(position)
        self.y.append(power * 1000.0)
        self.yerr.append(std * 1000.0)
        self.errorBars = pg.ErrorBarItem(x=np.asarray(self.x),y=np.asarray(self.y),top=np.asarray(self.yerr),bottom=np.asarray(self.yerr),beam=.05)
        self.plot.setData(self.x,self.y)
        self.plotWidget.addItem(self.errorBars)
        return succeed(False if self.abort else True)
'''
        
@inlineCallbacks
def getScanOutput():
    vmp = yield getProtocol(VOLTMETER_SERVER)
    channels = yield vmp.sendCommand('get-channels')
    channel = yield selectFromList(channels,'select default channel to monitor during scan')
    returnValue(VoltMeterStatsScanOutput(vmp,channel,10))

@inlineCallbacks
def main():
    # pdlStartDial = yield getFloat('what is the PDL dial reading now? ')
    # currPDLCtr = yield smp.sendCommand('get-position')
    # ZERO = PDLZeroSet(currPDLCtr,pdlStartDial)
    
    # smsi = StepperMotorScanInput(smp)
    # #shotsToAvg = yield getDigit('how many shots to average: ')
    # shotsToAvg = 10
    # vmso = VoltMeterAvgdScanOutput(vmp,channel,shotsToAvg)
    # title = '(%s) scan gui' % smName
    # import os
    # os.system('title %s' % title)
    
    # scanType = yield selectFromList(['Smart','Dumb'], 'Select what type of scan to run')
    # if scanType == 'Smart':
    #     widget = AvgdStepperMotorScanWidget(SmartScan(smsi,vmso,EXPPEAKS,WIDTH),vmso,channels)
    #     title = 'Smart ' + title
    
    # if scanType == 'Dumb':
    #     widget = AvgdStepperMotorScanWidget(Scan(smsi,vmso),vmso,channels)
    #     title = 'Dumb ' + title
    
    # widget.setWindowTitle(title)
    scanInput = yield getScanInput()
    scanOutput = yield getScanOutput()
    widget = AvgdStepperMotorScanWidget(scanInput,scanOutput)
    widget.show()

if __name__ == '__main__':
    main()
    reactor.run()
