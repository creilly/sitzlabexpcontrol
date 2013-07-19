#this must be run first before importing the alternate reactor to avoid a 
#conflict between the qt and twisted reactors
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install() 
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from ab.abclient import getProtocol
from config.voltmeter import VM_SERVER_CONFIG, VM_DEBUG_SERVER_CONFIG
from sitz import compose
from time import clock
from ab.abbase import selectFromList, sleep
from functools import partial
from pyqtgraph import PlotWidget
import os.path
from config.filecreation import POOHDATAPATH
from filecreationmethods import filenameGen, checkPath
import csv
import datetime

DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'
URL = (VM_DEBUG_SERVER_CONFIG if DEBUG else VM_SERVER_CONFIG)['url']
MAX = 200
SLEEP = .1

class VoltMeterWidget(QtGui.QWidget):
    def __init__(self,protocol):
        QtGui.QWidget.__init__(self)
        self.setLayout(QtGui.QVBoxLayout())
        plotter = PlotWidget()
        self.plot = plotter.plot()
        self.layout().addWidget(plotter,1)
        self.filename = None
        self.fileObj = None
        
        voltages = [0] * MAX
        
        def onVoltagesAcquired(data):
            datum = data[self.channel] *1000
            lcd.display(datum)
            voltages.pop(0)
            voltages.append(datum)
            self.plot.setData(range(len(voltages)),voltages)
            if self.filename is not None:
                timeStamp = datetime.datetime.now() - self.startTime
                timeStampStr = str(timeStamp.seconds)+'.'+str(timeStamp.microseconds/1000).zfill(3)
                csvLine = timeStampStr+','+str(datum)+'\n'
                self.fileObj.write(csvLine)


        controlPanel = QtGui.QHBoxLayout()
        controlPanel.addStretch(1)

        vmCombo = QtGui.QComboBox()
        vmCombo.currentIndexChanged[unicode].connect(
            partial(setattr,self,'channel')
        )
        vmCombo.setCurrentIndex(0)
        protocol.sendCommand('get-channels').addCallback(vmCombo.addItems)

        controlPanel.addWidget(vmCombo)

        def recButFunc():
            #if filename isn't set, initialize a file and filewriter to write to
            if self.filename == None:
                vmName = vmCombo.currentText()
                subfolder = os.path.join('voltmeterLog',vmName)
                relPath, self.filename = filenameGen(subfolder)
                absPath = os.path.join(POOHDATAPATH,relPath)
                checkPath(absPath)
                self.filename = os.path.join(absPath,self.filename+'.csv')
                self.fileObj = open(self.filename, 'wb')
                self.startTime = datetime.datetime.now()
                recordButton.setText('logging...')
            #if there is a filename, close the file and set filename to none
            else:
                self.filename = None
                self.fileObj.close()
                recordButton.setText('start log')
                
        recordButton = QtGui.QPushButton('log')
        recordButton.clicked.connect(recButFunc)
        controlPanel.addWidget(recordButton)

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
    container.append(widget)
    widget.show()

if __name__ == '__main__':
    container = []
    main()
    reactor.run()
