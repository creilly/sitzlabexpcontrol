import sys
from PySide import QtGui, QtCore
from pyqtgraph import PlotWidget
import qt4reactor
app = QtGui.QApplication(sys.argv)
qt4reactor.install()
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue, succeed
from abclient import getProtocol
from sitz import VOLTMETER_SERVER
from steppermotorserver import getStepperMotorNameURL
from functools import partial
from abbase import selectFromList
from scan import Scan, StepperMotorScanInput, VoltMeterScanOutput

MIN = -99999
MAX = 99999

class StepperMotorScanWidget(QtGui.QWidget):
    START, STOP, STEP, WAIT = 0,1,2,3
    SPINS = {
        START:('start',MIN,MAX,-500),
        STOP:('stop',MIN,MAX,500),
        STEP:('step',1,100,5),
        WAIT:('wait',0,10000,300) # time to wait ( in milliseconds )
    }
    def __init__(self,scan):
        QtGui.QWidget.__init__(self)

        self.scan = scan

        self.x = []
        self.y = []

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

        def onStep(position,power):
            self.x.append(position)
            self.y.append(power * 1000.0)
            self.plot.setData(self.x,self.y)
            return succeed(False if self.abort else True)
            
        @inlineCallbacks
        def onStart():
            self.x = []
            self.y = []
            self.abort = False
            start = spins[self.START].value()
            stop = spins[self.STOP].value()
            step = spins[self.STEP].value()
            wait = spins[self.WAIT].value() / 1000.0
            startButton.setEnabled(False)
            stopButton.setEnabled(True)
            yield self.scan.doScan(start,stop,step,wait,onStep)
            stopButton.setEnabled(False)
            startButton.setEnabled(True)

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
    channel = yield selectFromList(channels,'select channel to monitor during scan')
    smsi = StepperMotorScanInput(smp)
    vmso = VoltMeterScanOutput(vmp,channel)
    title = '(%s) scan gui' % smName
    import os
    os.system('title %s' % title)
    widget = StepperMotorScanWidget(Scan(smsi,vmso))
    widget.setWindowTitle(title)
    widget.show()

if __name__ == '__main__':
    main()
    reactor.run()
