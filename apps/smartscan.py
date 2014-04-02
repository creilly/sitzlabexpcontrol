#this must be run first before importing the alternate reactor to avoid a 
#conflict between the qt and twisted reactors
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install() 

# for server calls
from twisted.internet.defer import inlineCallbacks, Deferred, returnValue
from ab.abclient import getProtocol
# URLs (need to find better URL structure)
from sitz import STEPPER_MOTOR_SERVER, \
    TEST_STEPPER_MOTOR_SERVER, WAVELENGTH_SERVER, \
    TEST_WAVELENGTH_SERVER, DELAY_GENERATOR_SERVER, \
    TEST_DELAY_GENERATOR_SERVER 
from config.voltmeter import VM_SERVER_CONFIG, VM_DEBUG_SERVER_CONFIG

# some utility widgets
from qtutils.toggle import ToggleObject, ClosedToggle, ToggleWidget
from qtutils.dictcombobox import DictComboBox
from qtutils.layout import SqueezeRow
from qtutils.label import LabelWidget

# fun
from functools import partial
from sitz import compose

# saving scan data
from filecreationmethods import saveCSV
from config.scantypes import SCAN_TYPES
from config.filecreation import POOHDATAPATH

# core scan structures
from scan import Scan
from scan.widget import ScanToggleObject, IntervalScanInputWidget, ListScanInputWidget

# ID info for different apps
from daqmx.task.ai import VoltMeter
from config.steppermotor import KDP, BBO, PDL

# clients
from steppermotor.steppermotorclient import ChunkedStepperMotorClient
from voltmeter.voltmeterclient import VoltMeterClient
from steppermotor.wavelengthclient import WavelengthClient
from delaygenerator.delaygeneratorclient import DelayGeneratorClient

# plotting
from math import pow
import numpy as np
from pyqtgraph import PlotWidget, ErrorBarItem

DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'
SM_BOOL, WL_BOOL, DDG_BOOL, MAN_BOOL = 0,1,2,3
INPUTS = (SM_BOOL,WL_BOOL,DDG_BOOL,MAN_BOOL)
INPUTS_TOGGLE = {input:False for input in INPUTS}
INPUTS_KEYS = {
    's':SM_BOOL,
    'w':WL_BOOL,
    'd':DDG_BOOL,
    'm':MAN_BOOL
}
if len(sys.argv) > 1 and all(
        any(
            key==char for key in INPUTS_KEYS
        ) for char in sys.argv[1]
):
    for char in sys.argv[1]:
        INPUTS_TOGGLE[INPUTS_KEYS[char]] = True
else:
    for input in INPUTS_TOGGLE:
        INPUTS_TOGGLE[input] = True

'''
any widget added to the input widget tab will be expected to \
implement a getInput() method that returns an object with two \
methods:

next():

used as a scan input. see documentation for the Scan object for \
details on how scan inputs are used.

cancel():

issues a request for the current step to end as quickly as \
possible.
'''
class InputWidget:
    def getInput(self):
        raise Exception('dont instantiate this abstract class')

'''
same as for InputWidget. output widgets are expect to return a tuple \
of the mean and error (not std dev!) of the measurement
'''
class OutputWidget:
    def getOutput(self):
        raise Exception('dont instantiate this abstract class')

class ComboWidget(QtGui.QTabWidget):
    def __init__(self):
        QtGui.QTabWidget.__init__(self)

    def getInput(self):
        return self.currentWidget().getInput()

    def getOutput(self):
        return self.currentWidget().getOutput()

'''

implements InputWidget interface.

__init__(scan_input_generator,next_agent,cancel_agent)

-> scan_input_generator:
callable that takes a scan input agent and produces a scan input

-> next_agent:
scan input agent

-> cancel_agent:
to be called to abort any standing next() attempt

getInput()

'''
class CancelInputWidget(QtGui.QWidget):
    def __init__(self,scan_input_generator,next_agent,cancel_agent):
        QtGui.QWidget.__init__(self)
        self.next_agent = next_agent
        self.cancel_agent = cancel_agent
        self.scan_input_generator = scan_input_generator

    def getInput(self):
        this = self
        class Input:
            def __init__(self):
                self.scan_input = this.scan_input_generator(this.next_agent)
            def next(self):
                return self.scan_input.next()
            def cancel(self):
                return this.cancel_agent()
        return Input()
        
'''

CancelInputWidget where scan_input_generator is a list scan input widget

'''
class ListInputWidget(CancelInputWidget):
    def __init__(self,next_agent,cancel_agent):
        this = ListScanInputWidget()
        CancelInputWidget.__init__(self,this.getInput,next_agent,cancel_agent)
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().addWidget(this)

'''

CancelInputWidget where scan_input_generator is a interval scan input widget.

Has button that centers scan around 'current position' of object to be scanned.

__init__(...)

-> next_agent
see CancelInputWidget

-> cancel_agent
ditto

-> get_position
callable that returns a deferred that will callback with 'current position' of \
object to be scanned. widget will then center scan around this position (for \
convenience)

remaining parameters specify the bounds of the spin boxes and are self explanatory.

'''

class ManualInputWidget(CancelInputWidget):
    def __init__(self,parent):
        def scan_input_generator(_):
            class ManualInput:
                def next(self):
                    result, valid = QtGui.QInputDialog.getDouble(
                        parent, 
                        'next x value', 
                        'enter next x value',
                    )
                    return result if valid else None
            return ManualInput()
        CancelInputWidget.__init__(self,scan_input_generator,lambda:None,lambda:None)
                    
class CenterInputWidget(CancelInputWidget):
    def __init__(
        self,
        next_agent,
        cancel_agent,
        get_position,
        limit_min,
        limit_max,
        limit_prec,
        limit_init,
        step_min,
        step_max,
        step_prec,
        step_init
    ):                
        this = IntervalScanInputWidget()        
        CancelInputWidget.__init__(
            self,
            this.getInput,
            next_agent,
            cancel_agent
        )
        
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)        

        # set ranges, defaut, precision for spin box params
        for spinID in this.PROPERTIES:
            limit_params = {
                this.MIN:limit_min,
                this.MAX:limit_max,
                this.PRECISION:limit_prec,
                this.VALUE:limit_init
            }
            step_params = {
                this.MIN:step_min,
                this.MAX:step_max,
                this.PRECISION:step_prec,
                this.VALUE:step_init
            }            
            for param,value in {
                this.START:limit_params,
                this.STOP:limit_params,
                this.STEP:step_params
            }[spinID].items():
                this.setParameter(spinID,param,value)

        # create button that centers scan around current value
        center_button = QtGui.QPushButton('center scan')
        @inlineCallbacks
        def center_scan():
            # get current position
            position = yield get_position()
            
            # find width of scan
            old_positions = {
                spinID:this.getParameter(
                    spinID,
                    this.VALUE
                )
                for spinID in (
                    this.START,
                    this.STOP
                )
            }
            scan_width = (
                old_positions[this.STOP] -
                old_positions[this.START]
            )

            # center scan interval, keeping previous limit difference the same
            this.setParameter(
                this.START,
                this.VALUE,
                position - scan_width / 2
            )
            this.setParameter(
                this.STOP,
                this.VALUE,
                position + scan_width / 2
            )
        center_button = QtGui.QPushButton('center scan')        
        center_button.clicked.connect(center_scan)
        layout.addWidget(SqueezeRow(center_button,0))        
        layout.addWidget(this,1)

'''

-> __init__(volt_meter_client)
takes in client to volt meter server, returns object that implements \
the ScanOutput interface. Can specify channel to read from, and number \
of shots to read for each output. Returns mean value over shots as well \
as estimator of error on the mean.

'''
class VoltMeterOutputWidget(QtGui.QWidget):
    def __init__(self,volt_meter_client):                         
        QtGui.QWidget.__init__(self)
        layout = QtGui.QFormLayout()
        self.setLayout(layout)            

        # let user pick which channel to measure
        channels_dict = {}
        channels_combo = DictComboBox()        
        layout.addRow('channel',channels_combo)        

        # let user select number of shots to average
        shots_spin = QtGui.QSpinBox()
        shots_spin.setRange(0,1000)
        shots_spin.setValue(10)
        layout.addRow('shots',shots_spin)

        # populate combo box with available channels
        def on_channels(channels):
            if not channels: return
            channel = channels.pop()           
            def on_description(description):
                channels_dict[channel] = '%s\t(%s)' % (description,channel)
                if channels:
                    on_channels(channels)
                else:
                    channels_combo.updateCombo(channels_dict)
                    self.setEnabled(True)
            volt_meter_client.getChannelParameter(
                channel,VoltMeter.DESCRIPTION                
            ).addCallback(on_description)
        volt_meter_client.getChannels().addCallback(on_channels)

        # don't enable widget until we get all the channels
        self.setEnabled(False)
        
        self.volt_meter_client = volt_meter_client
        self.channels_combo = channels_combo
        self.shots_spin = shots_spin
        self.cancel = False
                         

    def getOutput(self):
        # measure current selected channel
        channel = self.channels_combo.getCurrentKey()

        # average over current specified shot number
        shots = self.shots_spin.value()
        
        this = self
        class Output:
            def __init__(self):
                self._cancel = False
            def next(self):
                voltages_list = []
                d = Deferred()
                def onVoltages(voltages_dict):
                    # push acquired value to list
                    voltages_list.append(voltages_dict[channel])                    
                    # are we done?
                    if len(voltages_list) is shots or self._cancel:
                        total = len(voltages_list)
                        self._cancel = False
                        this.volt_meter_client.removeListener(onVoltages)
                        mean = sum(voltages_list) / total
                        variance = sum(
                            voltage**2 for voltage in voltages_list
                        )/total - mean**2
                        error = pow(variance / total,.5)
                        d.callback((mean,error))
                # sign up for messages about new acquisitions
                this.volt_meter_client.addListener(onVoltages)
                return d
            def cancel(self):
                # if acquiring, quit on next acquisition
                self._cancel = True
        return Output()

'''

extends ScanToggleObject for canceling capabilities

'''
class SmartScanToggleObject(ScanToggleObject):
    def __init__(self):
        ScanToggleObject.__init__(self)
        self._cancel = lambda:None
        self.deactivationRequested.connect(self.cancel)
    def setCancel(self,cancel):
        self.cancel = cancel
    def cancel(self):
        return self._cancel()

# put together the interface
@inlineCallbacks
def SmartScanGUI():
    # oh god i'm so sorry
    class self:
        x,y,err = [], [], []
        
    #configure a layout for the plot widget & controls to go side by side on
    widget = QtGui.QWidget()
    container.append(widget)
    widget.show()
    layout = QtGui.QHBoxLayout()
    widget.setLayout(layout)
    
    # create a plot and associated widget
    
    plotWidget = PlotWidget()
    plot = plotWidget.plot()
    layout.addWidget(plotWidget,1)
    
    # configure a control panel layout
    cpLayout = QtGui.QVBoxLayout()
    layout.addLayout(cpLayout)

    # configure the output widget
    outputWidget = ComboWidget()
    cpLayout.addWidget(LabelWidget('output',outputWidget))

    # add volt meter to scan output
    vmProtocol = yield getProtocol(
        (VM_DEBUG_SERVER_CONFIG if DEBUG else VM_SERVER_CONFIG)['url']
    )
    vmClient = VoltMeterClient(vmProtocol)    
    vmWidget = VoltMeterOutputWidget(vmClient)
    outputWidget.addTab(vmWidget,'voltmeter')

    # configure the input widget
    inputWidget = ComboWidget()
    inputWidget.setTabPosition(inputWidget.West)
    cpLayout.addWidget(LabelWidget('input',inputWidget),1)    

    inputWidget.addTab(
        ManualInputWidget(widget),
        'manual'
    )

    # algorithm for scan inputs is:
    # 0. check to see if input is disabled
    # 1. create client for server from protocol object
    # 2. create combo widget to hold interval and list widgets
    # 3. create interval widget using client object, add to combo
    # 4. same for list widget
    # 5. add combo widget to base combo widget (resulting in 2-D tab widget)
    
    if INPUTS_TOGGLE[SM_BOOL]:
        # add stepper motors to scan input
        smProtocol = yield getProtocol(
            TEST_STEPPER_MOTOR_SERVER if DEBUG else STEPPER_MOTOR_SERVER 
        )    
        smClients = {
            smID:ChunkedStepperMotorClient(smProtocol,smID)
            for smID in (KDP,BBO,PDL)
        }

        for smID,smClient in smClients.items():
            combo_input_widget = ComboWidget()
            
            combo_input_widget.addTab(
                CenterInputWidget(
                    smClient.setPosition,
                    smClient.cancel,
                    smClient.getPosition,
                    -99999,
                    99999,
                    0,
                    0,
                    0,
                    1000,
                    0,
                    10
                ),
                'interval'
            )
        
            combo_input_widget.addTab(
                ListInputWidget(
                    smClient.setPosition,
                    smClient.cancel
                ),
                'list'
            )
        
            inputWidget.addTab(
                combo_input_widget,
                {
                    KDP:'kdp',
                    BBO:'bbo',
                    PDL:'pdl'
                }[smID]
            )
    
    if INPUTS_TOGGLE[WL_BOOL]:
        # add wavelength client to scan input
        wlProtocol = yield getProtocol(
            TEST_WAVELENGTH_SERVER if DEBUG else WAVELENGTH_SERVER
        )
        wlClient = WavelengthClient(wlProtocol)
        wlInputWidget = ComboWidget()
        wlInputWidget.addTab(
            CenterInputWidget(
                wlClient.setWavelength,
                wlClient.cancelWavelengthSet,
                wlClient.getWavelength,
                24100.0,            
                25000.0,
                2,
                24200.0,
                0.01,
                100.0,
                2,
                .2
            ),
            'interval'
        )
        wlInputWidget.addTab(
            ListInputWidget(
                wlClient.setWavelength,
                wlClient.cancelWavelengthSet
            ),
            'list'
        )
        inputWidget.addTab(
            wlInputWidget,
            'surf'
        )
    if INPUTS_TOGGLE[DDG_BOOL]:
        # add delay generator to scan input
        dgProtocol = yield getProtocol(
            TEST_DELAY_GENERATOR_SERVER if DEBUG else DELAY_GENERATOR_SERVER
        )
        dgClient = DelayGeneratorClient(dgProtocol)
        delays = yield dgClient.getDelays()
        for dgID in delays.keys():
            @inlineCallbacks
            def setter(delay):
                yield dgClient.setPartnerDelay(dgID,delay)
                returnValue(delay)
            @inlineCallbacks
            def getter():
                delays = yield dgClient.getDelays()
                returnValue(delays[dgID])
            def cancel(): pass
            dgCombo = ComboWidget()
            dgCombo.addTab(
                CenterInputWidget(
                    setter,
                    cancel,
                    getter,
                    1,
                    50000000,
                    0,
                    3896550.0,
                    0,
                    3000000,
                    1,
                    100
                ),
                'interval'
            )
            dgCombo.addTab(
                ListInputWidget(
                    setter,
                    cancel
                ),
                'list'
            )
            inputWidget.addTab(
                dgCombo,
                dgID
            )

    #create a scan toggle
    scanToggle = SmartScanToggleObject()
    cpLayout.addWidget(
        LabelWidget(
            'scan',ToggleWidget(scanToggle)
        )
    )
    
    def onActivationRequested():
        # empty data
        for l in (self.x,self.y,self.err):
            while l: l.pop()

        # get current selected scan output, scan input
        scanOutput = outputWidget.getOutput()
        scanInput = inputWidget.getInput()
        scanToggle.setOutput(scanOutput.next)
        scanToggle.setInput(scanInput.next)

        # on stop request, send cancel signal to scan input and output
        def cancel():
            scanInput.cancel()
            scanOutput.cancel()
        scanToggle.setCancel(cancel)

        # start scan
        scanToggle.toggle()    
    scanToggle.activationRequested.connect(onActivationRequested)
    
    # plot on step completion
    def onStepped(data):
        # unpack scan step data
        position, output = data

        # unpack output as mean and error
        mean, err = output

        # update plot data
        self.x.append(position)
        self.y.append(mean)
        self.err.append(err)

        # update plot
        plotWidget.clear()
        plotWidget.plot(self.x,self.y)
        plotWidget.addItem(
            ErrorBarItem(
                x=np.asarray(self.x),
                y=np.asarray(self.y),
                top=np.asarray(self.err),
                bottom=np.asarray(self.err),
                beam=.05
            )
        )

        # ready for next step!
        scanToggle.completeStep()        
    scanToggle.stepped.connect(onStepped)

    # set up data saving capabilities (ask bobby re: this)
    saveLayout = QtGui.QVBoxLayout()

    #dropdown box for measurementType so saveCSV (below) uses correct directory
    measureList = SCAN_TYPES.keys()
    measureCombo = QtGui.QComboBox()
    measureCombo.addItems(measureList)
    cpLayout.addWidget(
        LabelWidget(
            measureCombo,
            'measurement'
        )
    )
    saveLayout.addWidget(measureCombo)

    def onSaveClicked():
        measure = measureCombo.currentText()
        dataArray = np.asarray(
            [self.x,self.y,self.err],
            dtype=np.dtype(np.float32)
        )
        saveCSV(measure,dataArray.T,POOHDATAPATH)
    saveCSVButton = QtGui.QPushButton('save (csv)')
    saveCSVButton.clicked.connect(onSaveClicked)
    saveLayout.addWidget(SqueezeRow(saveCSVButton))
    
    cpLayout.addWidget(
        LabelWidget(
            'save',
            saveLayout
        )
    )    

if __name__ == '__main__':
    from twisted.internet import reactor
    container = []
    SmartScanGUI()
    reactor.run()
 
