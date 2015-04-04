## BOILERPLATE ##
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:    
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install()
## BOILERPLATE ##
from goto import MIN, MAX, PRECISION, SLIDER, POI, GotoWidget
from config.steppermotor import POL, SM_CONFIG
from qtutils.label import LabelWidget
from steppermotorclient import StepperMotorClient
from polarizerclient import PolarizerClient
from twisted.internet.defer  import Deferred, inlineCallbacks, returnValue
from functools import partial
from config.serverURLs import POLARIZER_SERVER, TEST_POLARIZER_SERVER, STEPPER_MOTOR_SERVER, TEST_STEPPER_MOTOR_SERVER


class PolarizerWidget(QtGui.QWidget):
    def __init__(self,polarizerProtocol,stepperMotorProtocol):
        QtGui.QWidget.__init__(self)
        self.setLayout(QtGui.QVBoxLayout())
        self.polSMC = StepperMotorClient(stepperMotorProtocol,POL)
        
        gotoWidget = GotoWidget(
            {
                MIN:-360,
                MAX:360,
                PRECISION:.1,
                SLIDER:2,
                POI:{}
            }
        )
        self.layout().addWidget(LabelWidget('angle',gotoWidget))
        
        # send command to tracking server when goto requested
        @inlineCallbacks
        def onGotoRequested(payload):
            angle, deferred = payload
            yield polarizerProtocol.sendCommand('set-angle',angle)
            deferred.callback(None)
        gotoWidget.gotoRequested.connect(onGotoRequested)

        
        # handle update requests (should the position fall out of sync)
        def onUpdateReqested():
            polarizerProtocol.sendCommand('get-angle').addCallback(gotoWidget.setPosition)
        gotoWidget.updateRequested.connect(onUpdateReqested)
        
        
        # send cancel request when goto widget requests
        gotoWidget.cancelRequested.connect(partial(polarizerProtocol.sendCommand,'cancel-angle-set'))
        

        # set goto widget position on polarizer sm position change
        self.polSMC.addListener(
            self.polSMC.POSITION,
            lambda _:polarizerProtocol.sendCommand('get-angle').addCallback(gotoWidget.setPosition)
        )

        # initialize position of goto widget
        polarizerProtocol.sendCommand('get-angle').addCallback(gotoWidget.setPosition)
        

        # add enable button to toggle state of sm
        enableButton = QtGui.QPushButton('enable', self)
        enableButton.clicked.connect(self.polSMC.toggleStatus)
        def adjustEnbStatus(status):
            if status == 'enabled': 
                enableButton.setText('disable')
                gotoWidget.setEnabled(True)
            elif status == 'disabled': 
                enableButton.setText('enable')
                gotoWidget.setEnabled(False)
        self.polSMC.addListener(self.polSMC.ENABLE,adjustEnbStatus)
        self.layout().addWidget(enableButton)

    def closeEvent(self, event):
        event.accept()
        quit()
        
        
@inlineCallbacks
def main():
    import sys
    from ab.abclient import getProtocol
    DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'
    polarizerProtocol = yield getProtocol(
        TEST_POLARIZER_SERVER if DEBUG else POLARIZER_SERVER
    )
    stepperMotorProtocol = yield getProtocol(
        TEST_STEPPER_MOTOR_SERVER if DEBUG else STEPPER_MOTOR_SERVER
    )
    #memory management nonsense
    container.append(PolarizerWidget(polarizerProtocol,stepperMotorProtocol))
    container[0].show()
    container[0].setWindowTitle('polarizer client ' + ('debug ' if DEBUG else 'real '))
    

if __name__ == '__main__':
    from twisted.internet import reactor
    container = []
    main()
    reactor.run()
