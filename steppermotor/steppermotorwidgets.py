from PySide import QtGui
from PySide import QtCore

from twisted.internet.defer import inlineCallbacks, Deferred
from qtutils.toggle import ToggleObject, ClosedToggle

from functools import partial

from sitz import compose

from scan.widget import ScanToggleObject


DEFAULTS = [(-50000,50000),(-50000,50000),(1,1000)]

'''
defines some widgets for gui interfaces to the steppermotorserver.
for use in apps

'''


class PickFromListWidget(QtGui.QWidget):
    def __init__(self,name,list,function=None,attributes=None):
        #create combobox to pick from a list and set attributes for function
        self.function, self.attributes = function, attributes
        QtGui.QWidget.__init__(self)
        self.label = QtGui.QLabel(self)
        self.label.setText(name)
        self.combo = QtGui.QComboBox(self)
        for item in list: self.combo.addItem(item)
        self.combo.activated[str].connect(self.onActivated)        
        self.show()
        
    def onActivated(self, text):
        #print '%s is selected.' % text
        if self.function is not None: 
            partial(setattr, self.function, self.attributes[text])
            print 'setting these attributes:'
            print self.attributes[text]



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

    
    #create a steppermotorcombo
    smList = ['test1','test2','test3']
    def logger(textToPrint,value): print textToPrint, value
    attr = {'test1':{'textToPrint':'success','value':1},
            'test2':{'textToPrint':'success2','value':2},
            'test3':{'textToPrint':'success3','value':3}
            }
    smComboWidget = PickFromListWidget("Stepper Motor", smList, logger, attr)
    cpLayout.addWidget(smComboWidget)
    smComboWidget.combo.activated.connect(logger)

    # create a scan toggle
    size = 200
    inputData = range(size)
    outputData = [(x/float(size))**2 - (x/float(size))**3 for x in inputData]
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
        yield sleep(.05)
        scanToggle.completeStep()
    scanToggle.stepped.connect(onStepped)

    def log(x): print x
    scanToggle.toggled.connect(partial(log,'toggled'))
    scanToggle.toggleRequested.connect(partial(log,'toggleRequested'))
    

    #add the control panel to the plot window layout
    layout.addWidget(controlPanel)
   
    #show the window
    app.exec_()

if __name__ == '__main__':
    test()
