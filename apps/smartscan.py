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

from sitz import compose, STEPPER_MOTOR_SERVER, TEST_STEPPER_MOTOR_SERVER, WAVELENGTH_SERVER

from scan import Scan

from scan.widget import ScanToggleObject, IntervalScanInputWidget, ListScanInputWidget
from scan.input import IntervalScanInput, ListScanInput

from voltmeter.voltmeterclient import VoltMeterClient

from ab.abclient import getProtocol    

from config.steppermotor import SM_CONFIG, KDP, BBO, PDL
from config.voltmeter import VM_SERVER_CONFIG, VM_DEBUG_SERVER_CONFIG
from config.scantypes import SCAN_TYPES

from steppermotor.steppermotorclient import ChunkedStepperMotorClient

MAX = 99999
MIN_STEP = 1
MAX_STEP = 1000

INTERVAL_DEFAULTS = [(-1 * MAX, MAX),(-1 * MAX, MAX),(MIN_STEP,MAX_STEP)]

DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'

'''
created by stevens4 on 2013/06/27

provides a gui built out of other components for scanning specific 
positions on a stepper motor, eg. SmartScan of PDL while observing
ion signal

'''
@inlineCallbacks
def SmartScanGUI():
    vmProtocol = yield getProtocol(
        (VM_DEBUG_SERVER_CONFIG if DEBUG else VM_SERVER_CONFIG)['url']
    )
    smProtocol = yield getProtocol(
        TEST_STEPPER_MOTOR_SERVER if DEBUG else STEPPER_MOTOR_SERVER 
    )
    wlProtocol = yield getProtocol(WAVELENGTH_SERVER)
    
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
    layout.addWidget(plotWidget,1)
    
    # configure a control panel layout
    cpLayout = QtGui.QFormLayout()
    layout.addLayout(cpLayout)

    # create dictionary of agents
    # <BLACK BOX>
    SET_POSITION, CANCEL = 0,1
    AGENT_CALLS = (SET_POSITION,CANCEL)
    agents = {
        tuple(
            ( 
                {
                    SET_POSITION:smClient.setPosition,
                    CANCEL:smClient.cancel
                }[agent_call] for agent_call in AGENT_CALLS
            )
        ):name        
        for name, smClient in
        (
            (
                SM_CONFIG[smID]['name'],
                ChunkedStepperMotorClient(smProtocol,smID)
            )
            for smID in
            SM_CONFIG.keys()
        )
    }
    @inlineCallbacks
    def wavelengthAgent(position):
        yield wlProtocol.sendCommand('set-wavelength',position)
        wavelength = yield wlProtocol.sendCommand('get-wavelength')
        returnValue(wavelength)
    agents.update(
        {
            tuple(
                (
                    {
                        SET_POSITION:wavelengthAgent,
                        CANCEL:partial(wlProtocol.sendCommand,'cancel-wavelength-set')
                    }[agent_call] for agent_call in AGENT_CALLS
                )
            ):'surf'
        }
    )
    # </BLACK BOX>

    # create a dict combo box to allow user to select agent
    agentsCombo = DictComboBox(agents)
    cpLayout.addRow('input',agentsCombo)
    
    #add a combobox for the voltmeters populated by a server request result
    vmClient = VoltMeterClient(vmProtocol)
    channels = yield vmClient.getChannels()
    vmCombo = DictComboBox({channel:channel for channel in channels})
    cpLayout.addRow('voltmeter',vmCombo)
    
    #create a tab widget for list scan & interval scan to go on
    scanInputTabs = QtGui.QTabWidget()
    scanInputTabs.setTabPosition(QtGui.QTabWidget.West)
    cpLayout.addRow('scan range',scanInputTabs)
    
    INTERVAL, LIST = 0, 1
    INPUTS = (INTERVAL,LIST)
    inputWidgets = {
        LIST:ListScanInputWidget(),
        INTERVAL:IntervalScanInputWidget(INTERVAL_DEFAULTS)
    }
    for inputWidget in INPUTS:
        scanInputTabs.addTab(
            inputWidgets[inputWidget],
            {
                INTERVAL:'interval',
                LIST:'list'
            }[inputWidget]
        )
    
    #create a scan toggle
    scanToggle = ScanToggleObject()
    
    #on start button click, clear data arrays & toggle scan
    x, y = [], []
    def onActivationRequested(x,y):
        while x: x.pop()
        while y: y.pop()
        scanToggle.setInput(
            inputWidgets[
                INPUTS[
                    scanInputTabs.currentIndex()
                ]
            ].getInput(
                agentsCombo.getCurrentKey()[AGENT_CALLS.index(SET_POSITION)]
            ).next
        )
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
        
    scanToggle.activationRequested.connect(partial(onActivationRequested,x,y))
    def onDeactivationRequested():
        agentsCombo.getCurrentKey()[AGENT_CALLS.index(CANCEL)]()
    scanToggle.deactivationRequested.connect(onDeactivationRequested)
    
    #create a spinbox for the shots to average parameter
    shotsSpin = QtGui.QSpinBox()
    shotsSpin.setRange(1,10000)
    cpLayout.addRow('shots to average', shotsSpin)
    
    # create a toggle widget
    from qtutils.toggle import ToggleWidget
    cpLayout.addWidget(ToggleWidget(scanToggle))

    # plot on step completion
    def onStepped(data):
        input, output = data
        x.append(input)
        y.append(output)
        plot.setData(x,y)
        scanToggle.completeStep()
    scanToggle.stepped.connect(onStepped)

if __name__ == '__main__':
    from twisted.internet import reactor
    container = []
    SmartScanGUI()
    reactor.run()
    
    
