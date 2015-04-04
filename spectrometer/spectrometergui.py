import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install() 

# for server calls
from twisted.internet.defer import inlineCallbacks, Deferred, returnValue
from twisted.internet.task import LoopingCall
from ab.abclient import getProtocol
from config.serverURLs import SPECTROMETER_SERVER, TEST_SPECTROMETER_SERVER
from spectrometerclient import SpectrometerClient

# for GUI to run, not related to server calls!
from twisted.internet import reactor
   
# some utility widgets
from qtutils.toggle import ToggleObject, ClosedToggle, ToggleWidget
from qtutils.dictcombobox import DictComboBox
from qtutils.layout import SqueezeRow
from qtutils.label import LabelWidget

from sitz import compose

# saving scan data
from filecreationmethods import saveCSV
from config.filecreation import POOHDATAPATH

# plotting
from math import pow
import numpy as np
from pyqtgraph import PlotWidget, ErrorBarItem, mkPen, LegendItem, InfiniteLine
import time

sample_interval_sec = .05
smoothing=1
oversampling=1
raw=False

DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'
NUM_PIXELS = 2028

class SpectrometerWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.setLayout(QtGui.QHBoxLayout())
        self.resize(700, 500)
        self.wave = []
        self.spec = []
        self.time = None
        
        @inlineCallbacks
        def onInit():
            # connect to server
            ipAddress = TEST_SPECTROMETER_SERVER if DEBUG else SPECTROMETER_SERVER
            protocol = yield getProtocol(ipAddress)
            
            # create a client
            self.client = SpectrometerClient(protocol)
            self.wave = yield self.client.getWavelengths()
            self.numberToAverage = 1
            self.numberAcquired = 0
            self.darkSpectrum = np.zeros(NUM_PIXELS)
            self.specProcessed = np.zeros(NUM_PIXELS)
            self.gettingDark = False
            
            # set up overall layout: 1 large panel (plot) to left of 1 narrow /
            # panel (controls) all above 1 skinny panel (timestamp)
            fullLayout = QtGui.QVBoxLayout()
            self.layout().addLayout(fullLayout)
            
            topHalfLayout = QtGui.QHBoxLayout()
            fullLayout.addLayout(topHalfLayout)
            
            # define the plot
            self.plotWidget = PlotWidget()
            self.plot = self.plotWidget.plot()
            topHalfLayout.addWidget(self.plotWidget,1)
            
            # define the controls panel
            cpLayout = QtGui.QVBoxLayout()
            topHalfLayout.addLayout(cpLayout)
            
            # define the capture controls (to go on controls panel)
            capLayout = QtGui.QVBoxLayout()
            
            def updatePlot(x,y):
                x = np.asarray(x)
                y = np.asarray(y)
                self.plotWidget.clear()
                self.plotWidget.plot(x,y,pen=mkPen('w',width=1))
                self.plotWidget.addItem(self.cursorVert)
                self.plotWidget.addItem(self.cursorHori)
                vertLabel.setText(str(round(self.cursorVert.pos()[0],2)))
                horiLabel.setText(str(round(self.cursorHori.pos()[1],2)))
            
            def avgSpec():
                oldAvgSpec = self.specProcessed
                addThis = self.spec - self.darkSpectrum
                self.numberAcquired += 1
                if self.numberAcquired < self.numberToAverage: 
                    scale = self.numberAcquired
                else:
                    scale = self.numberToAverage
                newAvg = (((scale-1)*oldAvgSpec + addThis)/scale)
                self.specProcessed = newAvg
                
            @inlineCallbacks   
            def capture():
                self.spec = yield self.client.getSpectrum()
                self.spec = np.asarray(self.spec)
                self.time = yield self.client.getLastTime()
                yield avgSpec()
                updatePlot(self.wave,self.specProcessed)
                self.timestamp.setText("last update: " + str(self.time))
                
            @inlineCallbacks
            def forcePress():
                self.numberAcquired = 0
                yield capture()
                
            forceButton = QtGui.QPushButton('force')        
            forceButton.clicked.connect(forcePress)
            capLayout.addWidget(forceButton)
            
            autoRunLayout = QtGui.QHBoxLayout()
            
            self.freeRunCall = LoopingCall(capture)
            self.freeRunStatus = False
            
            def freeRun():
                if self.freeRunStatus:
                    freeButton.setText("start auto")
                    forceButton.setEnabled(True)
                    self.freeRunCall.stop()
                    self.freeRunStatus = False
                    self.numberAcquired = 0
                    return
                if not self.freeRunStatus:
                    freeButton.setText("stop auto")
                    forceButton.setEnabled(False)
                    self.freeRunCall.start(autoRateSpin.value(), now=True)
                    self.freeRunStatus = True
                    
            freeButton = QtGui.QPushButton('start auto')
            freeButton.clicked.connect(freeRun)
            autoRunLayout.addWidget(freeButton)
            
            def updateAutoRate():
                if self.freeRunStatus:
                    self.freeRunCall.stop()
                    self.freeRunCall.start(autoRateSpin.value(), now=True)
            
            autoRateSpin = QtGui.QDoubleSpinBox()
            autoRateSpin.setRange(.1,10000.)
            autoRateSpin.setValue(.5)
            autoRateSpin.setSuffix("s")
            autoRateSpin.setSingleStep(.1)
            autoRateSpin.valueChanged.connect(updateAutoRate)
            autoRunLayout.addWidget(autoRateSpin)
            
            capLayout.addLayout(autoRunLayout)
                        
            cpLayout.addWidget(LabelWidget('capture',capLayout))
            
            
            # define the cursor/analysis controls
            curLayout = QtGui.QVBoxLayout()
            cpLayout.addWidget(LabelWidget('analysis', curLayout))
            
            self.cursorVert = InfiniteLine(pos=self.wave[NUM_PIXELS/2],angle=90,pen=mkPen('g',width=.5),movable=True)
            self.cursorHori = InfiniteLine(pos=0,angle=0,pen=mkPen('g',width=.5),movable=True)
            self.plotWidget.addItem(self.cursorVert)
            self.plotWidget.addItem(self.cursorHori)

            vertLayout = QtGui.QHBoxLayout()
            vertName = QtGui.QLabel()
            vertName.setText("wavelength: ")
            vertLayout.addWidget(vertName)
            vertLabel = QtGui.QLabel()
            vertLabel.setText(str(round(self.cursorVert.pos()[0],2)))
            vertLayout.addWidget(vertLabel)
            curLayout.addLayout(vertLayout)
            
            horiLayout = QtGui.QHBoxLayout()
            horiName = QtGui.QLabel()
            horiName.setText("intensity: ")
            horiLayout.addWidget(horiName)
            horiLabel = QtGui.QLabel()
            horiLabel.setText(str(round(self.cursorHori.pos()[0],2)))
            horiLayout.addWidget(horiLabel)
            curLayout.addLayout(horiLayout)
            
            # define the acquisition controls
            acqLayout = QtGui.QVBoxLayout()
            cpLayout.addWidget(LabelWidget('acquisition', acqLayout))
            
            # integration
            integLayout = QtGui.QHBoxLayout()
            acqLayout.addLayout(integLayout)

            integTimeLabel = QtGui.QLabel()
            integTimeLabel.setText("integration: ")
            integLayout.addWidget(integTimeLabel)
            
            def integTimeUpdate():
                newTime = integTimeSpin.value()
                self.client.setIntegrationTime(newTime)
            integTimeSpin = QtGui.QDoubleSpinBox()
            integTimeSpin.setRange(.001,10)
            integTimeSpin.setDecimals(3)
            integTimeSpin.setValue(.100)
            integTimeSpin.setSingleStep(.05)
            integTimeSpin.setSuffix("s")
            integTimeSpin.editingFinished.connect(integTimeUpdate)
            integLayout.addWidget(integTimeSpin)

            # averaging
            avgLayout = QtGui.QHBoxLayout()
            acqLayout.addLayout(avgLayout)

            avgLabel = QtGui.QLabel()
            avgLabel.setText("averaging: ")
            avgLayout.addWidget(avgLabel)
            
            def avgUpdate():
                self.numberToAverage = avgSpin.value()
            avgSpin = QtGui.QSpinBox()
            avgSpin.setRange(1,10000)
            avgSpin.setValue(1)
            avgSpin.valueChanged.connect(avgUpdate)
            avgLayout.addWidget(avgSpin)

            # dark spectrum
            darkLayout = QtGui.QHBoxLayout()
            acqLayout.addLayout(darkLayout)
            
            @inlineCallbacks
            def getDark():
                resetDark()
                self.gettingDark = True
                self.numberAcquired = 0
                wasInAuto = self.freeRunStatus
                if self.freeRunStatus: freeRun() #if in auto mode, stop it
                self.specProcessed = np.zeros(NUM_PIXELS)
                for specCount in range(self.numberToAverage):
                    yield capture()
                self.darkSpectrum = self.specProcessed
                self.specProcessed = np.zeros(NUM_PIXELS)
                if wasInAuto: freeRun()
                self.numberAcquired = 0
                self.gettingDark = False
                
            darkSpecButton = QtGui.QPushButton('dark')
            darkSpecButton.clicked.connect(getDark)
            darkLayout.addWidget(darkSpecButton)
            
            def resetDark():
                self.darkSpectrum = np.zeros(NUM_PIXELS)
                self.specProcessed = np.zeros(NUM_PIXELS)
            
            resetDarkButton = QtGui.QPushButton('reset')
            resetDarkButton.clicked.connect(resetDark)
            darkLayout.addWidget(resetDarkButton)
            
            
            
            # define the timestamp panel
            self.timestamp = QtGui.QLabel()
            self.timestamp.setText("last update: never")
            self.timestamp.setAlignment(QtCore.Qt.AlignCenter)
            fullLayout.addWidget(self.timestamp)
        
        onInit()
    
    

    
    
    def refresh(self):
        time.sleep(.5)
        self.update_plot()
        self.refresh()
    
    def closeEvent(self, event):
        reactor.stop()
        event.accept()


    
   

if __name__ == '__main__':
    from twisted.internet import reactor
    container = []
    widget = SpectrometerWidget()
    widget.show()
    container.append(widget)
    widget.setWindowTitle('spectrometer gui')
    reactor.run()
