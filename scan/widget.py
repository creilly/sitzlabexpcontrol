from PySide import QtGui
from PySide import QtCore

from twisted.internet.defer import inlineCallbacks, Deferred
from qtutils.toggle import ToggleObject, ClosedToggle

from functools import partial

from sitz import compose

from scan import Scan

from input import IntervalScanInput, ListScanInput

from copy import copy

DEFAULTS = [(-50000,50000),(-50000,50000),(1,1000)]


'''
update on 2013/06/24 by stevens4: rectified language of IntervalScanInput \
such that first and last points are referred to as 'begin' and 'end' to \
avoid confusion with 'start' and 'stop' actions of a scan.


scan starts on emission of activated signal

upon completion of a scan step, a stepped signal is \
emitted with the data from that step in a tuple (input,output) \
form.  to get the next step of the scan, call the completeStep \
method.

to stop a scan, use requestToggle

plugs straightforwardly into a ToggleWidget

'''
class ScanToggleObject(ToggleObject):
    stepped = QtCore.Signal(object)
    def __init__(self):
        ToggleObject.__init__(self,initialState=False)
        def callback(input,output):
            d = self._d = Deferred()
            self.stepped.emit((input,output))
            return d
        closedToggle = self.closedToggle = ClosedToggle(False)
        self.deactivationRequested.connect(closedToggle.requestToggle)
        self.activated.connect(closedToggle.requestToggle)
        @inlineCallbacks
        def onStart():
            yield Scan(self.input,self.output,callback).start()
            if closedToggle.isToggled(): closedToggle.requestToggle()
            self.toggle()
        closedToggle.activated.connect(onStart)

    def completeStep(self):
        self._d.callback(self.closedToggle.isToggled())
        
    def setInput(self,input):
        self.input = input
        
    def setOutput(self,output):
        self.output = output
        
class IntervalScanInputWidget(QtGui.QWidget):
    START,STOP,STEP = 0,1,2
    NAME, ATTRIBUTE = 0,1
    MIN, MAX, PRECISION = 0,1,2
    PARAMETERS = (MIN,MAX,PRECISION)
    PROPERTIES = {
        START:{
            NAME: 'begin',
            ATTRIBUTE: 'start'
        },
        STOP:{
            NAME: 'end',
            ATTRIBUTE: 'stop'
        },
        STEP:{
            NAME: 'step',
            ATTRIBUTE: 'step'
        }
    }
    def __init__(self):
        QtGui.QWidget.__init__(self)
        layout = QtGui.QFormLayout()
        self.setLayout(layout)
        self.spins = {}
        for id in self.PROPERTIES:
            spin = QtGui.QDoubleSpinBox()
            spin.valueChanged.connect(
                partial(
                    setattr,
                    self,
                    self.PROPERTIES[id][self.ATTRIBUTE]
                )
            )
            setattr(self,self.PROPERTIES[id][self.ATTRIBUTE],spin.value())
            layout.addRow(
                self.PROPERTIES[id][self.NAME],
                spin
            )
            self.spins[id]=spin

    def setParameter(self,spinID,parameter,value):
        spin = self.spins[spinID]
        if parameter is self.PRECISION:
            spin.setSingleStep(10 ** (-1 * value))
            spin.setDecimals(value)
        else:
            getattr(
                spin,
                {
                    self.MIN:'setMinimum',
                    self.MAX:'setMaximum'
                }[parameter]
            )(value)
                               
    def getInput(self,agent):
        return IntervalScanInput(
            agent,
            **{
                attr:getattr(self,attr) for attr in (
                    d[self.ATTRIBUTE] for d in self.PROPERTIES.values()
                )
            }
        )

class ListScanInputWidget(QtGui.QWidget):
    def __init__(self,positions = None):
        QtGui.QWidget.__init__(self)
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)
        self.loadPosListButton = QtGui.QPushButton('load queue')
        self.loadPosListButton.clicked.connect(
            compose(
                self.setPositions,
                self.loadPositions
            )
        )
        layout.addWidget(self.loadPosListButton)

        self.queueWidget = QtGui.QListWidget()
        self.queueWidget.setMaximumSize(200,150)
        layout.addWidget(self.queueWidget)
        self.setPositions([] if positions is None else positions)

    def setPositions(self,positions):
        self.positions = positions
        for position in positions:
            self.queueWidget.addItem(str(position))

    def loadPositions(self):
        fname, result = QtGui.QFileDialog.getOpenFileName(
            self,
            'Open file',
            'Z:\stevens4\gitHub\sitzlabexpcontrol\scan'
        )
        with open(fname, 'r') as fileObj:
            try:
                return [
                    float(position.replace(',','')) for position in fileObj.read().split('\n')
                ]
            except ValueError:
                QtGui.QMessageBox.warning('Error processing file - must be a list of newline separated numbers.')
                return self.loadPositions()

    def getInput(self,agent):
        return ListScanInput(agent,copy(self.positions))
            
def test():
    ## BOILERPLATE ##
    import sys
    from PySide import QtGui, QtCore
    from math import sin
    if QtCore.QCoreApplication.instance() is None:
        app = QtGui.QApplication(sys.argv)
        import qt4reactor
        qt4reactor.install()
    ## BOILERPLATE ##

    #create the widget name even if you're not using it so that onStepped doesn't error
    listScanInputWidget = None  
    def log(x): print x
    
    
    
    #configure a layout for the plot widget & controls to go side by side on
    widget = QtGui.QWidget()
    widget.show()
    layout = QtGui.QHBoxLayout()
    widget.setLayout(layout)

    # create a plot and associated widget
    from pyqtgraph import PlotWidget
    plotWidget = PlotWidget()
    plot = plotWidget.plot()
    layout.addWidget(plotWidget)

    
    #configure a control panel layout
    controlPanel = QtGui.QWidget()
    cpLayout = QtGui.QVBoxLayout()
    controlPanel.setLayout(cpLayout)

    #create a scanToggleObject
    scanToggle = ScanToggleObject()
    
    '''
    #create a list scan input & widget
    listScanInput = ListScanInput(lambda(x):x,None)
    listScanInputWidget = ListScanInputWidget(listScanInput)
    cpLayout.addWidget(listScanInputWidget)
    scanToggle.toggled.connect(
        compose(
            listScanInputWidget.setDisabled,
            scanToggle.isToggled
        )
    )
    scanToggle.toggled.connect(partial(log,listScanInputWidget.listScanInput.positions))
    scanToggle.setInput(listScanInput.next)
    
    '''
    #create an interval scan input & widget
    intScanInput = IntervalScanInput(lambda(x):x,0,1000,10)
    scanToggle.setInput(intScanInput.next)
    intScanInputWidget = IntervalScanInputWidget(intScanInput,DEFAULTS)
    cpLayout.addWidget(intScanInputWidget)
    scanToggle.toggled.connect(
        compose(
            intScanInputWidget.setDisabled,
            scanToggle.isToggled
        )
    )

    
    #create scan output, for now a sine wave, this is where voltmeter would go
    def output(): 
        result = sin(float(output.i)/output.res)
        output.i+=1
        return result
    output.i = 0
    output.res = 10
    scanToggle.setOutput(output)
    
    
    # create a scan toggle
    x, y = [], []
    def onActivationRequested(x,y):
        while x: x.pop()
        while y: y.pop()
        scanToggle.toggle()
    
    # not performing any setup, so go ahead and connect activation requests to toggle
    scanToggle.activationRequested.connect(
        partial(
            onActivationRequested,
            x,
            y
        )
    )

    
    # create a toggle widget
    from qtutils.toggle import ToggleWidget
    cpLayout.addWidget(ToggleWidget(scanToggle))

    
    # handle the stepped signal
    from ab.abbase import sleep
    @inlineCallbacks
    def onStepped(data):
        input, output = data
        x.append(input)
        y.append(output)
        plot.setData(x,y)
        yield sleep(.05)
        scanToggle.completeStep()
        if listScanInputWidget is not None: listScanInputWidget.updateQueue()
    scanToggle.stepped.connect(onStepped)

    #for debug purposes, connect to toggle signal
    scanToggle.toggled.connect(partial(log,'toggled'))
    scanToggle.toggleRequested.connect(partial(log,'toggleRequested'))

    
    #add the control panel to the window and execute
    layout.addWidget(controlPanel)
   
    app.exec_()

if __name__ == '__main__':
    test()
