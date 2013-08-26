#this must be run first before importing the alternate reactor to avoid a 
#conflict between the qt and twisted reactors
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install() 
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from ab.abclient import getProtocol
from config.voltmeter import VM_SERVER_CONFIG, VM_DEBUG_SERVER_CONFIG
from sitz import compose
from ab.abbase import selectFromList, sleep
from functools import partial
import pyqtgraph as pg
import os
from config.filecreation import POOHDATAPATH
from filecreationmethods import filenameGen, checkPath
from daqmx.task.ai import VoltMeter as VM
from math import log10
import time
from qtutils.toggle import ToggleObject, ToggleWidget

DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'
URL = (VM_DEBUG_SERVER_CONFIG if DEBUG else VM_SERVER_CONFIG)['url']
MAX = 200
SLEEP = .1

####################
#
# WARNING:
#
# if the voltmeter is unable to
# set a parameter to the requested
# value, an error will print to
# the server's log with no further
# action. reload a fresh edit
# dialog to see the current channel
# parameter settings
#
####################
class ChannelEditDialog(QtGui.QDialog):
    colorChanged = QtCore.Signal(QtGui.QColor)
    def __init__(self,protocol,channel,color,parent=None):
        @inlineCallbacks
        def init():
            QtGui.QDialog.__init__(self,parent)
            self.setWindowTitle('%s edit dialog' % channel)
            layout = QtGui.QFormLayout()
            self.setLayout(layout)
            PARAM_KEYS,PARAM_NAMES = zip(*VM.PARAMETERS)
            setParameter = partial(
                protocol.sendCommand,
                'set-channel-parameter',
                channel
            )
            parameters = {}
            for parameter in PARAM_KEYS:
                value = yield protocol.sendCommand('get-channel-parameter',channel,parameter)
                parameters[parameter] = value
            layout.addRow(
                PARAM_NAMES[
                    PARAM_KEYS.index(
                        VM.PHYSICAL_CHANNEL
                    )
                ],
                QtGui.QLabel(parameters[VM.PHYSICAL_CHANNEL])
            )
            descriptionLineEdit = QtGui.QLineEdit(parameters[VM.DESCRIPTION])
            descriptionLineEdit.returnPressed.connect(
                compose(
                    partial(
                        setParameter,
                        VM.DESCRIPTION
                    ),
                    descriptionLineEdit.text
                )
            )
            layout.addRow(
                PARAM_NAMES[
                    PARAM_KEYS.index(
                        VM.DESCRIPTION
                    )
                ],
                descriptionLineEdit
            )
            trmCfgComboBox = QtGui.QComboBox()
            for trmCfgKey, _, trmCfgName in VM.TERMINAL_CONFIGS:
                trmCfgComboBox.addItem(
                    trmCfgName,trmCfgKey
                )
            trmCfgComboBox.setCurrentIndex(
                trmCfgComboBox.findData(
                    parameters[
                        VM.TERMINAL_CONFIG
                    ]
                )
            )
            trmCfgComboBox.currentIndexChanged.connect(
                compose(
                    partial(
                        setParameter,
                        VM.TERMINAL_CONFIG
                    ),
                    trmCfgComboBox.itemData
                )
            )
            layout.addRow(
                PARAM_NAMES[
                    PARAM_KEYS.index(
                        VM.TERMINAL_CONFIG
                    )
                ],
                trmCfgComboBox
            )
            for param in (VM.MIN,VM.MAX):
                spinBox = QtGui.QDoubleSpinBox()
                spinBox.setDecimals(2)
                spinBox.setSingleStep(.01)
                spinBox.setRange(
                    *{
                        VM.MIN:(-10.0,-.01),
                        VM.MAX:(.01,10.0)
                    }[param]
                )
                spinBox.setValue(parameters[param])
                spinBox.valueChanged.connect(
                    partial(
                        setParameter,
                        param
                    )
                )
                layout.addRow(
                    PARAM_NAMES[
                        PARAM_KEYS.index(
                            param
                        )
                    ],
                    spinBox
                )
            colorEditButton = QtGui.QPushButton('edit')
            colorEditButton.pressed.connect(
                compose(
                    self.colorChanged.emit,
                    partial(
                        QtGui.QColorDialog.getColor,
                        color
                    )
                )
            )
            layout.addRow('color',colorEditButton)
        init()

class VoltMeterWidget(QtGui.QWidget):    
    ID_ROLE = 999
    HISTORY = 200
    MEASUREMENT_TYPE = 'voltmeter'
    def __init__(self,protocol):
        @inlineCallbacks
        def init():
            @inlineCallbacks
            def setText(channel):
                description = yield protocol.sendCommand(
                    'get-channel-parameter',
                    channel,
                    VM.DESCRIPTION
                )
                maxVoltage = yield protocol.sendCommand(
                    'get-channel-parameter',
                    channel,
                    VM.MAX
                )                
                decimalPlaces = int(-1*log10(maxVoltage)) + 1
                formatString = '%.' + str(decimalPlaces if decimalPlaces > 0 else 0) + 'f'
                items[channel].setText(
                    '%s\t%s\t%s V' % (
                        description,
                        channel,
                        (
                            formatString
                        ) % maxVoltage
                    )
                )
            def rightClicked(listWidget,p):
                item = listWidget.itemAt(p)
                if item is None: return
                channel = item.data(self.ID_ROLE)
                editDialog = ChannelEditDialog(protocol,channel,colors[channel],self)
                editDialog.colorChanged.connect(partial(colorChanged,channel))
                editDialog.show()
            def colorChanged(channel,color):
                colors[channel] = color
                items[channel].setBackground(color)
                plots[channel].setPen(
                    pg.mkPen(
                        color,
                        width=2
                    )
                )
            @inlineCallbacks
            def loop():
                voltages = yield protocol.sendCommand('get-voltages')
                for channel, voltage in voltages.items():
                    xData, yData = data[channel]
                    yData.pop(0)
                    scale = yield protocol.sendCommand(
                        'get-channel-parameter',
                        channel,
                        VM.MAX
                    )
                    yData.append(voltage)
                    plots[channel].setData(
                        xData,
                        [100.0 * voltage / scale for voltage in yData]
                    )
                if recordToggle.isToggled():
                    with open(self.fileName,'a') as file:
                        file.write(
                            '%s\n' % '\t'.join(
                                str(datum) for datum in (
                                    [time.time()] + [
                                        voltages[channel]
                                        for channel in
                                        recording
                                    ]
                                )
                            )
                        )
                        
                for channel in channels:
                    item = items[channel]
                    if item.checkState() is QtCore.Qt.CheckState.Checked:
                        if channel not in checked:
                            checked.append(channel)
                            plotWidget.addItem(
                                plots[channel]
                            )
                    elif channel in checked:
                        checked.remove(channel)
                        plotWidget.removeItem(
                            plots[channel]
                        )
                callbackRate = yield protocol.sendCommand('get-callback-rate')
                yield sleep(1.0 / callbackRate)
                loop()

            QtGui.QWidget.__init__(self)
            self.setLayout(QtGui.QHBoxLayout())
            
            plotWidget = pg.PlotWidget()
            self.layout().addWidget(plotWidget,1)

            controlsLayout = QtGui.QVBoxLayout()
            self.layout().addLayout(controlsLayout)
            
            listWidget = QtGui.QListWidget()
            listWidget.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
            listWidget.setContextMenuPolicy(
                QtCore.Qt.ContextMenuPolicy.CustomContextMenu
            )
            listWidget.customContextMenuRequested.connect(
                partial(
                    rightClicked,
                    listWidget
                )
            )
            controlsLayout.addWidget(listWidget)
            controlsLayout.addStretch(1)
            channels = yield protocol.sendCommand('get-channels')
            data = {
                channel:(
                    range(self.HISTORY),
                    [0] * self.HISTORY
                ) for index, channel in enumerate(channels)
            }
            colors = {
                channel:QtGui.QColor.fromHsv(
                    int(
                        255 * float(index) / len(channels)
                    ),
                    255,
                    255
                ) for index, channel in enumerate(channels)
            }
            plots = {
                channel:pg.PlotDataItem(
                    data[channel][0],
                    data[channel][1],
                    name=channel,
                    pen=pg.mkPen(
                        colors[channel],
                        width=2
                    )
                ) for channel in channels
            }
            items = {}
            for index, channel in enumerate(channels):
                description = yield protocol.sendCommand(
                    'get-channel-parameter',
                    channel,
                    VM.DESCRIPTION
                )
                listWidgetItem = QtGui.QListWidgetItem()                
                listWidgetItem.setData(self.ID_ROLE,channel)
                listWidgetItem.setBackground(QtGui.QBrush(colors[channel]))
                listWidget.addItem(listWidgetItem)
                items[channel] = listWidgetItem
                setText(channel)
            for index in range(listWidget.count()):
                listWidget.item(index).setCheckState(QtCore.Qt.CheckState.Unchecked)                                             
            def onChannelParameterChanged(channel,parameter,value):
                setText(channel)
            protocol.messageSubscribe(
                'channel-parameter-changed',
                partial(
                    apply,
                    onChannelParameterChanged
                )                
            )
            checked = []
            recording = []            
            recordToggle = ToggleObject()
            def onRecordStartRequested():
                for channel in channels:
                    item = items[channel]
                    if item.checkState() is QtCore.Qt.CheckState.Checked:
                        recording.append(channel)
                        item.setForeground(
                            QtGui.QBrush(
                                QtGui.QColor('red')
                            )
                        )
                relPath, fileName = filenameGen(self.MEASUREMENT_TYPE)
                absPath = os.path.join(POOHDATAPATH,relPath)
                checkPath(absPath)
                self.fileName = os.path.join(absPath,fileName)
                with open(self.fileName,'w') as file:
                    file.write(
                        '%s\n' % '\t'.join(
                            ['time'] + [
                                items[channel].text().replace('\t','_')
                                for channel in
                                recording
                            ]
                        )
                    )
                recordToggle.toggle()
            recordToggle.activationRequested.connect(onRecordStartRequested)
            def onRecordStopRequested():
                while recording:
                    items[recording.pop()].setForeground(
                        QtGui.QBrush(
                            QtGui.QColor('black')
                        )
                    )
                recordToggle.toggle()
            recordToggle.deactivationRequested.connect(onRecordStopRequested)
            controlsLayout.addWidget(
                ToggleWidget(
                    recordToggle,
                    ('record','stop')
                )
            )
            loop()
            
        init()
        
        # plotter = PlotWidget()
        # self.plot = plotter.plot()
        # self.layout().addWidget(plotter,1)
        # self.filename = None
        # self.fileObj = None
        
        # voltages = [0] * MAX
        
        # def onVoltagesAcquired(data):
        #     datum = data[self.channel] *1000
        #     lcd.display(datum)
        #     voltages.pop(0)
        #     voltages.append(datum)
        #     self.plot.setData(range(len(voltages)),voltages)
        #     if self.filename is not None:
        #         timeStamp = datetime.datetime.now() - self.startTime
        #         timeStampStr = str(timeStamp.seconds)+'.'+str(timeStamp.microseconds/1000).zfill(3)
        #         csvLine = timeStampStr+','+str(datum)+'\n'
        #         self.fileObj.write(csvLine)


        # controlPanel = QtGui.QHBoxLayout()
        # controlPanel.addStretch(1)

        # vmCombo = QtGui.QComboBox()
        # vmCombo.currentIndexChanged[unicode].connect(
        #     partial(setattr,self,'channel')
        # )
        # vmCombo.setCurrentIndex(0)
        # protocol.sendCommand('get-channels').addCallback(vmCombo.addItems)

        # controlPanel.addWidget(vmCombo)

        # def recButFunc():
        #     #if filename isn't set, initialize a file and filewriter to write to
        #     if self.filename == None:
        #         vmName = vmCombo.currentText()
        #         subfolder = os.path.join('voltmeterLog',vmName)
        #         relPath, self.filename = filenameGen(subfolder)
        #         absPath = os.path.join(POOHDATAPATH,relPath)
        #         checkPath(absPath)
        #         self.filename = os.path.join(absPath,self.filename+'.csv')
        #         self.fileObj = open(self.filename, 'wb')
        #         self.startTime = datetime.datetime.now()
        #         recordButton.setText('logging...')
        #     #if there is a filename, close the file and set filename to none
        #     else:
        #         self.filename = None
        #         self.fileObj.close()
        #         recordButton.setText('start log')
                
        # recordButton = QtGui.QPushButton('log')
        # recordButton.clicked.connect(recButFunc)
        # controlPanel.addWidget(recordButton)

        # lcd = QtGui.QLCDNumber(5)
        # lcd.setSegmentStyle(lcd.Flat)

        # controlPanel.addWidget(lcd)

        # self.layout().addLayout(controlPanel)
        
        # @inlineCallbacks
        # def loop():
        #     voltages = yield protocol.sendCommand('get-voltages')
        #     onVoltagesAcquired(voltages)
        #     yield sleep(SLEEP)
        #     loop()
        # loop()

@inlineCallbacks
def main():
    protocol = yield getProtocol(URL)
    widget = VoltMeterWidget(protocol)
    container.append(widget)
    widget.show()

if __name__ == '__main__':
    container = []
    main()
    reactor.run()
