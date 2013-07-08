#this must be run first before importing the alternate reactor to avoid a 
#conflict between the qt and twisted reactors
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install() 

from twisted.internet.defer import inlineCallbacks, Deferred, returnValue

from qtutils.toggle import ToggleObject, ClosedToggle
from qtutils.dictcombobox import DictComboBox

from functools import partial

from sitz import compose

from scan import Scan

from scan.widget import ScanToggleObject, IntervalScanInputWidget, ListScanInputWidget
from scan.input import IntervalScanInput, ListScanInput

from voltmeter.voltmeterclient import VoltMeterClient

from ab.abclient import getProtocol    

from config.steppermotor import SM_CONFIG
from config.voltmeter import VM_SERVER_CONFIG, VM_DEBUG_SERVER_CONFIG
from config.scantypes import SCAN_TYPES

DEFAULTS = [(-50000,50000),(-50000,50000),(1,1000)]


'''
created by stevens4 on 2013/06/27

provides a gui built out of other components for scanning specific 
positions on a stepper motor, eg. SmartScan of PDL while observing
ion signal

'''

def SmartScanGUI():

    
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
    cpLayout = QtGui.QFormLayout()
    controlPanel.setLayout(cpLayout)

    
    def log(x): print x
    
    #scantypes combobox to configure some settings quickly
    scanTypesCombo = QtGui.QComboBox()
    scanTypesCombo.addItems(SCAN_TYPES.keys())
    cpLayout.addRow('configuration', scanTypesCombo)
    

    
    #add a combobox for the stepper motors
    smDict = {'pdl':'dye laser', 'kdp':'kdp xtal', 'bbo':'bbo xtal'}
    smCombo = DictComboBox(smDict)
    cpLayout.addRow('stepper motor',smCombo)
    smCombo.choiceMade.connect(log)
    
    
    '''
    def getVM():
        vmServerURL = VM_DEBUG_SERVER_CONFIG['url']
        protocol = yield getProtocol(vmServerURL)
        vmp = yield getProtocol(protocol)
        channels = yield vmp.sendCommand('get-channels')
        return vmp
    
    vmp = getVM()
    vmp.addCallback(log)
    '''
    
    
    #add a combobox for the voltmeters populated by a server request result
    def getVMDict():
        d = Deferred()
        vmServerURL = VM_DEBUG_SERVER_CONFIG['url']
        protocol = yield getProtocol(vmServerURL)
        client = VoltMeterClient(protocol)
        list = client.getChannels()
        self.d.callback(list)
        return d
        
    getVM = getVMDict()
    #getVM.addCallback(log)
    
    vmDictTemp = {'test1':'test vm 1','test2':'test vm 2','test3':'test vm 3'}
    vmCombo = DictComboBox(vmDictTemp)
    cpLayout.addRow('voltmeter',vmCombo)
    vmCombo.choiceMade.connect(log)
    '''
    dict = {' ':' '}
        for vm in list: dict.add({vm:vm})
        print dict
    '''
    
    #create a tab widget for list scan & interval scan to go on
    scanInputTabs = QtGui.QTabWidget()
    scanInputTabs.setTabPosition(QtGui.QTabWidget.West)
    cpLayout.addWidget(scanInputTabs)

    
    #crease a list scan input & widget and put it on a scanInputTab
    listScanInput = ListScanInput(lambda(x):x,None)
    listScanInputWidget = ListScanInputWidget(listScanInput)
    scanInputTabs.addTab(listScanInputWidget,'list')


    #crease a interval scan input & widget and put it on a scanInputTab
    intScanInput = IntervalScanInput(lambda(x):x,0,1000,10)
    intScanInputWidget = IntervalScanInputWidget(intScanInput,DEFAULTS)
    scanInputTabs.addTab(intScanInputWidget,'interval')
    
    '''
    scanToggle.setInput(intScanInput.next)
    scanToggle.toggled.connect(
        compose(
            intScanInputWidget.setDisabled,
            scanToggle.isToggled
        )
    )
    '''

    #create a scan toggle
    scanToggle = ScanToggleObject()
    
    
    #create scan output, for now a sine wave, this is where voltmeter would go
    from math import sin
    def output(): 
        result = sin(float(output.i)/output.res)
        output.i+=1
        return result
    output.i = 0
    output.res = 10
    scanToggle.setOutput(output)
   
    
    #depending on which input tab is active, set that as the scanToggle input
    def switchInput(activeInput):
        print activeInput
        if activeInput == 'list':
            scanToggle.setInput(listScanInput.next)
        if activeInput == 'interval':
            scanToggle.setInput(intScanInput.next)
    scanInputTabs.currentChanged.connect(
        compose(
            switchInput,
            scanInputTabs.tabText
        )
    )
    scanInputTabs.currentChanged.emit(0)

    
    #on start button click, clear data arrays & toggle scan
    x, y = [], []
    def onActivationRequested(x,y):
        while x: x.pop()
        while y: y.pop()
        scanToggle.toggle()
    scanToggle.activationRequested.connect(
        partial(
            onActivationRequested,
            x,
            y
        )
    )

    
    #configure widgets to disable when scanning
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
    #scanToggle.toggled.connect(partial(log,listScanInputWidget.listScanInput.positions))

    
    #create a spinbox for the shots to average parameter
    shotsSpin = QtGui.QSpinBox()
    shotsSpin.setRange(1,10000)
    cpLayout.addRow('shots to average: ', shotsSpin)
    shotsSpin.valueChanged.connect(log)
    
    
    # create a toggle widget
    from qtutils.toggle import ToggleWidget
    cpLayout.addWidget(ToggleWidget(scanToggle))

    
    #save button for use on plots with errorbars
    def saveCSVButFunc():
        measure = scanTypeCombo.currentText()
        dataArray = np.asarray([self.x,self.y,self.yerr],dtype=np.dtype(np.float32))
        saveCSV(measure,dataArray.T,DATAPATH)

    saveCSVButton = QtGui.QPushButton('save (csv)')
    #saveCSVButton.clicked.connect(saveCSVButFunc)
    cpLayout.addWidget(saveCSVButton)
    
    
    #spectrum analyzer button to fit and return peaks
    analyzeButton = QtGui.QPushButton('analyze spectrum')
    #analyzeButton.clicked.connect(onAnalyze)
    cpLayout.addWidget(analyzeButton)
        
    
    # handle the stepped signal
    from ab.abbase import sleep
    @inlineCallbacks
    def onStepped(data):
        input, output = data
        x.append(input)
        y.append(output)
        plot.setData(x,y)
        yield sleep(.05)
        if listScanInputWidget is not None: listScanInputWidget.updateQueue()
        scanToggle.completeStep()
    scanToggle.stepped.connect(onStepped)

        
    def log(x): print x
    scanToggle.toggled.connect(partial(log,'toggled'))
    scanToggle.toggleRequested.connect(partial(log,'toggleRequested'))

    
    #add the control panel to the plot window layout
    layout.addWidget(controlPanel)
   
    app.exec_()



if __name__ == '__main__':
    SmartScanGUI()
    
    
