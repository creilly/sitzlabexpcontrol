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

PARAMS = {
    MIN:-99999,
    MAX:99999,
    PRECISION:0,
    SLIDER:200
}

RATE_MIN = 50.0
RATE_MAX = 1000.0

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
        @inlineCallbacks
        def onInit():
            config = yield protocol.sendCommand('get-configuration')
            self.show()
            for id in config.keys():
                layout = QtGui.QVBoxLayout()

                gotoWidget = GotoWidget(PARAMS)
                layout.addWidget(gotoWidget)
                sm = ChunkedStepperMotorClient(protocol,id)                
                @inlineCallbacks
                def onGotoRequested(sm,payload):
                    position, deferred = payload
                    print position
                    yield sm.setPosition(int(position))
                    deferred.callback(None)
                gotoWidget.gotoRequested.connect(partial(onGotoRequested,sm))
                sm.addListener(sm.POSITION,gotoWidget.setPosition)
                gotoWidget.cancelRequested.connect(sm.cancel)
                position = yield sm.getPosition()
                gotoWidget.setPosition(position)

                rate = yield sm.getStepRate()
                rateSpin = QtGui.QDoubleSpinBox()
                layout.addWidget(LabelWidget('rate',rateSpin))
                rateSpin.editingFinished.connect(
                    compose(
                        sm.setStepRate,
                        rateSpin.value
                    )
                )
                rateSpin.setValue(rate)
                rateSpin.setRange(
                    RATE_MIN if rate > RATE_MIN else rate,
                    RATE_MAX if rate < RATE_MAX else rate
                )
                sm.addListener(sm.RATE,rateSpin.setValue)
                self.layout().addWidget(
                    LabelWidget(
                        config[id]['name'],
                        layout
                    )
                )
        onInit()
        
        
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
