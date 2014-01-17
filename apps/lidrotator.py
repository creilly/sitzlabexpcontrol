## BOILERPLATE ##
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:    
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install()
## BOILERPLATE ##
from twisted.internet.defer import inlineCallbacks
from steppermotor.steppermotorclient import ChunkedStepperMotorClient
from qtutils.label import LabelWidget
from qtutils.qled import LEDWidget
from operator import index
from sitz import compose
from ab.abclient import getProtocol
from functools import partial

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


PARAMS = {
    MIN:-999999,
    MAX:999999,
    PRECISION:0,
    SLIDER:200
}

RATE_MIN = 50.0
RATE_MAX = 1000.0
UPDATE_RATE = 10.0 # position updates per second

class LidRotatorWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.setLayout(QtGui.QVBoxLayout())
        self.resize(250, 275)
        self.enabled = False

        #@inlineCallbacks
        def onInit():
            
            #log position
            def logPosition(position,direction):
                if self.logfile is None: return
                timestamp = str(datetime.now())
                dirStr = {DigitalLineStepperMotor.FORWARDS:'FORWARDS',DigitalLineStepperMotor.BACKWARDS:'BACKWARDS'}[direction]
                logEntry = timestamp+'\t'+str(position)+'\t'+str(dirStr)+'\n'
                self.logfile.write(logEntry)
                print 'wrote to logfile: '+logEntry
            
            #send new position to stepper motor
            def onGotoRequested(position):
                debugSteps = 0
                def loop():
                    currPos = self.sm.getPosition()
                    #print 'error:\t%d' % debugSteps - currPos
                    lcd.display(currPos)
                    stepsPerChunk = int( self.sm.getStepRate() / UPDATE_RATE )
                    delta = position - currPos
                    if self.abort or delta == 0: 
                        logPosition(currPos,self.sm.getDirection())
                        goToggle.toggle()
                        return
                    if abs(delta) < stepsPerChunk:
                        debugSteps = position
                        self.sm.setPosition(
                            position,
                            loop
                        )
                    else:
                        debugSteps = (
                            currPos + (
                                1 if delta > 0 else -1
                            ) * stepsPerChunk
                        )
                        self.sm.setPosition(
                            currPos + (
                                1 if delta > 0 else -1
                            ) * stepsPerChunk,
                            loop
                        )                                    
                loop()
            
            self.show()
            
            #create an lcd & put at top
            lcd = self.lcd = QtGui.QLCDNumber(8)
            lcd.setSmallDecimalPoint(True)
            lcd.setSegmentStyle(lcd.Flat)
            self.lcdSetPosition = lcd.display
            self.layout().addWidget(lcd)
            
            def allSetEnabled(state):
                sputterRadioButton.setEnabled(state)
                scatterRadioButton.setEnabled(state)
                leedRadioButton.setEnabled(state)
                lipdRadioButton.setEnabled(state)
                customRadioButton.setEnabled(state)
                customSpinbox.setEnabled(state)
                goButton.setEnabled(state)
        
            # create enable/disable button
            def enableButtonFunc():
                if self.enabled:
                    # if already enabled, disable when clicked
                    print 'disabling...'
                    
                    # destroy stepper motor instance
                    self.sm.destroy()
                    
                    #close log
                    self.logfile.close()
                    
                    # turn relay off
                    self.relayTask.writeState(False)
                    
                    # disable all other gui items
                    allSetEnabled(False)
                    enableButton.setText('enable')
                    self.enabled = False
                    print 'disabled'
                    
                    return
                    
                if not self.enabled:
                    print 'starting...'
                    enableButton.setText('starting...')
                    
                    # write logic high to relay & wait for physical motor to start
                    relayChannel = LID_CONFIG['relay_channel'] if not DEBUG else DEBUG_LID_CONFIG['relay_channel']

                    self.relayTask = DOTask()
                    self.relayTask.createChannel(relayChannel)
                    self.relayTask.writeState(True)
                    
                    sleep(1)
                    print 'relay powered'
                    
                    #open logfile and read last values
                    logfilename = LID_CONFIG['logfile'] if not DEBUG else DEBUG_LID_CONFIG['logfile']
                    path = os.path.join(POOHDATAPATH,logfilename)
                    print path
                    self.logfile = open(path,'r+')
                    last_line = ''
                    for line in self.logfile: 
                        last_line = line
                    if not last_line: raise Exception('empty log file')
                    lastTime, lastPos, lastDir = last_line.strip().split('\t')
                    print 'loaded settings from ' + lastTime
                    lastPos = int(lastPos)
                    lastDir = {'FORWARDS':DigitalLineStepperMotor.FORWARDS,'BACKWARDS':DigitalLineStepperMotor.BACKWARDS}[lastDir]
                    lcd.display(lastPos)

                    # create stepper motor instance
                    if DEBUG:
                        self.sm = FakeStepperMotor(position=lastPos,rate=1000)
                    if not DEBUG:
                        self.sm = DigitalLineStepperMotor(
                            LID_CONFIG['step_channel'],
                            LID_CONFIG['counter_channel'],
                            LID_CONFIG['direction_channel'],
                            step_rate=LID_CONFIG['step_rate'],
                            initial_position=int(lastPos),
                            backlash=LID_CONFIG['backlash'],
                            direction=lastDir
                        )                        

                    #add to callback to disable cancel button & write to logfile
                    


                    
                    # enable all other gui items
                    allSetEnabled(True)
                    enableButton.setText('disable')
                    self.enabled = True
                    print 'enabled'
                    return

            enableButton = QtGui.QPushButton('enable', self)
            enableButton.clicked.connect(enableButtonFunc)
            self.layout().addWidget(enableButton)
            
            # create radio buttons for predefined positions
            radioButtonsGroup = QtGui.QButtonGroup()
            
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
                print 'going to ' +str(requestedPosition)
                
                onGotoRequested(requestedPosition)
                
                
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
            customSpinbox.setMinimum(PARAMS[MIN])
            customSpinbox.setMaximum(PARAMS[MAX])
            customSpinbox.setSingleStep(10 ** (-1 * PARAMS[PRECISION]))
            customButtonLayout.addWidget(customSpinbox)
            
            self.layout().addLayout(customButtonLayout)
            
            def start():
                self.abort = False
                goToggle.toggle()
            
            def goCancel():
                print 'aborting!'
                self.abort = True
                goToggle.toggle()
           
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
        if self.enabled:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("You must disable the motor first!")
            msgBox.exec_()
            event.ignore()
        if not self.enabled:
            event.accept()
        


        
        
#@inlineCallbacks
def main(container):
    widget = LidRotatorWidget()
    container.append(widget)    
    widget.setWindowTitle('lid client ' + ('debug' if DEBUG else 'real'))

if __name__ == '__main__':
    from twisted.internet import reactor
    container = []
    main(container)
    reactor.run()
