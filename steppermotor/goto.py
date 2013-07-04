## BOILERPLATE ##
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:    
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install()
## BOILERPLATE ##
from PySide.QtCore import Signal

from twisted.internet.defer import inlineCallbacks, Deferred

from qtutils.toggle import ToggleWidget, ToggleObject
from ab.abbase import sleep
from functools import partial
from sitz import compose

'''

general widget for controlling the position of something. \
users request position changes by specifying a position with \
the goto button/spin combo, or by tugging a slider.

to use the widget, connect to the gotoRequested((@position,@deferred)) \
signal, setting the specified @position and firing the @deferred \
(passing None) when finished.

in order for the slider to work properly it is necessary to update the \
widget with the current position.

The user can also cancel the goto request. manage this request by connecting \
to the cancelRequested signal.

'''
MIN, MAX, PRECISION, SLIDER = 0,1,2,3
class GotoWidget(QtGui.QWidget):
    gotoRequested = Signal(object)
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
        
        lcd = self.lcd = QtGui.QLCDNumber(8)
        lcd.setSegmentStyle(lcd.Flat)
        self.setPosition = lcd.display

        layout.addRow('position',lcd)

        ## GOTO ##

        toggle = ToggleObject(False)

        spin = QtGui.QDoubleSpinBox()
        spin.setMinimum(params[MIN])
        spin.setMaximum(params[MAX])
        spin.setSingleStep(10 ** (-1 * params[PRECISION]))
        spin.setDecimals(params[PRECISION])

        layout.addRow('goto',spin)

        gotoToggleWidget = ToggleWidget(toggle,('goto','stop'))
        layout.addRow(gotoToggleWidget)

        toggle.activationRequested.connect(toggle.toggle)
        @inlineCallbacks
        def onActivated():
            d = Deferred()
            self.gotoRequested.emit((spin.value(),d))
            yield d
            toggle.toggle()
        toggle.activated.connect(onActivated)
        toggle.deactivationRequested.connect(self.cancelRequested.emit)

        ## SLIDER ##
        slider = QtGui.QSlider()
        @inlineCallbacks
        def nudgeLoop():
            delta = slider.value()
            if delta:
                delta = int(delta / abs(delta) * pow(params[SLIDER],(float(abs(delta))-1.0)/99.0))
                d = Deferred()
                print lcd.value()
                self.gotoRequested.emit((lcd.value()+delta,d))
                yield d
            yield sleep(self.NUDGE)
            if slider.isSliderDown():
                yield nudgeLoop()
            else:
                self.cancelRequested.emit()
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
