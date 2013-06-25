import sys
from PySide import QtGui, QtCore
from PySide.QtCore import Signal
from pyqtgraph import PlotWidget
import qt4reactor
app = QtGui.QApplication(sys.argv)
qt4reactor.install()
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue, succeed
from abclient import getProtocol
from sitz import VOLTMETER_SERVER
from steppermotorserver import getConfig
from functools import partial
from abbase import selectFromList
from scan import Scan, StepperMotorScanInput, VoltMeterScanOutput, GroupScanInput, VoltMeterStatsScanOutput
import pyqtgraph as pg
import numpy as np
from fileCreationMethods import saveCSV, filenameGen
from peakFitting import specAnalysis
import os

MIN = -99999
MAX = 99999
ZERO = 24205.6 #what the dial reads when the net steps sent is 0
DATAPATH = os.path.abspath("Z:\data\pooh")
EXPPEAKS = [24196.9,24210.6,24237.4,24277.2]
WIDTH = 1.


class StepperMotorScanWidget(QtGui.QWidget):
    START, STOP, STEP, WAIT, AVG = 0,1,2,3,4
    SPINS = {
        START:('start',MIN,MAX,-500),
        STOP:('stop',MIN,MAX,500),
        STEP:('step',1,100,5),
        WAIT:('wait',0,10000,300), # time to wait ( in milliseconds )
        AVG:('avg',1,1000,1) # shots to average 
    }
    scanToggled = Signal(bool)
    def __init__(self,scanInput,scanOutput):
        QtGui.QWidget.__init__(self)

        self.scan = Scan(scanInput,scanOutput,EXPPEAKS,WIDTH)
        #self.scan = SmartScan(scanInput,scanOutput,EXPPEAKS,WIDTH)

        self.x = []
        self.y = []
        self.yerr = []
        self.errorBars = []
        self.scantype = ''

        self.abort = False

        layout = QtGui.QHBoxLayout()

        plotter = PlotWidget()
        self.plotWidget = plotter
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
        
        spins[4].valueChanged.connect(partial(setattr, scanOutput, 'shotsToAvg'))
        self.scanToggled.connect(spin.setDisabled)
        
        #mod by stevens4 on 2013-06-08: promoted this method out of __init__ so that the doScan method can be modified by the smart scan check box
        @inlineCallbacks
        def onStart():
            #clear any error bars remaining from the last scan from the canvas
            self.plotWidget.clear()
            self.x = []
            self.y = []
            self.yerr = []
            self.errorBars = []
            self.abort = False
            start = spins[self.START].value()
            stop = spins[self.STOP].value()
            step = spins[self.STEP].value()
            wait = spins[self.WAIT].value() / 1000.0
            startButton.setEnabled(False)
            stopButton.setEnabled(True)
            self.scanToggled.emit(True)
            if smartScanChkBox.checkState():
                yield self.scan.doSmartScan(start,stop,step,wait,self.onStep)
            else:
                 yield self.scan.doScan(start,stop,step,wait,self.onStep)       
            stopButton.setEnabled(False)
            startButton.setEnabled(True)
            self.scanToggled.emit(False)
        
        def saveCSVButFunc():
            measure = scanTypeCombo.currentText()
            dataArray = np.asarray([self.x,self.y,self.yerr],dtype=np.dtype(np.float32))
            saveCSV(measure,dataArray.T,DATAPATH)
            
        def onAnalyze():
            displayCurve(*map(np.asarray(self.x,self.y,self.yerr)))
            
        def displayCurve(x,y,yerr):
            dataArray = np.vstack((x,y,yerr))
            fittedCurves,fittedParams = specAnalysis(dataArray=dataArray.transpose(),quiet=False)
            for curve in fittedCurves:
                self.plotWidget.addItem(curve)
            
            self.fittedParams = fittedParams
            
            # creates a newline seperated list of newline seperated peak parameters
            information = '\n'.join(
                [
                    'peak %d\n' % (index + 1) + '\n'.join(
                        [
                            '%s: %.2f' % (name,data) for name, data in zip(
                                ('peak at', 'amplitude', 'width'),
                                fitParam[:3]
                            )
                        ]
                    ) for index, fitParam in enumerate(fittedParams)
                ]
            )
            QtGui.QMessageBox.information(
                self,
                'Fitting Algorithm Results',
                "The fit algorithm has returned with %d peaks.\n" % len(fittedParams) +
                information
            )
        
        smartScanChkBox = QtGui.QCheckBox('smart scan')
        #only if steppermotor is PDL is this checkable
        smartScanChkBox.setCheckable(True)
        controlPanel.addRow(smartScanChkBox)
        
        startButton = QtGui.QPushButton('start scan')
        startButton.clicked.connect(onStart)
        controlPanel.addRow(startButton)
        
        stopButton = QtGui.QPushButton('stop scan')
        stopButton.clicked.connect(partial(setattr,self,'abort',True))
        stopButton.setEnabled(False)
        controlPanel.addRow(stopButton)

        channelsCombo = QtGui.QComboBox()
        controlPanel.addRow('channel',channelsCombo)

        smCombo = QtGui.QComboBox()
        smCombo.addItems(scanInput.scanInputs.keys())
        smCombo.currentIndexChanged[str].connect(partial(setattr,scanInput,'activeScanInput'))
        smCombo.currentIndexChanged[str].emit(smCombo.currentText())
        
        #I need this to enable the smart scan check box iff the steppermotor is the PDL. currently can't figure out how to capture the indexchanged signal
        #if smCombo.currentText() == "PDL":
        #    smartScanChkBox.setCheckable(True)
        controlPanel.addRow('stepper motor',smCombo)

        scanTypeCombo = QtGui.QComboBox()
        scanTypeCombo.addItems(["popBottle","popPiglet","popBeam","pdlPower","thirdHarmonicPower","bboScan","kdpScan"])
        controlPanel.addRow('scan type', scanTypeCombo)

        saveCSVButton = QtGui.QPushButton('save (csv)')
        saveCSVButton.clicked.connect(saveCSVButFunc)
        controlPanel.addRow(saveCSVButton)
        
        analyzeButton = QtGui.QPushButton('analyze spectrum')
        analyzeButton.clicked.connect(onAnalyze)
        controlPanel.addRow(analyzeButton)
        
        layout.addLayout(controlPanel)

        self.setLayout(layout)
        
        @inlineCallbacks
        def init():
            channels = yield scanOutput.vmp.sendCommand('get-channels')
            channelsCombo.addItems(channels)
            channelsCombo.currentIndexChanged[str].connect(partial(setattr,scanOutput,'channel'))
            channelsCombo.setCurrentIndex(channels.index(scanOutput.channel))
        def debug(_):
            SIZE = 300
            NOISE = 0.0001
            from peakFitting import gauss
            x = np.linspace(0,100,SIZE)
            rand = np.random.normal(0.0,NOISE,x.shape)
            f = gauss(x,80.0,1.0,5.0,0.01)
            g = gauss(x,30.0,1.0,5.0,0.0)
            y = f + rand
            dataPlotItem = pg.PlotDataItem(x,y,symbol='+')
            self.plotWidget.addItem(dataPlotItem)
            displayCurve(x,y,np.array([NOISE] * SIZE))
        init().addCallback(debug)
        
    

    '''
    # override this to modify what happens on scan step
    def onStep(self,position,power):
        #self.x.append(PDLDialConvert(position))
        self.x.append(position)
        self.y.append(power * 1000.0)
        self.plot.setData(self.x,self.y)
        return succeed(False if self.abort else True)
    '''
    
    #mod by stevens4 on 2013-06-08: replace onStep to handle an optional input 'std' (standard deviation) from 
    #voltmeterSTATSoutput and plot the resulting data with errorbars.
    def onStep(self,position,power,std=0):
        #self.x.append(PDLDialConvert(position))
        self.x.append(position)
        self.y.append(power * 1000.0)
        #self.plot.setData(self.x,self.y,symbol="+")
        dataPlotItem = pg.PlotDataItem(self.x,self.y,symbol='+')
        self.plotWidget.addItem(dataPlotItem)
        
        self.yerr.append(std * 1000.0)
        thisErrorBar = pg.ErrorBarItem(x=np.asarray(self.x),y=np.asarray(self.y),top=np.asarray(self.yerr),bottom=np.asarray(self.yerr),beam=.05)
        
        self.plotWidget.addItem(thisErrorBar)
        return succeed(False if self.abort else True)
    



@inlineCallbacks
def getScanInput():
    stepperMotors = ('KDP','BBO','PDL')
    config = getConfig()
    scanInputs = {}
    for stepperMotor in stepperMotors:
        protocol = yield getProtocol(config[stepperMotor]['url'])
        scanInput = StepperMotorScanInput(protocol)
        scanInputs[stepperMotor] = scanInput
    default = 'KDP'#yield selectFromList(stepperMotors,'select default stepper motor: ')
    scanInput = GroupScanInput(scanInputs,default)
    returnValue(scanInput)

#mod by stevens4 on 2013-06-08: made this return a voltmeterSTATSscanoutput instead for errorbars testing    
@inlineCallbacks
def getScanOutput(shotsToAvg=1):
    vmp = yield getProtocol(VOLTMETER_SERVER)
    channels = yield vmp.sendCommand('get-channels')
    channel = yield 'xtals power meter' #selectFromList(channels,'select default channel to monitor during scan')
    #returnValue(VoltMeterScanOutput(vmp,channel))
    returnValue(VoltMeterStatsScanOutput(vmp,channel,shotsToAvg))

@inlineCallbacks
def main():
    scanInput = yield getScanInput()
    scanOutput = yield getScanOutput()
    widget = StepperMotorScanWidget(scanInput,scanOutput)
    widget.setWindowTitle('scan gui')
    widget.show()

if __name__ == '__main__':
    main()
    reactor.run()
