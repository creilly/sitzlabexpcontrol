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
from goto import MIN, MAX, PRECISION, SLIDER, POI, GotoWidget
from qtutils.label import LabelWidget
from qtutils.qled import LEDWidget
from operator import index
from sitz import compose
from ab.abclient import getProtocol
from functools import partial

PARAMS = {
    MIN:-99999,
    MAX:99999,
    PRECISION:0,
    SLIDER:200,
    POI:{'none':0}
}

RATE_MIN = 1
RATE_MAX = 1000

class StepperMotorWidget(QtGui.QWidget):
    def __init__(self,protocol):
        QtGui.QWidget.__init__(self)
        self.setLayout(QtGui.QHBoxLayout())
        def onConnectionLost(reason):
            if reactor.running: 
                QtGui.QMessageBox.information(self,'connection lost','connect to server terminated. program quitting.')
                self.close()
                reactor.stop()
                protocol.__class__.connectionLost(protocol,reason)
        protocol.connectionLost = onConnectionLost
        
        self.gotoWids = {}
        self.enbButtons = {}
        self.sms = {}
        
        @inlineCallbacks
        def onInit():
            config = yield protocol.sendCommand('get-configuration')
            self.show()
            
            #sort the list of dgNames based on guiOrder key in config
            sorted_sms = list()
            for smName in config.keys():
                sorted_sms.append((smName,config[smName]['guiOrder'],config[smName]))
            sorted_sms = sorted(sorted_sms, key=lambda x:x[1])
            
            #create a vertical layout for each sm (thisLayout), when done add to the full horizontal layout (self.layout())
            for id, guiOrder, config in sorted_sms:
                thisLayout = QtGui.QVBoxLayout()
                
                sm = ChunkedStepperMotorClient(protocol,id)
                self.sms[id] = sm
                #create a goto widget for this steppermotor
                PARAMS[POI] = config['pts_of_int']
                gotoWidget = GotoWidget(PARAMS)
                self.gotoWids[sm.id] = gotoWidget
                thisLayout.addWidget(gotoWidget)
                @inlineCallbacks
                def onGotoRequested(sm,payload):
                    position, deferred = payload
                    yield sm.setPosition(int(position))
                    deferred.callback(None)
                gotoWidget.gotoRequested.connect(partial(onGotoRequested,sm))
                #gotoWidget.spin.editingFinished.connect(partial(onGotoRequested,sm))
                sm.addListener(sm.POSITION,gotoWidget.setPosition)
                def onUpdateRequested(stepperMotor,gw):
                    stepperMotor.getPosition().addCallback(gw.setPosition)
                gotoWidget.updateRequested.connect(partial(onUpdateRequested,sm,gotoWidget))
                gotoWidget.cancelRequested.connect(sm.cancel)
                position = yield sm.getPosition()
                gotoWidget.setPosition(position)

                #create an enable toggle button for this sm
                enableButton = QtGui.QPushButton('enable', self)
                self.enbButtons[sm.id] = enableButton
                enableButton.clicked.connect(sm.toggleStatus)
                #handle external application toggling this sm
                def adjustText(sm,status):
                    if status == 'enabled': 
                        self.enbButtons[sm.id].setText('disable')
                        self.gotoWids[sm.id].setEnabled(True)
                    elif status == 'disabled': 
                        self.enbButtons[sm.id].setText('enable')
                        self.gotoWids[sm.id].setEnabled(False)
                sm.addListener(sm.ENABLE,partial(adjustText,sm))
                
                #disable enable button if this sm doesn't have that functionality
                if config['enable_channel'] == None: enableButton.setEnabled(False)
                else: gotoWidget.setEnabled(False)
                thisLayout.addWidget(enableButton)
                
                #create a spinbox to control the step rate for this sm
                rate = yield sm.getStepRate()
                rateSpin = QtGui.QSpinBox()
                thisLayout.addWidget(LabelWidget('rate',rateSpin))
                rateSpin.editingFinished.connect(
                    compose(
                        sm.setStepRate,
                        rateSpin.value
                    )
                )
                rateSpin.setRange(
                    RATE_MIN if rate > RATE_MIN else rate,
                    RATE_MAX if rate < RATE_MAX else rate
                )
                rateSpin.setValue(rate)
                sm.addListener(sm.RATE,rateSpin.setValue)
                
                #add this steppermotor panel to the gui
                self.layout().addWidget(
                    LabelWidget(
                        config['name'],
                        thisLayout
                    )
                )
        onInit()
        
    def closeEvent(self, event):
        globalStatus = False
        for gotoWidget in self.gotoWids.values():
            thisStatus = gotoWidget.isEnabled()
            globalStatus = globalStatus or thisStatus
        if globalStatus:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("You must disable ALL motors first!")
            msgBox.exec_()
            event.ignore()
        else:
            event.accept()
            quit()
        
        
@inlineCallbacks
def main(container):
    # check if debugging / testing
    import sys
    debug = len(sys.argv) > 1 and sys.argv[1] == 'debug'

    from sitz import STEPPER_MOTOR_SERVER, TEST_STEPPER_MOTOR_SERVER
    from ab.abclient import getProtocol
    protocol = yield getProtocol(
        TEST_STEPPER_MOTOR_SERVER
        if debug else
        STEPPER_MOTOR_SERVER
    )
    widget = StepperMotorWidget(protocol)
    container.append(widget)    
    widget.setWindowTitle('%s stepper motor client' % ('debug' if debug else 'real'))    

if __name__ == '__main__':
    from twisted.internet import reactor
    container = []
    main(container)
    reactor.run()
