import sys
from PySide import QtGui, QtCore
from pyqtgraph import PlotWidget
import qt4reactor
app = QtGui.QApplication(sys.argv)
qt4reactor.install()
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from ab.abclient import getProtocol
from sitz import VOLTMETER_SERVER, TEST_VOLTMETER_SERVER, compose
from time import clock
from ab.abbase import selectFromList, sleep
from functools import partial

URL = TEST_VOLTMETER_SERVER
MAX = 200
SLEEP = .1

class VoltMeterWidget(QtGui.QWidget):
    def __init__(self,protocol):
        print 'running'
        QtGui.QWidget.__init__(self)
        self.setLayout(QtGui.QVBoxLayout())
        plotter = PlotWidget()
        self.plot = plotter.plot()
        self.layout().addWidget(plotter,1)
        
        voltages = [0] * MAX
        
        def onVoltagesAcquired(data):
            datum = data[self.channel] *1000
            lcd.display(datum)
            voltages.pop(0)
            voltages.append(datum)
            self.plot.setData(range(len(voltages)),voltages)

        controlPanel = QtGui.QHBoxLayout()
        controlPanel.addStretch(1)

        combo = QtGui.QComboBox()
        combo.currentIndexChanged[unicode].connect(
            partial(setattr,self,'channel')
        )
        combo.setCurrentIndex(0)             
        protocol.sendCommand('get-channels').addCallback(combo.addItems)

        controlPanel.addWidget(combo)

        lcd = QtGui.QLCDNumber(5)
        lcd.setSegmentStyle(lcd.Flat)

        controlPanel.addWidget(lcd)

        self.layout().addLayout(controlPanel)
        
        @inlineCallbacks
        def loop():
            voltages = yield protocol.sendCommand('get-voltages')
            onVoltagesAcquired(voltages)
            yield sleep(SLEEP)
            loop()
        loop()

@inlineCallbacks
def main():
    protocol = yield getProtocol(URL)
    widget = VoltMeterWidget(protocol)
    widget.show()

if __name__ == '__main__':
    main()
    app.exec_()
