## BOILERPLATE ##
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:    
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install()
## BOILERPLATE ##

from twisted.internet.defer import inlineCallbacks, returnValue

from abclient import getProtocol
from steppermotorserver import getStepperMotorOptions, getConfig

from utilwidgets import ToggleWidget, ToggleObject
from abbase import sleep
from functools import partial

from toggle import Looper, ToggleWidget

from sitz import compose

from steppermotorclient import StepperMotorClient

MIN = -99999
MAX = 99999
UPDATE = 300
WARN = 1000
GOTO_MAX = 250
SLIDER_RANGE = 200
RATE_MIN = 20
RATE_MAX = 1000

class StepperMotorWidget(QtGui.QWidget):
    
    def __init__(self,client):
        QtGui.QWidget.__init__(self)
        layout = QtGui.QFormLayout()
        
        ## LCD ##
        
        lcd = QtGui.QLCDNumber(6)
        lcd.setSegmentStyle(lcd.Flat)
        client.setPositionListener(lcd.display)

        layout.addRow('position',lcd)

        ## GOTO ##

        looper = Looper()
        
        spin = QtGui.QSpinBox()
        spin.setMinimum(MIN)
        spin.setMaximum(MAX)

        looper.toggled.connect(
            compose(
                spin.setDisabled,
                spin.isEnabled
            )
        )

        layout.addRow('goto',spin)

        gotoToggleWidget = ToggleWidget(looper,('goto','stop'))
        layout.addRow(gotoToggleWidget)

        @inlineCallbacks
        def onLoopRequested(loopRequest):
            current = yield client.getPosition()
            desired = spin.value()
            delta = desired - current
            if abs(delta) > GOTO_MAX:
                # sometimes hangs here (?)
                yield client.setPosition(current + delta / abs(delta) * GOTO_MAX)
                loopRequest.completeRequest(True)
            else:
                yield client.setPosition(desired)
                loopRequest.completeRequest(False)

        looper.activated.connect(looper.startLooping)        
        looper.loopRequested.connect(onLoopRequested)

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

        looper.activated.connect(partial(slider.setEnabled,False))
        looper.deactivated.connect(partial(slider.setEnabled,True))

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
            client.setRateListener(
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
        yield sleep(.300)
        if slider.isSliderDown():
            yield self.nudgeLoop(slider,client)
        
@inlineCallbacks
def main():
    options = yield getStepperMotorOptions()
    url = options['url']
    protocol = yield getProtocol(url)
    widget = StepperMotorWidget(
        StepperMotorClient(
            protocol
        )
    )
    consoleTitle = '(%s) sm gui' % options['name']
    import os    
    os.system('title %s' % consoleTitle)
    widget.setWindowTitle(options["name"]+"[*]")
    widget.show()

if __name__ == '__main__':
    from twisted.internet import reactor
    main()
    reactor.run()
