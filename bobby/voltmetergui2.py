import sys
from PySide import QtGui, QtCore
from plotter import Plotter
import qt4reactor
app = QtGui.QApplication(sys.argv)
qt4reactor.install()
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from abclient import getProtocol
from sitz import VOLTMETER_SERVER, TEST_VOLTMETER_SERVER, compose
from time import clock
from abbase import selectFromList
from functools import partial

URL = VOLTMETER_SERVER
MAX = 200
class VoltMeterWidget(QtGui.QWidget):
    def __init__(self,url=URL):
        QtGui.QWidget.__init__(self)
        self.setLayout(QtGui.QVBoxLayout())
        self.plotter = Plotter()
        self.plotter.setAxis(Plotter.Y,0.0,130.0)
        self.layout().addWidget(self.plotter,1)
        self.url = url
        self.init()
        
    @inlineCallbacks
    def init(self):
        voltages = [0] * MAX
        @inlineCallbacks
        def onTimeout():
            volts = yield protocol.sendCommand('get-voltages')
            onVoltagesMeasured(volts)
        def onVoltagesMeasured(data):
            datum = data[self.channel] * 1000
            lcd.display(datum)
            voltages.pop(0)
            voltages.append(datum)
            self.plotter.updatePlot(range(len(voltages)),voltages)

        protocol = yield getProtocol(self.url)
        channels = yield protocol.sendCommand('get-channels')

        controlPanel = QtGui.QHBoxLayout()
        controlPanel.addStretch(1)

        combo = QtGui.QComboBox()
        combo.addItems(channels)
        combo.currentIndexChanged[unicode].connect(
            partial(setattr,self,'channel')
        )
        combo.setCurrentIndex(0)
        combo.currentIndexChanged[unicode].emit(channels[0])        

        controlPanel.addWidget(combo)

        lcd = QtGui.QLCDNumber(5)
        lcd.setSegmentStyle(lcd.Flat)

        controlPanel.addWidget(lcd)

        self.layout().addLayout(controlPanel)
        
        timer = self.timer = QtCore.QTimer()
        timer.setInterval(100)
        timer.timeout.connect(onTimeout)
        timer.start()
        #protocol.messageSubscribe('voltages-measured',onVoltagesMeasured)

widget = VoltMeterWidget()

widget.show()

app.exec_()
