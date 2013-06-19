import sys
from PySide import QtGui, QtCore
from PySide.QtCore import Signal
from pyqtgraph import PlotWidget
import qt4reactor
app = QtGui.QApplication(sys.argv)
qt4reactor.install()
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue, succeed, Deferred 
from abclient import getProtocol
from sitz import VOLTMETER_SERVER
from steppermotorserver import getStepperMotorNameURL
from functools import partial
from abbase import selectFromList
from scan import Scan, StepperMotorScanInput, VoltMeterScanOutput

MIN = -99999
MAX = 99999


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


class VoltMeterAvgdScanMultiOutput(VoltMeterAvgdScanOutput):
    def __init__(self,voltMeterProtocol,channels,shotsToAvg):
        VoltMeterAvgdScanOutput.__init__(self,voltMeterProtocol,channels,shotsToAvg)
        self.channels = channels
    
    def getOutput(self):
        outputDict = {}
        for channel in self.channels:
            self.channel = channel
            output = VoltMeterAvgdScanOutput.getOutput(self)
            outputDict.update({'channel':channel,'output':output})
        return outputDict
    

class StepperMotorScanWidget(QtGui.QWidget):
    START, STOP, STEP, WAIT = 0,1,2,3
    SPINS = {
        START:('start',MIN,MAX,-500),
        STOP:('stop',MIN,MAX,500),
        STEP:('step',1,100,5),
        WAIT:('wait',0,10000,300) # time to wait ( in milliseconds )
    }
    scanToggled = Signal(bool)
    def __init__(self,scan,channels):
        QtGui.QWidget.__init__(self)

        self.scan = scan

        self.abort = False

        layout = QtGui.QHBoxLayout()

        plotter = PlotWidget()
        self.plot = plotter.plot()

        layout.addWidget(plotter,1)

        controlPanel = QtGui.QFormLayout()

        spins = {}
        for id, spinConfig in self.SPINS.items():
            name, min, max, default = spinConfig
            spin = QtGui.QSpinBox()
            spin.setMinimum(min)
            spin.setMaximum(max)
            spin.setValue(default)
            spins[id] = spin
            controlPanel.addRow(name,spin)

        def onStep(position,powers):
            self.x.append(PDLDialConvert(position))
            i = 0
            for power in powers:
                self.y[i].append(power*1000.0)
                self.plot.plot(self.x,self.y[i],pen=i)
                i = i + 1
            return succeed(False if self.abort else True)       
            
        @inlineCallbacks
        def onStart():
            self.x = []
            self.y = []
            for channel in channels:
                self.y.append([])
            self.abort = False
            start = spins[self.START].value()
            stop = spins[self.STOP].value()
            step = spins[self.STEP].value()
            wait = spins[self.WAIT].value() / 1000.0
            startButton.setEnabled(False)
            stopButton.setEnabled(True)
            self.scanToggled.emit(True)
            yield self.scan.doScan(start,stop,step,wait,onStep)
            stopButton.setEnabled(False)
            startButton.setEnabled(True)
            self.scanToggled.emit(False)

        startButton = QtGui.QPushButton('start scan')
        startButton.clicked.connect(onStart)
        controlPanel.addRow(startButton)
        
        stopButton = QtGui.QPushButton('stop scan')
        stopButton.clicked.connect(partial(setattr,self,'abort',True))
        stopButton.setEnabled(False)
        controlPanel.addRow(stopButton)

        layout.addLayout(controlPanel)

        self.setLayout(layout)

@inlineCallbacks
def main():
    smName, smURL = yield getStepperMotorNameURL()
    smp = yield getProtocol(smURL)
    vmp = yield getProtocol(VOLTMETER_SERVER)
    channels = yield vmp.sendCommand('get-channels')
    #channel = yield selectFromList(channels,'select channel to monitor during scan')
    smsi = StepperMotorScanInput(smp)
    vmso = VoltMeterAvgdScanMultiOutput(vmp,channels,10)
    title = '(%s) scan gui' % smName
    import os
    os.system('title %s' % title)
    widget = StepperMotorScanWidget(Scan(smsi,vmso),channels)
    widget.setWindowTitle(title)
    widget.show()

if __name__ == '__main__':
    main()
    reactor.run()
