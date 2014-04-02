## BOILERPLATE ##
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:    
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install()
## BOILERPLATE ##
from steppermotor.steppermotor import DigitalLineStepperMotor, FakeStepperMotor
from config.lid import LID_POSITIONS, LID_CONFIG, DEBUG_LID_CONFIG
from time import sleep

from config.filecreation import POOHDATAPATH
from daqmx.task.do import DOTask
from steppermotor.goto import MIN, MAX, PRECISION, SLIDER, GotoWidget
import os
from qtutils.toggle import ToggleObject, ToggleWidget
from datetime import datetime


import sys
DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'


RATE_MIN = 1
RATE_MAX = 10000
UPDATE_RATE = 10.0 # position updates per second

class LidRotatorWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.setLayout(QtGui.QVBoxLayout())
        self.resize(250, 275)
        
        def onInit():
            
            # create stepper motor instance
            if DEBUG:
                self.sm = FakeStepperMotor(rate=1000)
            if not DEBUG:
                self.sm = DigitalLineStepperMotor(
                    LID_CONFIG['step_channel'],
                    LID_CONFIG['counter_channel'],
                    LID_CONFIG['direction_channel'],
                    log_file=LID_CONFIG['logfile'],
                    enable_channel=LID_CONFIG['relay_channel'],
                    step_rate=LID_CONFIG['step_rate'],
                    backlash=LID_CONFIG['backlash']
                    )
            
            #send new position to stepper motor, this is a chunking method so the user can cancel mid-trip
            def onGotoRequested(position):
                enableButton.setEnabled(False)
                stepsPerChunk = int( self.sm.getStepRate() / UPDATE_RATE )
                def testDone():
                    currPos = self.sm.getPosition()
                    lcd.display(currPos)
                    delta = position - currPos
                    if delta == 0 or self.abort: 
                        goToggle.toggle()
                        enableButton.setEnabled(True)
                        return
                    elif abs(delta) < stepsPerChunk:
                        self.sm.setPosition(position,testDone)
                    else: 
                        goto = currPos + stepsPerChunk*(1 if delta > 0 else -1)
                        chunking(goto) #this looks sloppy but is necessary to not overload the threading that occurs
                    
                def chunking(goto):
                    self.sm.setPosition(goto,testDone)                                
                testDone()

            self.show()
            
            #create an lcd & put at top
            lcd = self.lcd = QtGui.QLCDNumber(8)
            lcd.setSmallDecimalPoint(True)
            lcd.setSegmentStyle(lcd.Flat)
            self.lcdSetPosition = lcd.display
            self.layout().addWidget(lcd)
            
            #show the first position on the lcd
            pos = self.sm.getPosition()
            lcd.display(pos)
            
            def allSetEnabled(state):
                sputterRadioButton.setEnabled(state)
                scatterRadioButton.setEnabled(state)
                leedRadioButton.setEnabled(state)
                lipdRadioButton.setEnabled(state)
                customRadioButton.setEnabled(state)
                customSpinbox.setEnabled(state)
                goButton.setEnabled(state)
                self.sm._setEnableStatus(state)
        
            # create enable/disable button
            def enableButtonFunc():
                if self.sm.getEnableStatus() == 'enabled':
                    allSetEnabled(False)
                    enableButton.setText('enable')
                    return
                    
                elif self.sm.getEnableStatus() == 'disabled':
                    allSetEnabled(True)
                    enableButton.setText('disable')
                    return

            enableButton = QtGui.QPushButton('enable', self)
            enableButton.clicked.connect(enableButtonFunc)
            self.layout().addWidget(enableButton)
            
            def findActiveButton():
                #determine selected button & look up position from definedPositions
                selectedButtonID = radioButtonsGroup.id(radioButtonsGroup.checkedButton())
                if selectedButtonID in (SPUTTER_ID, SCATTER_ID, LEED_ID, LIPD_ID):
                    requestedPosition = LID_POSITIONS[
                        {
                            SPUTTER_ID:'sputter', SCATTER_ID:'scatter', LEED_ID:'LEED', LIPD_ID:'LIPD'
                        }[selectedButtonID]
                    ]
                elif selectedButtonID is CUSTOM_ID:
                    requestedPosition = customSpinbox.value()
                else: return
                
                #go to that position
                onGotoRequested(requestedPosition)
                
            # create radio buttons for predefined positions
            radioButtonsGroup = QtGui.QButtonGroup()
            SPUTTER_ID, SCATTER_ID, LEED_ID, LIPD_ID, CUSTOM_ID = range(5)
            
            sputterRadioButton = QtGui.QRadioButton('sputter ('+str(LID_POSITIONS['sputter'])+')')
            radioButtonsGroup.addButton(sputterRadioButton,SPUTTER_ID)
            self.layout().addWidget(sputterRadioButton)
            
            scatterRadioButton = QtGui.QRadioButton('scatter ('+str(LID_POSITIONS['scatter'])+')')
            radioButtonsGroup.addButton(scatterRadioButton,SCATTER_ID)
            self.layout().addWidget(scatterRadioButton)
            
            leedRadioButton = QtGui.QRadioButton('LEED ('+str(LID_POSITIONS['LEED'])+')')
            radioButtonsGroup.addButton(leedRadioButton,LEED_ID)
            self.layout().addWidget(leedRadioButton)
            
            lipdRadioButton = QtGui.QRadioButton('LIPD ('+str(LID_POSITIONS['LIPD'])+')')
            radioButtonsGroup.addButton(lipdRadioButton,LIPD_ID)
            self.layout().addWidget(lipdRadioButton)
            
            customButtonLayout = QtGui.QHBoxLayout()
            
            customRadioButton = QtGui.QRadioButton('custom: ')
            radioButtonsGroup.addButton(customRadioButton,CUSTOM_ID)
            customButtonLayout.addWidget(customRadioButton)
            
            customSpinbox = QtGui.QSpinBox()
            customSpinbox.setMinimum(LID_POSITIONS['minimum'])
            customSpinbox.setMaximum(LID_POSITIONS['maximum'])
            customSpinbox.setSingleStep(1)
            customButtonLayout.addWidget(customSpinbox)
            
            self.layout().addLayout(customButtonLayout)
            
            def start():
                self.abort = False
                goToggle.toggle()
            
            def goCancel():
                print 'aborting!'
                self.abort = True
           
            goToggle = ToggleObject()
            goToggle.activationRequested.connect(start)
            goToggle.activated.connect(findActiveButton)
            goToggle.deactivationRequested.connect(goCancel)
            
            goButton = ToggleWidget(goToggle,('go','abort'))
            goButton.setEnabled(False)
            self.layout().addWidget(goButton)

            allSetEnabled(False)
            
        onInit()
        
    def closeEvent(self, event):
        if self.sm.getEnableStatus() == 'enabled':
            msgBox = QtGui.QMessageBox()
            msgBox.setText("You must disable the motor first!")
            msgBox.exec_()
            event.ignore()
        else:
            event.accept()
            self.sm.destroy()
            quit()
        

def main(container):
    widget = LidRotatorWidget()
    container.append(widget)    
    widget.setWindowTitle('lid client ' + ('debug' if DEBUG else 'real'))

if __name__ == '__main__':
    from twisted.internet import reactor
    container = []
    main(container)
    reactor.run()
