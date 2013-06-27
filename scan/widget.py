from PySide import QtGui
from PySide import QtCore

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
    stepped = QtCore.Signal(object)
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
    START,STOP,STEP = 0,1,2
    PROPERTIES = (START,STOP,STEP)
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
                        self.START:'start',
                        self.STOP:'stop',
                        self.STEP:'step'
                    }[id]
                )
            ),
            layout.addRow(
                {
                    self.START:'start',
                    self.STOP:'stop',
                    self.STEP:'step'
                }[id],
                spin
            )


class ListScanInputWidget(QtGui.QWidget):
    def __init__(self,listScanInput):
        QtGui.QWidget.__init__(self)
        self.listScanInput = listScanInput
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)
        self.label = QtGui.QLabel(self)
        positions = []
        fname = 'nothing'
       
        def loadPosList():
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                'Z:\stevens4\gitHub\sitzlabexpcontrol\scan')
            fileObj = open(fname, 'r')
            with fileObj:
                plainText = fileObj.read()
                try: 
                    for pos in plainText.split('\n'): positions.append(float(pos.replace(',','')))
                except ValueError:
                    print 'somebody done messed up'
                    msgBox = QtGui.QMessageBox()
                    msgBox.setText("Error processing file - must be a list of floats on newlines.")
                    msgBox.exec_()
                    loadPosList()
                    return
                self.listScanInput.positions = positions
                self.label.setText(fname.split('/')[-1]+' is loaded.')
                self.label.adjustSize()
                for pos in self.listScanInput.positions: self.queueWidget.addItem(str(pos))
            fileObj.close()
        
        def clearQueue():
            while positions: positions.pop()
            while self.listScanInput.positions: self.listScanInput.positions.pop()
            self.label.setText('nothing is loaded.')
            self.queueWidget.clear()
        
        self.loadPosListButton = QtGui.QPushButton('load queue')
        self.loadPosListButton.clicked.connect(loadPosList)
        layout.addWidget(self.loadPosListButton)
        self.label.setText(fname+' is loaded.')
        
        self.queueWidget = QtGui.QListWidget()
        self.queueWidget.setMaximumSize(200,150)
        layout.addWidget(self.queueWidget)
        
        self.clrQueueButton = QtGui.QPushButton('clear queue')
        self.clrQueueButton.clicked.connect(clearQueue)
        layout.addWidget(self.clrQueueButton)
        
    def updateQueue(self):
        #pops the first elements off the queue to represent typical scan behavior
        self.queueWidget.takeItem(0)


        

            
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

    
    #crease a list scan input
    listScanInput = ListScanInput(lambda(x):x,None)
    
    
    # create a scan toggle
    size = 200
    inputData = range(size)
    outputData = [(x/float(size))**2 - (x/float(size))**3 for x in inputData]
    def input(): return inputData.pop() if inputData else None
    def output(): return outputData.pop()
    #scanToggle = ScanToggleObject(input,output)
    scanToggle = ScanToggleObject(listScanInput.nextPosition,output)
    

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
        yield sleep(.05)
        scanToggle.completeStep()
        listScanInputWidget.updateQueue()
    scanToggle.stepped.connect(onStepped)

    def log(x): print x
    scanToggle.toggled.connect(partial(log,'toggled'))
    scanToggle.toggleRequested.connect(partial(log,'toggleRequested'))
    

    #setPosition method takes a position, returns read position
    #for testing purposes use: " return lambda(x): x "
    '''
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
    listScanInputWidget = ListScanInputWidget(listScanInput)
    cpLayout.addWidget(listScanInputWidget)
    scanToggle.toggled.connect(
        compose(
            listScanInputWidget.loadPosListButton.setDisabled,
            scanToggle.isToggled
        )
    )
    scanToggle.toggled.connect(
        compose(
            listScanInputWidget.clrQueueButton.setDisabled,
            scanToggle.isToggled
        )
    )
    scanToggle.toggled.connect(partial(log,listScanInputWidget.listScanInput.positions))

    
    
    #add the control panel to the plot window layout
    layout.addWidget(controlPanel)
   
    app.exec_()

if __name__ == '__main__':
    test()
