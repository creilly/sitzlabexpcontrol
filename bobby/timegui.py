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


class TimeWidget(QtGui.QWidget):
    def __init__(self,outputObject):
        QtGui.QWidget.__init__(self)

        self.x = []
        self.y = []
        self.yerr = []

        self.abort = False

        layout = QtGui.QHBoxLayout()

        plotter = PlotWidget()
        self.plotWidget = plotter
        self.plot = plotter.plot()

        layout.addWidget(plotter,1)

        controlPanel = QtGui.QFormLayout()

        #create the spinbox for the shots to average parameter
        name, min, max, default = ('avg',1,1000,10)
        avgSpin = QtGui.QSpinBox()
        avgSpin.setMinimum(min)
        avgSpin.setMaximum(max)
        avgSpin.setValue(default)
        controlPanel.addRow(name,avgSpin)
        
        @inlineCallbacks
        def reset():
            #clear the canvas
            self.plotWidget.clear()
            #reinitialize all data arrays
            self.x, self.y, self.yerr = [], [], []
            self.abort = False
            
        def saveCSVButFunc():
            measure = scanTypeCombo.currentText()
            dataArray = np.asarray([self.x,self.y,self.yerr],dtype=np.dtype(np.float32))
            saveCSV(measure,dataArray.T,DATAPATH)

        resetButton = QtGui.QPushButton('reset')
        resetButton.clicked.connect(reset)
        controlPanel.addRow(resetButton)

        
        
        
        saveCSVButton = QtGui.QPushButton('save (csv)')
        saveCSVButton.clicked.connect(saveCSVButFunc)
        controlPanel.addRow(saveCSVButton)
        
        layout.addLayout(controlPanel)

        self.setLayout(layout)
        
        @inlineCallbacks
        def init():
            channels = yield outputObject.vmp.sendCommand('get-channels')
            channelCheckBoxesGroup = QtGui.QButtonGroup()
            channelCheckBoxesGroup.isExclusiveToggle()
            channelCheckBoxes = []
            for i,channel in enumerate(channels):
                channelCheckBoxes[i] = QtGui.QCheckBox(channel)
                controlPanel.addRow(channelCheckBoxes[i])
                channelCheckBoxesGroup.addButton(channelCheckBoxes[i],i)
                
        '''       
        while True:
            output = yield self.outputObject.getOutput()
        '''    
            
    

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
    




#mod by stevens4 on 2013-06-08: made this return a voltmeterSTATSscanoutput instead for errorbars testing    
@inlineCallbacks
def getOutputObject(shotsToAvg=1):
    vmp = yield getProtocol(VOLTMETER_SERVER)
    channels = yield vmp.sendCommand('get-channels')
    channel = yield 'xtals power meter' #selectFromList(channels,'select default channel to monitor during scan')
    #returnValue(VoltMeterScanOutput(vmp,channel))
    returnValue(VoltMeterStatsScanOutput(vmp,channel,shotsToAvg))

@inlineCallbacks
def main():
    outputObject = yield getOutputObject()
    widget = TimeWidget(outputObject)
    widget.setWindowTitle('time gui')
    widget.show()

if __name__ == '__main__':
    main()
    reactor.run()
