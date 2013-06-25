## BOILERPLATE ##
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:    
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install()
## BOILERPLATE ##

from twisted.internet.defer import inlineCallbacks

from qtutils.toggle import ToggleWidget, ToggleObject
from ab.abbase import sleep
from functools import partial

from sitz import compose

from steppermotorclient import ChunkedStepperMotorClient

MIN = -99999
MAX = 99999
UPDATE = 300
WARN = 1000
GOTO_MAX = 250
SLIDER_RANGE = 200
RATE_MIN = 20
RATE_MAX = 1000

class StepperMotorWidget(QtGui.QWidget):
    NUDGE = .3
    def __init__(self,client):
        QtGui.QWidget.__init__(self)
        layout = QtGui.QFormLayout()
        
        ## LCD ##
        
        lcd = QtGui.QLCDNumber(6)
        lcd.setSegmentStyle(lcd.Flat)
        client.addListener(client.POSITION,lcd.display)

        layout.addRow('position',lcd)

        ## GOTO ##

        toggle = ToggleObject(False)

        spin = QtGui.QSpinBox()
        spin.setMinimum(MIN)
        spin.setMaximum(MAX)

        layout.addRow('goto',spin)

        gotoToggleWidget = ToggleWidget(toggle,('goto','stop'))
        layout.addRow(gotoToggleWidget)

        toggle.activationRequested.connect(toggle.toggle)
        
        @inlineCallbacks
        def onActivated():
            yield client.setPosition(spin.value())
            toggle.toggle()

        toggle.activated.connect(onActivated)

        toggle.deactivationRequested.connect(client.cancel)

        ## SLIDER ##
        slider = QtGui.QSlider()
        slider.setMinimum(-100)
        slider.setMaximum(100)
        slider.setOrientation(QtCore.Qt.Horizontal)
        slider.setTickInterval(25)
        slider.setTickPosition(slider.TicksBelow)
        slider.sliderPressed.connect(partial(self.nudgeLoop,slider,client))
        slider.sliderPressed.connect(partial(gotoToggleWidget.setEnabled,False))
        
        slider.sliderReleased.connect(partial(slider.setValue,0))
        slider.sliderReleased.connect(partial(gotoToggleWidget.setEnabled,True))

        toggle.activated.connect(partial(slider.setEnabled,False))
        toggle.deactivated.connect(partial(slider.setEnabled,True))

        layout.addRow(slider)

        ## STEPPING RATE ##

        rateSpin = QtGui.QSpinBox()
        layout.addRow('stepping rate',rateSpin)

        @inlineCallbacks
        def init():
            position = yield client.getPosition()
            lcd.display(position)
            rate = yield client.getStepRate()
            rate = int(rate)
            rateSpin.setRange(RATE_MIN if RATE_MIN < rate else rate,RATE_MAX if RATE_MAX > rate else rate)
            rateSpin.setValue(rate)
            rateSpin.editingFinished.connect(
                compose(                
                    client.setStepRate,
                    rateSpin.value
                )
            )
            client.addListener(
                client.RATE,
                compose(
                    rateSpin.setValue,
                    int
                )
            )
        init()
        self.setLayout(layout)

    # HACK: THIS WILL CRASH UNLESS IT IS AN INSTANCE METHOD (CAN'T BE A REGULAR FUNCTION) (WEIIIIIIIIIRD)
    @inlineCallbacks
    def nudgeLoop(self,slider,client):
        delta = slider.value()
        if delta:
            delta = int(delta / abs(delta) * pow(SLIDER_RANGE,(float(abs(delta))-1.0)/99.0))
            position = yield client.getPosition()
            yield client.setPosition(position + delta)
        yield sleep(self.NUDGE)
        if slider.isSliderDown():
            yield self.nudgeLoop(slider,client)
        
@inlineCallbacks
def main(container):
    # check if debugging / testing
    import sys
    debug = len(sys.argv) > 1 and sys.argv[1] == 'debug'

    # initialize widget
    widget = QtGui.QWidget()
    container.append(widget)
    widget.show()
    widget.setWindowTitle('%s stepper motor client' % ('debug' if debug else 'real'))

    layout = QtGui.QHBoxLayout()
    widget.setLayout(layout)

    from sitz import STEPPER_MOTOR_SERVER, TEST_STEPPER_MOTOR_SERVER
    from ab.abclient import getProtocol
    protocol = yield getProtocol(
        TEST_STEPPER_MOTOR_SERVER
        if debug else
        STEPPER_MOTOR_SERVER
    )

    config = yield protocol.sendCommand('get-configuration')
    for id in config.keys():
        groupBox = QtGui.QGroupBox(config[id]['name'])
        gLayout = QtGui.QVBoxLayout()
        groupBox.setLayout(gLayout)
        gLayout.addWidget(
            StepperMotorWidget(
                ChunkedStepperMotorClient(
                    protocol,
                    id
                )
            )
        )
        layout.addWidget(groupBox)

    def onConnectionLost(reason):
        if reactor.running: 
            QtGui.QMessageBox.information(widget,'connection lost','connect to server terminated. program quitting.')
            widget.close()
            reactor.stop()
            protocol.__class__.connectionLost(protocol,reason)

    protocol.connectionLost = onConnectionLost

if __name__ == '__main__':
    from twisted.internet import reactor
    container = []
    main(container)
    reactor.run()
