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

from sitz import compose, STEPPER_MOTOR_SERVER, TEST_STEPPER_MOTOR_SERVER

from scan import Scan

from scan.widget import ScanToggleObject, IntervalScanInputWidget, ListScanInputWidget
from scan.input import IntervalScanInput, ListScanInput

from voltmeter.voltmeterclient import VoltMeterClient

from ab.abclient import getProtocol    

from config.steppermotor import SM_CONFIG, KDP, BBO, PDL
from config.voltmeter import VM_SERVER_CONFIG, VM_DEBUG_SERVER_CONFIG
from config.scantypes import SCAN_TYPES

MAX = 99999
MIN_STEP = 1
MAX_STEP = 1000

DEFAULTS = [(-1 * MAX, MAX),(-1 * MAX, MAX),(MIN_STEP,MAX_STEP)]

DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'

'''
created by stevens4 on 2013/06/27

provides a gui built out of other components for scanning specific 
positions on a stepper motor, eg. SmartScan of PDL while observing
ion signal

'''
# @inlineCallbacks
# def pollVMServer(serverURL):
    # protocol = yield getProtocol(serverURL)
    # client = VoltMeterClient(protocol)
    # vmNameList = yield client.getChannels()
    # vmDict = {' ':' '}
    # for vm in vmNameList: vmDict[vm] = vm
    # returnValue(vmDict)


@inlineCallbacks
def SmartScanGUI():
    print (VM_DEBUG_SERVER_CONFIG if DEBUG else VM_SERVER_CONFIG)['url']
    vmProtocol = yield getProtocol(
        (VM_DEBUG_SERVER_CONFIG if DEBUG else VM_SERVER_CONFIG)['url']
    )
    smProtocol = yield getProtocol(
        TEST_STEPPER_MOTOR_SERVER if DEBUG else STEPPER_MOTOR_SERVER 
    )
    class StepperMotorAgent:
        def __init__(self,protocol,stepperMotor=SM_CONFIG.keys()[0]):
            self.protocol = protocol
            self.stepperMotor = stepperMotor
        def setPosition(self,position):
            return self.protocol.sendCommand('set-position',self.stepperMotor,position)
        def setStepperMotor(self,stepperMotor):
            self.stepperMotor = stepperMotor
        def getStepperMotor(self):
            return self.stepperMotor
    stepperMotorAgent = StepperMotorAgent(smProtocol)
    
    #configure a layout for the plot widget & controls to go side by side on
    widget = QtGui.QWidget()
    container.append(widget)
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
    smDict = {PDL:'dye laser', KDP:'kdp xtal', BBO:'bbo xtal'}
    smCombo = DictComboBox(smDict)
    cpLayout.addRow('stepper motor',smCombo)
    smCombo.choiceMade.connect(log)
    
    #add a combobox for the voltmeters populated by a server request result
    vmClient = VoltMeterClient(vmProtocol)
    channels = yield vmClient.getChannels()
    vmCombo = DictComboBox({channel:channel for channel in channels})
    cpLayout.addRow('voltmeter',vmCombo)
    # vmCombo.choiceMade.connect(log)
    # vmPoll.addCallback(vmCombo.updateCombo)
    
    def testUpdate():
        dict = {'changed1':'changed1','changed2':'changed2'}
        vmCombo.updateCombo(dict)

    testUpdateButton = QtGui.QPushButton('test update')
    testUpdateButton.clicked.connect(testUpdate)
    cpLayout.addWidget(testUpdateButton)
    
    
    '''
    dict = {' ':' '}
        for vm in list: dict.add({vm:vm})
        print dict
    '''
    
    #create a tab widget for list scan & interval scan to go on
    scanInputTabs = QtGui.QTabWidget()
    scanInputTabs.setTabPosition(QtGui.QTabWidget.West)
    cpLayout.addWidget(scanInputTabs)
    
    INTERVAL, LIST = 0, 1
    INPUTS = (INTERVAL,LIST)

    for inputType in INPUTS:
        if inputType is LIST:
            #create a list scan input & widget and put it on a scanInputTab
            listScanInput = ListScanInput(stepperMotorAgent.setPosition,None)
            listScanInputWidget = ListScanInputWidget(listScanInput)
            scanInputTabs.addTab(listScanInputWidget,'list')
        elif inputType is INTERVAL:
            #create a interval scan input & widget and put it on a scanInputTab
            # intScanInput = IntervalScanInput(stepperMotorAgent.setPosition,0,1000,10)
            intScanInputWidget = IntervalScanInputWidget(DEFAULTS)
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
   
    
    # # depending on which input tab is active, set that as the scanToggle input
    # def switchInput(activeInput):
        # print activeInput
        # if activeInput == 'list':
            # scanToggle.setInput(listScanInput.next)
        # if activeInput == 'interval':
            # scanToggle.setInput(intScanInput.next)
    # scanInputTabs.currentChanged.connect(
        # compose(
            # switchInput,
            # scanInputTabs.tabText
        # )
    # )
    # scanInputTabs.currentChanged.emit(0)

    
    #on start button click, clear data arrays & toggle scan
    x, y = [], []
    def onActivationRequested(x,y):
        while x: x.pop()
        while y: y.pop()
        activeInputWidget = INPUTS[scanInputTabs.currentIndex()]
        if activeInputWidget is INTERVAL:
            scanToggle.setInput(intScanInputWidget.getInput(stepperMotorAgent.setPosition).next)
        else:
            scanToggle.setInput(listScanInput.next)
        def output(channel,total):
            output.count = 0
            output.average = 0
            d = Deferred()
            def onVoltages(voltages):
                output.average += voltages[channel]
                output.count += 1
                if output.count is total:
                    vmClient.removeListener(onVoltages)
                    d.callback(output.average / total)
            vmClient.addListener(onVoltages)
            return d
        scanToggle.setOutput(partial(output,vmCombo.getCurrentKey(),shotsSpin.value()))
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

if __name__ == '__main__':
    from twisted.internet import reactor
    container = []
    SmartScanGUI()
    reactor.run()
    
    
