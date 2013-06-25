from PySide import QtGui, QtCore
from pyqtgraph import PlotWidget
import qt4reactor
app = QtGui.QApplication(sys.argv)
qt4reactor.install()
from scan import Scan, StepperMotorScanInput, VoltMeterScanOutput
from qtutils.toggle import ToggleObject, ToggleWidget
from libs.sitz import compose
import os

MIN = -99999
MAX = 99999

class ScanInputWidget(QtGui.QWidget):
    def __init__(self):
        scanToggle = ToggleObject()
        scanInputWidget = ToggleWidget(scanToggle)
        
        QtGui.QWidget.__init__(self)
        
        scanToggle.activationRequested.connect(

        
       
        scanToggleWidget = ToggleWidget(looper,('start','stop'))
        layout.addRow(scanToggleWidget)

        @inlineCallbacks
        def onLoopRequested(loopRequest):
            #start scan here
            
            current = yield client.getPosition()
            desired = spin.value()
            delta = desired - current
            if abs(delta) > GOTO_MAX:
                # sometimes hangs here (?)
                yield client.setPosition(current + delta / abs(delta) * GOTO_MAX)
                loopRequest.completeRequest(True)
            else:
                yield client.setPosition(desired)
                loopRequest.completeRequest(False)

        looper.activated.connect(looper.startLooping)        
        looper.loopRequested.connect(onLoopRequested)




        
        
class PlotWidget(QtGui.QWidget):
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
    title = 'scan gui'
    os.system('title %s' % title)
    widget = ScanInputWidget(Scan(smsi,vmso))
    widget.setWindowTitle(title)
    widget.show()

if __name__ == '__main__':
    main()
    reactor.run()
