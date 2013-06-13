import sys
from PySide import QtGui, QtCore
from plotter import Plotter
from pyqtgraph import PlotWidget
import qt4reactor
app = QtGui.QApplication(sys.argv)
qt4reactor.install()
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from abclient import getProtocol
from sitz import VOLTMETER_SERVER, TEST_VOLTMETER_SERVER, compose
from time import clock
from abbase import selectFromList, sleep
from functools import partial

URL = VOLTMETER_SERVER
MAX = 200
mapEnabled = False

class VoltMeterWidget(QtGui.QWidget):
    def __init__(self,url=URL,listening=False):
        QtGui.QWidget.__init__(self)
        self.setLayout(QtGui.QVBoxLayout())
        plotter = PlotWidget()
        self.plot = plotter.plot()
        self.layout().addWidget(plotter,1)
        self.url = url
        self.listening = listening
        self.init()
        
    @inlineCallbacks
    def init(self):
        
        self.looping = False
        
        voltages = [0] * MAX
        
        def onVoltagesAcquired(data):
            datum = data[self.channel] *1000
            lcd.display(datum)
            voltages.pop(0)
            voltages.append(datum)
            self.plot.setData(range(len(voltages)),voltages)

        protocol = yield getProtocol(self.url)
        channels = yield protocol.sendCommand('get-channels')

        controlPanel = QtGui.QHBoxLayout()
        controlPanel.addStretch(1)

      
        
        @inlineCallbacks
        def onStart():
            if self.looping: returnValue(None)
            if self.listening: protocol.messageUnsubscribe('voltages-acquired')
            self.looping = True
            while self.looping:
                voltages = yield protocol.sendCommand('get-voltages')
                yield sleep(.15)
                #cbRate = yield protocol.sendCommand('get-callback-rate')
                onVoltagesAcquired(voltages)               

        startButton = QtGui.QPushButton('start')
        startButton.pressed.connect(onStart)
        controlPanel.addWidget(startButton)

        def onStop():
            if not self.looping: returnValue(None)
            self.looping = False
            if self.listening: protocol.messageSubscribe('voltages-acquired',onVoltagesAcquired)

        stopButton = QtGui.QPushButton('stop')
        stopButton.pressed.connect(onStop)
        controlPanel.addWidget(stopButton)

        callbackRate = yield protocol.sendCommand('get-callback-rate')
        callbackSpin = QtGui.QDoubleSpinBox()
        callbackSpin.setRange(callbackRate if callbackRate < .5 else .5,callbackRate if callbackRate > 10.0 else 10.0)
        callbackSpin.setDecimals(1)
        callbackSpin.setSingleStep(.1)
        callbackSpin.setValue(callbackRate)
        callbackSpin.editingFinished.connect(
            compose(
                partial(protocol.sendCommand,'set-callback-rate'),
                callbackSpin.value
            )
        )
        controlPanel.addWidget(callbackSpin)

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

        if self.listening: protocol.messageSubscribe('voltages-acquired',onVoltagesAcquired)


widget = VoltMeterWidget()

widget.show()

app.exec_()
