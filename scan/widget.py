from PySide import QtGui
from PySide.QtCore import Signal

from twisted.internet.defer import inlineCallbacks, Deferred
from qtutils.toggle import ToggleObject, ClosedToggle

from scan import Scan
"""

scan starts on emission of activated signal

upon completion of a scan step, a stepped signal is \
emitted with the data from that step in a tuple (input,output) \
form.  to get the next step of the scan, call the completeStep \
method.

to stop a scan, use requestToggle

plugs straightforwardly into a ToggleWidget

"""
class ScanToggleObject(ToggleObject):
    stepped = Signal(object)
    def __init__(self,input,output):
        ToggleObject.__init__(self,initialState=False)
        def callback(input,output):
            d = self._d = Deferred()
            self.stepped.emit((input,output))
            return d
        scan = Scan(input,output,callback)
        closedToggle = self.closedToggle = ClosedToggle(False)
        self.deactivationRequested.connect(closedToggle.requestToggle)
        self.activated.connect(closedToggle.requestToggle)
        @inlineCallbacks
        def onStart():
            yield scan.start()
            if closedToggle.isToggled(): closedToggle.requestToggle()
            self.toggle()
        closedToggle.activated.connect(onStart)

    def completeStep(self):
        self._d.callback(self.closedToggle.isToggled())

class IntervalScanInputWidget(QtGui.QWidget):
    START,STOP,STEP = 0,1,2
    PROPERTIES = (START,STOP,STEP)
    def __init__(self,intervalScanInput,defaults):
        QtGui.QWidget.__init__(self)
        self.input = intervalScanInput
        layout = QtGui.QFormLayout()
        for id in PROPERTIES:
            spin = QtGui.QSpinBox()
            spin.setRange(defaults[id])
            spin.valueChanged.connect(
                partial(
                    setattr,
                    intervalScanInput,
                    {
                        START:'start',
                        STOP:'stop',
                        STEP:'step'
                    }[id]
                )
            ),
            layout.addRow(
                {
                    START:'start',
                    STOP:'stop',
                    STEP:'step'
                }[id],
                spin
            )
            
def test():
    ## BOILERPLATE ##
    import sys
    from PySide import QtGui, QtCore
    if QtCore.QCoreApplication.instance() is None:
        app = QtGui.QApplication(sys.argv)
        import qt4reactor
        qt4reactor.install()
    ## BOILERPLATE ##

    widget = QtGui.QWidget()
    widget.show()
    
    layout = QtGui.QVBoxLayout()
    widget.setLayout(layout)

    # create a plot

    from pyqtgraph import PlotWidget

    plotWidget = PlotWidget()
    plot = plotWidget.plot()

    layout.addWidget(plotWidget)

    # create a scan toggle

    size = 200
    inputData = range(size)
    outputData = [(x/float(size))**2 - (x/float(size))**3 for x in inputData]
    def input(): return inputData.pop() if inputData else None
    def output(): return outputData.pop()
    scanToggle = ScanToggleObject(input,output)

    # not performing any setup, so go ahead and connect activation requests to toggle
    scanToggle.activationRequested.connect(scanToggle.toggle)

    # create a toggle widget

    from qtutils.toggle import ToggleWidget

    layout.addWidget(ToggleWidget(scanToggle))

    # handle the stepped signal
    x, y = [], []
    from ab.abbase import sleep
    @inlineCallbacks
    def onStepped(data):
        input, output = data
        x.append(input)
        y.append(output)
        plot.setData(x,y)
        yield sleep(.05)
        scanToggle.completeStep()
    scanToggle.stepped.connect(onStepped)

    def log(x): print x
    from functools import partial
    scanToggle.toggled.connect(partial(log,'toggled'))
    scanToggle.toggleRequested.connect(partial(log,'toggleRequested'))
    
    app.exec_()

if __name__ == '__main__':
    test()
    
        
    
    
    