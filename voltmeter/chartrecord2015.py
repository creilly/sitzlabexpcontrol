#this must be run first before importing the alternate reactor to avoid a 
#conflict between the qt and twisted reactors
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install() 

# server calls
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from ab.abclient import getProtocol
from ab.abbase import selectFromList, sleep

# voltmeter client
from voltmeter.voltmeterclient import VoltMeterClient

# configuration parameters
from config.voltmeter import VM_SERVER_CONFIG
from config.filecreation import POOHDATAPATH

# base voltmeter functionality (for configuring channel parameters)
from daqmx.task.ai import VoltMeter as VM

# custom GUI libraries
from qtutils.toggle import ToggleObject, ToggleWidget
from qtutils.label import LabelWidget

# math libraries
import numpy as np
from math import log10

# plotting
import pyqtgraph as pg

# function manipulators for easier GUI programming
from sitz import compose
from functools import partial

# logging
import os.path
from filecreationmethods import filenameGen, checkPath
import time
import datetime

# regular expressions
import re

# python types
from types import *


####################
#
# WARNING:
#
# if the voltmeter is unable to
# set a parameter to the requested
# value, an error will print to
# the server's log with no further
# action. reload a fresh edit
# dialog to see the current channel
# parameter settings
#
####################



    # define GUI as plot on left with a control panel on the right
# define channel A & B
    # get voltages for channel A & B
    # plot B vs A

    # save button
    # spinbox: binning value (resolution on A)
    # spinbox: number of measurements of B to keep in average


# defines the main window of the program which is a plotter with a control panel        
class ChartRecordWidget(QtGui.QWidget):                   
    def __init__(self,vmClient):
        self.history = []
        self.data = {}
        # integerBinNumber: [ (binMin, binMax), xValue, yList]
        
        ############################################CHANNELS DEFINED HERE#########################
        chanA = "Dev1/ai15"
        chanB = "Dev1/ai6"
        self.numAvg = 10
        
        @inlineCallbacks
        def init():
            # define overall layout: graph to left of control panel
            QtGui.QWidget.__init__(self)
            self.layout = QtGui.QHBoxLayout()
            self.setLayout(self.layout)
            
            # define plot
            plotWidget = pg.PlotWidget()
            self.plot = pg.PlotDataItem([0],[0])
            plotWidget.addItem(self.plot)
            self.layout.addWidget(plotWidget,1)
            
            # define controls panel
            controlsLayout = QtGui.QVBoxLayout()
            self.layout.addLayout(controlsLayout)
            
            # set up binning function and spinbox
            @inlineCallbacks
            def getRange():
                from daqmx.task.ai import VoltMeter as VM
                rangeKey = VM.PARAMETERS[2][0]
                setRangeKey = yield vmClient.getChannelParameter(chanA,rangeKey)
                vRange = VM.VOLTAGE_RANGES[setRangeKey][1]
                returnValue(vRange)
            
            @inlineCallbacks
            def updateBins():
                self.data = {}
                self.binSize = binSpin.value()
                vRange = yield getRange()
                self.numBins = 2*int(vRange/self.binSize)
                for i in range(self.numBins):
                    binMin = -1.*vRange + i*self.binSize
                    binMax = binMin + self.binSize
                    xValue = binMin + .5*self.binSize
                    theseYVals = [0.]
                    if len(self.history) > 0:
                        for xVolt, yVolt in self.history:
                            if xVolt >= binMin and xVolt < binMax:
                                theseYVals.append(yVolt)
                    self.data[i] = ( (binMin, binMax), xValue, theseYVals )
                updatePlot()
            vRange = yield getRange()
            binMin = 2*int(vRange)/(2**12)
            
            binSpin = QtGui.QDoubleSpinBox()
            binSpin.setDecimals(3)
            binSpin.setMinimum(binMin)
            binSpin.setSingleStep(binMin)
            binSpin.setMaximum(10.)
            binSpin.setValue(1.)
            controlsLayout.addWidget(LabelWidget('binning',binSpin))
            binSpin.editingFinished.connect(updateBins)
            
            # set up averaging function and spinbox
            def updateAverage():
                self.numAvg = avgSpin.value()
            avgSpin = QtGui.QSpinBox()
            avgSpin.setRange(1,10000)
            avgSpin.setValue(10)
            controlsLayout.addWidget(LabelWidget('averaging',avgSpin))
            avgSpin.editingFinished.connect(updateAverage)
            
            # set up data saving capabilities
            saveLayout = QtGui.QVBoxLayout()
            def onSaveClicked():
                xVals = []
                yVals = []
                yErr = []
                for binRange, xValue, yList in self.data.values():
                    xVals.append(xValue)
                    yVals.append(np.mean(yList))
                    yErr.append(np.std(yList))
                
                dataArray = np.asarray(
                    [xVals,yVals,yErr],
                    dtype=np.dtype(np.float32)
                )
                
                date = datetime.datetime.now().strftime("%Y-%m-%d")
                time = datetime.datetime.now().strftime("%H%M")
                dir = os.path.join(
                    POOHDATAPATH,
                    date
                )
                
                if not os.path.exists(dir):
                    os.makedirs(dir)
                path = QtGui.QFileDialog.getExistingDirectory(
                    self,
                    'select filename', 
                    dir
                )
                if not path: return
                desc, valid = QtGui.QInputDialog.getText(
                    self,
                    'enter file description',
                    'description'
                )
                filename = '%s_%s.csv' % (time,desc) if valid else '%s.csv' % time 
                np.savetxt(
                    os.path.join(
                        path,
                        filename
                    ),
                    dataArray.transpose(),
                    delimiter=','
                )
            saveButton = QtGui.QPushButton('save')
            saveButton.clicked.connect(onSaveClicked)
            saveLayout.addWidget(saveButton)
            
            controlsLayout.addWidget(
                LabelWidget(
                    'save',
                    saveLayout
                )
            )
            
            # function to redraw the plot
            def updatePlot():
                xVals = []
                yVals = []
                for bins, xValue, yList in self.data.values():
                    xVals.append(xValue)
                    yVals.append(np.mean(yList))
                self.plot.setData(np.asarray(xVals), np.asarray(yVals))
            
            
            # the main execution loop
            yield updateBins()
            @inlineCallbacks
            def loop():
                # get latest values
                voltages = yield vmClient.getVoltages()
                xVolt = voltages[chanA]
                yVolt = voltages[chanB]
                
                callbackRate = yield vmClient.getCallbackRate()
                yield sleep(1.0 / callbackRate)
                
                # pop oldest value if history is too long, store latest value 
                #if len(self.history) > self.numAvg*self.numBins:
                #    self.history.pop(0)
                self.history.append( (xVolt, yVolt) )
                
                # sort new value into appropriate bin
                for binRange, xValue, yList in self.data.values():
                    if xVolt >= binRange[0] and xVolt < binRange[1]:
                        if len(yList) > self.numAvg:
                            yList.pop(0)
                        yList.append(yVolt)
                # update plot
                updatePlot()
                
                loop()
            loop()
        init()

    def closeEvent(self, event):
        event.accept()
        quit()


@inlineCallbacks
def main():
    URL = VM_SERVER_CONFIG['url']
    protocol = yield getProtocol(URL)
    vmClient = VoltMeterClient(protocol)
    widget = ChartRecordWidget(vmClient)
    container.append(widget)
    widget.show()
    widget.setWindowTitle('Chart Recorder 2015')

if __name__ == '__main__':
    container = []
    main()
    reactor.run()
