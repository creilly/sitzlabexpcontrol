## BOILERPLATE ##
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:    
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install()
## BOILERPLATE ##
from twisted.internet.defer import inlineCallbacks
from steppermotorclient import ChunkedStepperMotorClient
from goto import MIN, MAX, PRECISION, SLIDER, GotoWidget
from qtutils.label import LabelWidget
from qtutils.qled import LEDWidget
from operator import index
from sitz import compose
from ab.abclient import getProtocol
from functools import partial

from config.lid import LID_POSITIONS
from time import sleep

PARAMS = {
    MIN:-99999,
    MAX:99999,
    PRECISION:0,
    SLIDER:200
}

RATE_MIN = 50.0
RATE_MAX = 1000.0

class LidRotatorWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.setLayout(QtGui.QVBoxLayout())
        self.resize(250, 275)
        self.enabled = False

        #@inlineCallbacks
        def onInit():
            self.show()
            
            # create lcd display
            lcd = self.lcd = QtGui.QLCDNumber(8)
            lcd.setSmallDecimalPoint(True)
            lcd.setSegmentStyle(lcd.Flat)
            self.setPosition = lcd.display
            self.layout().addWidget(lcd)
            
            def allSetEnabled(state):
                sputterRadioButton.setEnabled(state)
                scatterRadioButton.setEnabled(state)
                leedRadioButton.setEnabled(state)
                lipdRadioButton.setEnabled(state)
                customRadioButton.setEnabled(state)
                customSpinbox.setEnabled(state)
                customCommitButton.setEnabled(state)
        
            # create enable/disable button
            def enableButtonFunc():
                if self.enabled:
                    # if already enabled, disable when clicked
                    # write counter status?
                    
                    # destroy stepper motor instance

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
                    sleep(1)
                    print 'started'
                    
                    # create stepper motor instance & load last position & direction from file
                    '''this section needs to be rewritten for the new sm
                    sm = ChunkedStepperMotorClient(protocol,id)   #replace with lid sm!!             
                    @inlineCallbacks
                    def onGotoRequested(sm,payload):
                        position, deferred = payload
                        print position
                        yield sm.setPosition(int(position))
                        deferred.callback(None)
                    gotoWidget.gotoRequested.connect(partial(onGotoRequested,sm))
                    gotoWidget.cancelRequested.connect(sm.cancel)
                    position = yield sm.getPosition()
                    gotoWidget.setPosition(position)
                    '''
                    
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
            
            def radioButtonFunc():
                #determine selected button & look up position from definedPositions
                selectedButton = radioButtonsGroup.checkedButton()
                print selectedButton.text()
                if (selectedButton.text() in LID_POSITIONS.keys()):
                    requestedPosition = LID_POSITIONS[selectedButton.text()]
                else:
                    requestedPosition = customSpinbox.value()
                
                
                #go to that position
                print 'going to ' +str(requestedPosition)
                
                
            sputterRadioButton = QtGui.QRadioButton('sputter ('+str(LID_POSITIONS['sputter'])+')')
            sputterRadioButton.clicked.connect(radioButtonFunc)
            radioButtonsGroup.addButton(sputterRadioButton)
            self.layout().addWidget(sputterRadioButton)
            
            scatterRadioButton = QtGui.QRadioButton('scatter ('+str(LID_POSITIONS['scatter'])+')')
            scatterRadioButton.clicked.connect(radioButtonFunc)
            radioButtonsGroup.addButton(scatterRadioButton)
            self.layout().addWidget(scatterRadioButton)
            
            leedRadioButton = QtGui.QRadioButton('LEED ('+str(LID_POSITIONS['LEED'])+')')
            leedRadioButton.clicked.connect(radioButtonFunc)
            radioButtonsGroup.addButton(leedRadioButton)
            self.layout().addWidget(leedRadioButton)
            
            lipdRadioButton = QtGui.QRadioButton('LIPD ('+str(LID_POSITIONS['LIPD'])+')')
            lipdRadioButton.clicked.connect(radioButtonFunc)
            radioButtonsGroup.addButton(lipdRadioButton)
            self.layout().addWidget(lipdRadioButton)
            
            customButtonLayout = QtGui.QHBoxLayout()
            
            customRadioButton = QtGui.QRadioButton('custom: ')
            radioButtonsGroup.addButton(customRadioButton)
            customButtonLayout.addWidget(customRadioButton)
            
            customSpinbox = QtGui.QSpinBox()
            customSpinbox.setMinimum(PARAMS[MIN])
            customSpinbox.setMaximum(PARAMS[MAX])
            customSpinbox.setSingleStep(10 ** (-1 * PARAMS[PRECISION]))
            customButtonLayout.addWidget(customSpinbox)
            
            customCommitButton = QtGui.QPushButton('go')
            customCommitButton.clicked.connect(radioButtonFunc)
            customButtonLayout.addWidget(customCommitButton)
            
            
            allSetEnabled(False)
            self.layout().addLayout(customButtonLayout)

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
    # check if debugging / testing
    import sys
    debug = len(sys.argv) > 1 and sys.argv[1] == 'debug'

    from sitz import STEPPER_MOTOR_SERVER, TEST_STEPPER_MOTOR_SERVER
    from ab.abclient import getProtocol
    '''
    protocol = yield getProtocol(
        TEST_STEPPER_MOTOR_SERVER
        if debug else
        STEPPER_MOTOR_SERVER
    )
    '''
    widget = LidRotatorWidget()
    container.append(widget)    
    widget.setWindowTitle('lid client ' + ('debug' if debug else 'real'))

if __name__ == '__main__':
    from twisted.internet import reactor
    container = []
    main(container)
    reactor.run()
