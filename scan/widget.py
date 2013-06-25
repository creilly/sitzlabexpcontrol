from PySide import QtGui
from PySide.QtCore import Signal

from twisted.internet.defer import inlineCallbacks, Deferred
from qtutils.toggle import ToggleObject, ClosedToggle

from functools import partial

from sitz import compose

from scan import Scan

from input import IntervalScanInput, ListScanInput

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
    stepped = Signal(object)
    def __init__(self,input,output):
        ToggleObject.__init__(self,initialState=False)
        def callback(input,output):
            d = self._d = Deferred()
            self.stepped.emit((input,output))
            return d
        scan = Scan(input,output,callback)
        closedToggle = self.closedToggle = ClosedToggle(False)
        self.toggleRequested.connect(closedToggle.requestToggle)
        @inlineCallbacks
        def onStart():
            self.toggle()
            yield scan.start()
            if closedToggle.isToggled(): closedToggle.requestToggle()
            self.toggle()
        closedToggle.activated.connect(onStart)

    def completeStep(self):
        self._d.callback(self.closedToggle.isToggled())


        
class IntervalScanInputWidget(QtGui.QWidget):
    BEGIN,END,STEP = 0,1,2
    PROPERTIES = (BEGIN,END,STEP)
    def __init__(self,intervalScanInput,defaults):
        QtGui.QWidget.__init__(self)
        self.input = intervalScanInput
        layout = QtGui.QFormLayout()
        self.setLayout(layout)
        for id in self.PROPERTIES:
            spin = QtGui.QSpinBox()
            spin.setRange(*defaults[id])
            spin.valueChanged.connect(
                partial(
                    setattr,
                    intervalScanInput,
                    {
                        self.BEGIN:'begin',
                        self.END:'end',
                        self.STEP:'step'
                    }[id]
                )
            ),
            layout.addRow(
                {
                    self.BEGIN:'begin',
                    self.END:'end',
                    self.STEP:'step'
                }[id],
                spin
            )


class ListScanInputWidget(QtGui.QWidget):
    def __init__(self,listScanInput):
        QtGui.QWidget.__init__(self)
        self.input = listScanInput
        layout = QtGui.QFormLayout()
        self.textEdit = QtGui.QTextEdit()
       
        def loadPosList():
            filename, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                'Z:\stevens4\gitHub\sitzlabexpcontrol\scan')
            fileObj = open(fname, 'r')
            with fileObj:
                positions = fileObj.read()
                self.textEdit.setText(positions) #display the list in a text edit widget
            partial(setattr, listScanInput,
                    {self.positions:'positions'}
                )
        
        loadPosListButton = QtGui.QPushButton('load positions list')
        loadPosListButton.clicked.connect(loadPosList)
        controlPanel.addRow(loadPosListButton)

            
def test():
    ## BOILERPLATE ##
    import sys
    from PySide import QtGui, QtCore
    if QtCore.QCoreApplication.instance() is None:    
        app = QtGui.QApplication(sys.argv)
        import qt4reactor
        qt4reactor.install()
    ## BOILERPLATE ##

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

    # create a scan toggle
    size = 30
    inputData = range(size)
    outputData = [x**2 for x in range(size)]
    def input(): return inputData.pop() if inputData else None
    def output(): return outputData.pop()
    scanToggle = ScanToggleObject(input,output)

    
    
    # create a toggle widget
    from qtutils.toggle import ToggleWidget
    cpLayout.addWidget(ToggleWidget(scanToggle))

    # handle the stepped signal
    x, y = [], []
    from ab.abbase import sleep
    @inlineCallbacks
    def onStepped(data):
        input, output = data
        x.append(input)
        y.append(output)
        plot.setData(x,y)
        yield sleep(.1)
        scanToggle.completeStep()
    scanToggle.stepped.connect(onStepped)

    def log(x): print x
    scanToggle.toggled.connect(partial(log,'toggled'))
    scanToggle.toggleRequested.connect(partial(log,'toggleRequested'))
    
    '''
    #setPosition method takes a position, returns read position
    #for testing purposes use: " return lambda(x): x "
    
    #create a IntervalScanInput and associated widget
    intScanInput = IntervalScanInput(lambda(x):x,0,1000,10)
    intScanInputWidget = IntervalScanInputWidget(intScanInput,DEFAULTS)
    cpLayout.addWidget(intScanInputWidget)
    scanToggle.toggled.connect(
        compose(
            intScanInputWidget.setDisabled,
            scanToggle.isToggled
        )
    )
    '''
    dummyPos = range(30)
    listScanInput = ListScanInput(lambda(x):x,dummyPos)
    listScanInputWidget = ListScanInputWidget(listScanInput)
    cpLayout.addWidget(listScanInputWidget)
    
    
    
    
    #add the control panel to the plot window layout
    layout.addWidget(controlPanel)
   
    app.exec_()

if __name__ == '__main__':
    test()
