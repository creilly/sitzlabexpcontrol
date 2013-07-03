## BOILERPLATE ##
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:    
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install()
## BOILERPLATE ##
from PySide.QtCore import Signal

from twisted.internet.defer import inlineCallbacks

from qtutils.toggle import ToggleWidget, ToggleObject
from ab.abbase import sleep
from functools import partial

from sitz import compose

MIN, MAX, PRECISION, SLIDER = 0,1,2,3
class GotoWidget(QtGui.QWidget):
    gotoRequested = Signal(float)
    cancelRequested = Signal()
    NUDGE = .3
    def __init__(
            self,
            params = {
                MIN:0,
                MAX:100,
                PRECISION:0,
                SLIDER:20
            }
    ):
        QtGui.QWidget.__init__(self)
        layout = QtGui.QFormLayout()
        
        ## LCD ##
        
        lcd = self.lcd = QtGui.QLCDNumber(6)
        lcd.setSegmentStyle(lcd.Flat)
        self.setPosition = lcd.display

        layout.addRow('position',lcd)

        ## GOTO ##

        toggle = ToggleObject(False)

        spin = QtGui.QDoubleSpinBox()
        spin.setMinimum(params[MIN])
        spin.setMaximum(params[MAX])
        spin.setSingleStep(10 ** (-1 * params[PRECISION]))
        spin.setPrecision(params[PRECISION])

        layout.addRow('goto',spin)

        gotoToggleWidget = ToggleWidget(toggle,('goto','stop'))
        layout.addRow(gotoToggleWidget)

        toggle.activationRequested.connect(toggle.toggle)
        
        toggle.activated.connect(
            compose(
                self.gotoRequested.emit,
                spin.value
            )
        )

        toggle.deactivationRequested.connect(self.cancelRequested.emit)

        ## SLIDER ##
        slider = QtGui.QSlider()
        @inlineCallbacks
        def nudgeLoop():
            delta = slider.value()
            if delta:
                delta = int(delta / abs(delta) * pow(SLIDER_RANGE,(float(abs(delta))-1.0)/99.0))                
                yield self.gotoRequested(spin.value()+delta)
            yield sleep(self.NUDGE)
            if slider.isSliderDown():
                yield self.nudgeLoop()
        slider.setMinimum(-100)
        slider.setMaximum(100)
        slider.setOrientation(QtCore.Qt.Horizontal)
        slider.setTickInterval(25)
        slider.setTickPosition(slider.TicksBelow)
        slider.sliderPressed.connect(nudgeLoop)
        slider.sliderPressed.connect(partial(gotoToggleWidget.setEnabled,False))
        
        slider.sliderReleased.connect(partial(slider.setValue,0))
        slider.sliderReleased.connect(partial(gotoToggleWidget.setEnabled,True))

        toggle.activated.connect(partial(slider.setEnabled,False))
        toggle.deactivated.connect(partial(slider.setEnabled,True))

        layout.addRow(slider)

        self.setLayout(layout)
