## BOILERPLATE ##
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:    
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install()
## BOILERPLATE ##
from twisted.internet.defer import inlineCallbacks
from qtutils.label import LabelWidget
from qtutils.qled import LEDWidget
from operator import index
from sitz import compose
from sitz import DELAY_GENERATOR_SERVER, TEST_DELAY_GENERATOR_SERVER
from ab.abclient import getProtocol
from functools import partial
from config.delaygenerator import DEBUG_DG_CONFIG, DG_CONFIG
from delaygeneratorserver import MIN, MAX
from delaygeneratorclient import DelayGeneratorClient


import sys
print sys.argv
DEBUG = len(sys.argv) > 1 and 'debug' in sys.argv
LOCAL = len(sys.argv) > 1 and 'local' in sys.argv
print 'debug: %s' % DEBUG
print 'local: %s' % LOCAL

import os
os.system("delay generator gui")


class DelayGeneratorWidget(QtGui.QWidget):
    def __init__(self,protocol):
        QtGui.QWidget.__init__(self)
        self.setLayout(QtGui.QVBoxLayout())
        self.resize(700, 500)
        self.lcdPositions = {}
        self.spinboxes = {}
        self.commitButtons = {}
        self.overrideBoxes = {}
        self.errPop = None

        def updateLCD(payload):
            dgName, newValue = payload
            lcdUpdate = self.lcdPositions[dgName]
            lcdUpdate(newValue)
        
        def errorPop(payload):
            dgName, error = payload
            lcdUpdate = self.lcdPositions[dgName]
            lcdUpdate("Err")
            msgBox = QtGui.QMessageBox()
            msgBox.setText(dgName+' '+error)
            msgBox.exec_()
        
        @inlineCallbacks
        def onInit():
            #query the delay generator server for active delay gens
            self.dgClient = DelayGeneratorClient(protocol)
            self.dgClient.setDelayListener(updateLCD)
            self.dgClient.setErrorListener(errorPop)
            config = yield self.dgClient.getDelays()
            self.show()

            #sort the list of dgNames based on guiOrder key in config
            sorted_dgs = list()
            for dgName in config.keys():
                if DEBUG:
                    sorted_dgs.append((dgName,DEBUG_DG_CONFIG[dgName]['guiOrder'],config[dgName]))
                else:
                    sorted_dgs.append((dgName,DG_CONFIG[dgName]['guiOrder'],config[dgName]))
            sorted_dgs = sorted(sorted_dgs, key=lambda x:x[1])

            #create a horizontal layout for each dg (thisLayout), when done add them to the full layout (self.layout())
            for dgName, guiOrder, delay in sorted_dgs:
                thisLayout = QtGui.QHBoxLayout()
                controlsLayout = QtGui.QVBoxLayout()
                
                #create a label
                if DEBUG:
                    partnerName = DEBUG_DG_CONFIG[dgName]['partner']
                    partnerDelay = DEBUG_DG_CONFIG[dgName]['rel_part_delay']
                else:
                    partnerName = DG_CONFIG[dgName]['partner']
                    partnerDelay = DG_CONFIG[dgName]['rel_part_delay']
                
                if partnerName == None:
                    thisLabel = QtGui.QLabel(dgName)
                else:                
                    thisLabel = QtGui.QLabel(dgName+':\n    partner: '+str(partnerName)+' @ '+str(partnerDelay))
                controlsLayout.addWidget(thisLabel)
                
                gotoLayout = QtGui.QHBoxLayout()

                
                #create a spinbox
                thisSpinbox = QtGui.QSpinBox()
                thisSpinbox.setMinimum(MIN)
                thisSpinbox.setMaximum(MAX)
                thisSpinbox.setSingleStep(10 ** (-1 * 0))
                thisSpinbox.setValue(delay)
                self.spinboxes[dgName] = thisSpinbox
                gotoLayout.addWidget(thisSpinbox)

                def writeDelay():
                    for dg, button in self.commitButtons.items():
                        if button.isChecked():
                            dgToWrite = dg
                    valueToWrite = int(self.spinboxes[dgToWrite].cleanText())
                    self.dgClient.setPartnerDelay(dgToWrite,valueToWrite)
                    self.commitButtons[dgToWrite].setChecked(False)
                
                #create a commit button
                thisCommitButton = QtGui.QPushButton('write delay')
                thisCommitButton.setCheckable(True)
                self.commitButtons[dgName] = thisCommitButton
                thisCommitButton.clicked.connect(writeDelay)
                gotoLayout.addWidget(thisCommitButton)
                
                def toggleOverride():
                    for dgName, override in self.overrideBoxes.items():
                        if override.isChecked():
                            self.dgClient.enablePartner(dgName,False)
                        elif not override.isChecked():
                            self.dgClient.enablePartner(dgName,True)
                
                #create partner override checkbox but lock it out if there isn't a partner
                thisOverride = QtGui.QCheckBox("override partner")
                thisOverride.stateChanged.connect(toggleOverride)
                self.overrideBoxes[dgName] = thisOverride
                gotoLayout.addWidget(thisOverride)
                if partnerName == None:
                    self.overrideBoxes[dgName].setCheckState(QtCore.Qt.Checked)
                    self.overrideBoxes[dgName].setVisible(False)
                controlsLayout.addLayout(gotoLayout)
                thisLayout.addLayout(controlsLayout)
                
                #create an lcd 
                lcd = thisLCD = QtGui.QLCDNumber(10)
                thisLCD.setSmallDecimalPoint(True)
                thisLCD.setSegmentStyle(lcd.Flat)
                self.lcdPositions[dgName] = thisLCD.display
                updateLCD((dgName,delay))
                thisLayout.addWidget(thisLCD)

                self.layout().addLayout(thisLayout)

        onInit()
        
    def closeEvent(self, event):
        self.dgClient.removeDelayListener()
        if reactor.running: reactor.stop()
        event.accept()
        
@inlineCallbacks
def main(container):
    protocol = yield getProtocol(
        TEST_DELAY_GENERATOR_SERVER
        if LOCAL else
        DELAY_GENERATOR_SERVER
    )
    widget = DelayGeneratorWidget(protocol)
    container.append(widget)
    widget.setWindowTitle('delay generator client ' + ('debug ' if DEBUG else 'real ') + ('local' if LOCAL else 'sitz lab'))

if __name__ == '__main__':
    from twisted.internet import reactor
    container = []
    main(container)
    reactor.run()
