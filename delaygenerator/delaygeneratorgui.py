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
DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'



class DelayGeneratorWidget(QtGui.QWidget):
    def __init__(self,protocol):
        QtGui.QWidget.__init__(self)
        self.setLayout(QtGui.QVBoxLayout())
        self.resize(700, 500)
        self.lcdPositions = {}
        self.spinboxes = {}
        self.commitButtons = {}
        self.overrideBoxes = {}

        '''
        def onConnectionLost(reason):
            if reactor.running: 
                QtGui.QMessageBox.information(self,'connection lost','connect to server terminated. program quitting.')
                self.close()
                reactor.stop()
                protocol.__class__.connectionLost(protocol,reason)
        protocol.connectionLost = onConnectionLost
        '''
        def updateLCD(payload):
            dgName, newValue = payload
            lcdUpdate = self.lcdPositions[dgName]
            lcdUpdate(newValue)
        
        @inlineCallbacks
        def onInit():
            #query the delay generator server for active delay gens
            self.dgClient = DelayGeneratorClient(protocol)
            self.dgClient.setDelayListener(updateLCD)
            config = yield self.dgClient.getDelays()
            
            self.show()
            
            print config
            
            #sort dictionary of dgs & delays for creating the GUI
            import operator
            sorted_dgs = sorted(config.iteritems(), key=operator.itemgetter(1))
            
            for dg, delay in sorted_dgs:
                thisLayout = QtGui.QHBoxLayout()
                controlsLayout = QtGui.QVBoxLayout()
                
                #create a label
                if DEBUG:
                    partnerName = DEBUG_DG_CONFIG[dg]['partner']
                    partnerDelay = DEBUG_DG_CONFIG[dg]['rel_part_delay']
                else:
                    partnerName = DG_CONFIG[dg]['partner']
                    partnerDelay = DG_CONFIG[dg]['rel_part_delay']
                
                
                thisLabel = QtGui.QLabel(dg+':\n    partner: '+str(partnerName)+' @ '+str(partnerDelay))
                controlsLayout.addWidget(thisLabel)
                
                gotoLayout = QtGui.QHBoxLayout()
                
                #create a spinbox
                thisSpinbox = QtGui.QSpinBox()
                thisSpinbox.setMinimum(MIN)
                thisSpinbox.setMaximum(MAX)
                thisSpinbox.setSingleStep(10 ** (-1 * 0))
                thisSpinbox.setValue(delay)
                self.spinboxes[dg] = thisSpinbox
                gotoLayout.addWidget(thisSpinbox)
                
                def writeDelay():
                    for dg, button in self.commitButtons.items():
                        if button.isChecked():
                            dgToWrite = dg
                    valueToWrite = int(self.spinboxes[dgToWrite].cleanText())
                    override = self.overrideBoxes[dgToWrite].checkState()
                    if override: 
                        print self.dgClient.setDelay(dgToWrite,valueToWrite)
                        self.dgClient.setDelay(dgToWrite,valueToWrite)
                    else: 
                        self.dgClient.setPartnerDelay(dgToWrite,valueToWrite)
                    self.commitButtons[dgToWrite].setChecked(False)
                    
                
                
                #create a commit button
                thisCommitButton = QtGui.QPushButton('write delay')
                thisCommitButton.setCheckable(True)
                #self.commitButtonsGroup.addButton(thisCommitButton,self.dgIDs[dg])
                self.commitButtons[dg] = thisCommitButton
                thisCommitButton.clicked.connect(writeDelay)
                gotoLayout.addWidget(thisCommitButton)
                
                #create partner override checkbox
                thisOverride = QtGui.QCheckBox("override partner")
                self.overrideBoxes[dg] = thisOverride
                gotoLayout.addWidget(thisOverride)
                
                controlsLayout.addLayout(gotoLayout)
                thisLayout.addLayout(controlsLayout)
                
                #create an lcd 
                lcd = thisLCD = QtGui.QLCDNumber(10)
                thisLCD.setSmallDecimalPoint(True)
                thisLCD.setSegmentStyle(lcd.Flat)
                self.lcdPositions[dg] = thisLCD.display
                updateLCD((dg,delay))
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
        if DEBUG else
        DELAY_GENERATOR_SERVER
    )
    widget = DelayGeneratorWidget(protocol)
    container.append(widget)
    widget.setWindowTitle('delay generator client ' + ('debug' if DEBUG else 'real'))

if __name__ == '__main__':
    from twisted.internet import reactor
    container = []
    main(container)
    reactor.run()
