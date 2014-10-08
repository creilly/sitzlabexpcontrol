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

from config.serverURLs import *
'''# URLs (need to find better URL structure)
from sitz import STEPPER_MOTOR_SERVER, \
    TEST_STEPPER_MOTOR_SERVER, WAVELENGTH_SERVER, \
    TEST_WAVELENGTH_SERVER, DELAY_GENERATOR_SERVER, \
    TEST_DELAY_GENERATOR_SERVER 
'''
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
from steppermotor.polarizerclient import PolarizerClient

# plotting
from math import pow
import numpy as np
from pyqtgraph import PlotWidget, ErrorBarItem, mkPen, LegendItem

import os
import datetime

'''optional parameters interpretation code
has debug mode as well as optional input modes for
steppermotor, wavelengthserver, ddg, manual, & polarizer modes
to enable just pass the associated letter (see inputs_keys)
like this: python smartscan.py swdm
'''
DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'
SM_BOOL, WL_BOOL, DDG_BOOL, MAN_BOOL, MAN_LIST_BOOL, POL_BOOL = 0,1,2,3,4,5
INPUTS = (SM_BOOL,WL_BOOL,DDG_BOOL,MAN_BOOL,MAN_LIST_BOOL,POL_BOOL)
INPUTS_TOGGLE = {input:False for input in INPUTS}
INPUTS_KEYS = {
    's':SM_BOOL,
    'w':WL_BOOL,
    'd':DDG_BOOL,
    'm':MAN_BOOL,
    'q':MAN_LIST_BOOL,
    'p':POL_BOOL
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

print INPUTS_TOGGLE
        
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
                        decimals=3
                    )
                    return result if valid else None
            return ManualInput()
        CancelInputWidget.__init__(self,scan_input_generator,lambda:None,lambda:None)

class SmartScanListInputWidget(CancelInputWidget):
    def __init__(
        self,            
        next_agent,
        cancel_agent,
        limit_min,
        limit_max,
        limit_prec,
        limit_init,
        step_min,
        step_max,
        step_prec,
        step_init
    ):
        this = self.intervalScanInputWidget = IntervalScanInputWidget()
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

        layout.addWidget(this,1)

class CenterInputWidget(SmartScanListInputWidget):
    def __init__(
        self,
        next_agent,    #agent to progress the scan
        cancel_agent,  #agent to abort the scan
        limit_min,     #minimum value of scan bounds
        limit_max,     #maximum value of scan bounds 
        limit_prec,    #precision (number of zeroes after decimal) on bounds
        limit_init,    #initial value for scan bounds
        step_min,      #minimum value of step size
        step_max,      #maximum value of scan bounds
        step_prec,     #precision (number of zeroes after decimal) on step size
        step_init,     #initial value for step size
        get_position   #agent to read position for scan
    ):
        SmartScanListInputWidget.__init__(
            self,
            next_agent,
            cancel_agent,
            limit_min,
            limit_max,
            limit_prec,
            limit_init,
            step_min,
            step_max,
            step_prec,
            step_init
        )
        this = self.intervalScanInputWidget
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
        self.layout().insertWidget(0,SqueezeRow(center_button,0),0)        


class ManualScanInputWidget(SmartScanListInputWidget):
    def __init__(self,parent):
        def next(position):
            QtGui.QMessageBox.information(
                parent,
                'next position',
                'next position:\t%s' % position
            )
            return position
        SmartScanListInputWidget.__init__(
            self,
            next,
            lambda:None,
            -1.e4,
            1.e4,
            4,
            10,
            1.e-4,
            1.e3,
            4,
            1.
        )
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

extends ScanToggleObject for cancelling capabilities

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
        refData = {}

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
    inputWidget.addTab(
        ManualScanInputWidget(widget),
        'manual scan'
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
                    -99999,
                    99999,
                    0,
                    0,
                    0,
                    1000,
                    0,
                    10,
                    smClient.getPosition                    
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
                24100.0,            
                25000.0,
                2,
                24200.0,
                0.01,
                100.0,
                2,
                .2,
                wlClient.getWavelength                
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
    if INPUTS_TOGGLE[POL_BOOL]:
        print 'adding pol'
        # add wavelength client to scan input
        polProtocol = yield getProtocol(
            TEST_POLARIZER_SERVER if DEBUG else POLARIZER_SERVER
        )
        polClient = PolarizerClient(polProtocol)
        polInputWidget = ComboWidget()
        polInputWidget.addTab(
            CenterInputWidget(
                polClient.setAngle,  #agent to progress the scan
                polClient.cancelAngleSet,  #agent to abort the scan
                -720.0, #minimum value of scan bounds           
                720.0,  #maximum value of scan bounds 
                2,      #precision (number of zeroes after decimal) on bounds 
                90.0,   #initial value for scan bounds
                0.01,   #minimum value of step size
                180.0,  #maximum value of scan bounds
                2,      #precision (number of zeroes after decimal) on step size
                5.0,    #initial value for step size
                polClient.getAngle  #agent to read position for scan
            ),
            'interval'
        )
        polInputWidget.addTab(
            ListInputWidget(
                polClient.setAngle,
                polClient.cancelAngleSet
            ),
            'list'
        )
        inputWidget.addTab(
            polInputWidget,
            'pol'
        )
    if INPUTS_TOGGLE[DDG_BOOL]:
        # add delay generator to scan input
        dgProtocol = yield getProtocol(
            TEST_DELAY_GENERATOR_SERVER if DEBUG else DELAY_GENERATOR_SERVER
        )
        dgClient = DelayGeneratorClient(dgProtocol)
        delays = yield dgClient.getDelays()
        for dgID in delays.keys():
            def setter(dgID):
                @inlineCallbacks
                def _setter(delay):
                    yield dgClient.setPartnerDelay(dgID,delay)
                    returnValue(delay)
                return _setter
            def getter(dgID):
                @inlineCallbacks
                def _getter():
                    delays = yield dgClient.getDelays()
                    returnValue(delays[dgID])
                return _getter
            def cancel(dgID):
                def _cancel(): pass
                return _cancel
            dgCombo = ComboWidget()
            dgCombo.addTab(
                CenterInputWidget(
                    setter(dgID),
                    cancel(dgID),
                    1,
                    50000000,
                    0,
                    3896550.0,
                    0,
                    1000000,
                    1,
                    100,
                    getter(dgID)                    
                ),
                'interval'
            )
            dgCombo.addTab(
                ListInputWidget(
                    setter(dgID),
                    cancel(dgID)
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
    
    def xYPlot(plotWidget,x,y,yerr=None,xerr=None,color='w',name='Current'):
        thisPlot = plotWidget.plot(x,y,pen=mkPen(color,width=2))
        plotWidget.addItem(
            ErrorBarItem(
                x=np.asarray(x),
                y=np.asarray(y),
                top=np.asarray(yerr) if yerr is not None else None,
                bottom=np.asarray(yerr) if yerr is not None else None,
                left=np.asarray(xerr) if xerr is not None else None,
                right=np.asarray(xerr) if xerr is not None else None,
                beam=.05,
                pen=mkPen(color)
            )
        )
        
    
    # plot on step completion
    def updatePlot():
        plotWidget.clear()
        for name, refData in self.refData.iteritems():
            xYPlot(
                plotWidget,
                refData['data'][0],
                refData['data'][1],
                yerr=refData['data'][2],
                color=refData['color'],
                name=name
            )
        if len(self.x) >= 1:
            xYPlot(plotWidget,self.x,self.y,yerr=self.err)
        
    
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
        updatePlot()

        # ready for next step!
        scanToggle.completeStep()        
    scanToggle.stepped.connect(onStepped)

    
    # set up reference data capabilities
    refLayout = QtGui.QHBoxLayout()
    
    def onLoadClicked():
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        time = datetime.datetime.now().strftime("%H%M")
        dir = os.path.join(
            POOHDATAPATH,
            date
        )
        
        refFileName = QtGui.QFileDialog.getOpenFileName(
            widget,
            'select file', 
            dir,
            "CSV Files (*.csv)"
        )
        
        refData = np.loadtxt(open(refFileName[0],"rb"),delimiter=",")
        name = refFileName[0].rpartition('/')[2]
        
        color = QtGui.QColorDialog.getColor()
        
        self.refData[name] = {
            'color': color,
            'data': [refData[:,0], refData[:,1], refData[:,2]]
        }
        
        updatePlot()
    
    loadButton = QtGui.QPushButton('load')
    loadButton.clicked.connect(onLoadClicked)
    refLayout.addWidget(SqueezeRow(loadButton))

    def onClearClicked():
        for refs in self.refData.keys():
            del self.refData[refs]
            
        updatePlot()

    clearButton = QtGui.QPushButton('clear all')
    clearButton.clicked.connect(onClearClicked)
    refLayout.addWidget(SqueezeRow(clearButton))

    cpLayout.addWidget(
        LabelWidget(
            'reference',
            refLayout
        )
    )    

    
    # set up data saving capabilities
    saveLayout = QtGui.QVBoxLayout()

    def onSaveClicked():
        dataArray = np.asarray(
            [self.x,self.y,self.err],
            dtype=np.dtype(np.float32)
        )
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        time = datetime.datetime.now().strftime("%H%M")
        dir = os.path.join(
            POOHDATAPATH,
            date
        )
        if not os.path.exists(dir):
            os.makedirs(dir)
        path = QtGui.QFileDialog.getExistingDirectory(
            widget,
            'select filename', 
            dir
        )
        if not path: return
        desc, valid = QtGui.QInputDialog.getText(
            widget,
            'enter file description',
            'description'
        )
        filename = '%s_%s.csv' % (time,desc) if valid else '%s.csv' % time 
        np.savetxt(
            os.path.join(
                path,
                filename
            ),
            dataArray.transpose(),
            delimiter=','
        )
    saveButton = QtGui.QPushButton('save')
    saveButton.clicked.connect(onSaveClicked)
    saveLayout.addWidget(SqueezeRow(saveButton))
    
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
 
