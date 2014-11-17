#this must be run first before importing the alternate reactor to avoid a 
#conflict between the qt and twisted reactors
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install() 

# server calls
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from ab.abclient import getProtocol
from ab.abbase import selectFromList, sleep

# configuration parameters
from config.voltmeter import VM_SERVER_CONFIG, VM_DEBUG_SERVER_CONFIG
from config.filecreation import POOHDATAPATH

# base voltmeter functionality (for configuring channel parameters)
from daqmx.task.ai import VoltMeter as VM

# custom GUI libraries
from qtutils.toggle import ToggleObject, ToggleWidget
from qtutils.label import LabelWidget

# math libraries
import numpy as np
from math import log10

# plotting
import pyqtgraph as pg

# function manipulators for easier GUI programming
from sitz import compose
from functools import partial

# logging
import os.path
from filecreationmethods import filenameGen, checkPath
import time

# regular expressions
import re

# python types
from types import *

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

# defines the new window drawn on right clicking a channel tile.
# used to edit channel properties (e.g. range, termination)
class ChannelEditDialog(QtGui.QDialog):
    colorChanged = QtCore.Signal(QtGui.QColor)
    def __init__(self,protocol,channel,color,parent=None):
        @inlineCallbacks
        def init():
            QtGui.QDialog.__init__(self,parent)
            self.setWindowTitle('%s properties' % channel)
            layout = QtGui.QFormLayout()
            self.setLayout(layout)
            
            # create two lists pertaining to this channel's properties
            PARAM_KEYS,PARAM_NAMES = zip(*VM.PARAMETERS)

            # build a dictionary of dictionaries of the form [propertyKey]:{[propertyItems]:[value]}
            propDict = {}
            for propKey, propName in zip(PARAM_KEYS,PARAM_NAMES):
                value = yield protocol.sendCommand('get-channel-parameter',channel,propKey)
                propDict[propKey] = {}
                propDict[propKey]['name'] = propName
                propDict[propKey]['value'] = value
                if propKey == 0:  # physical channel property
                    propDict[propKey]['editor'] = None
                    propDict[propKey]['display'] = QtGui.QLabel(value)
                if propKey != 0:  # all other properties can be changed
                    propDict[propKey]['editor'] = partial(protocol.sendCommand,'set-channel-parameter',channel,propKey)
                    if type(value) is UnicodeType:
                        thisDisplayObj = QtGui.QLineEdit()
                        thisDisplayObj.setText(value)
                        thisDisplayObj.editingFinished.connect(
                            compose(
                                propDict[propKey]['editor'],
                                thisDisplayObj.text
                            )
                        )
                        propDict[propKey]['display'] = thisDisplayObj
                    
                    if type(value) is IntType:
                        thisDisplayObj = QtGui.QComboBox()
                        if propKey == 3:  #voltage range
                            for voltConfKey, voltConfVal in VM.VOLTAGE_RANGES:
                                thisDisplayObj.addItem(
                                    '%.2f (V)' % voltConfVal, voltConfKey
                                )
                        if propKey == 2: #terminal configuration
                            for termConfKey, _, termConfName in VM.TERMINAL_CONFIGS:
                                thisDisplayObj.addItem(
                                    termConfName,termConfKey
                                )
                        thisDisplayObj.setCurrentIndex(
                            thisDisplayObj.findData(value)
                        )
                        thisDisplayObj.currentIndexChanged.connect(
                            compose(
                                propDict[propKey]['editor'],
                                thisDisplayObj.itemData
                            )
                        )
                        propDict[propKey]['display'] = thisDisplayObj
                    
                    layout.addRow(propDict[propKey]['name'],propDict[propKey]['display'])
            
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

        
# defines the main window of the program which is a plotter with a control panel        
class VoltMeterWidget(QtGui.QWidget):    
    ID_ROLE = 999
    HISTORY = 200
    MEASUREMENT_TYPE = 'voltmeter'
    newBufferVal = False 
        
    @staticmethod
    def vrngk2v(k):
        vrngKeys, vrngVals = zip(*VM.VOLTAGE_RANGES)
        return vrngVals[vrngKeys.index(k)]
        
    def __init__(self,protocol):
        @inlineCallbacks
        def init():
            # to change displayed values of channel tiles
            @inlineCallbacks
            def setText(channel):
                description = yield protocol.sendCommand(
                    'get-channel-parameter',
                    channel,
                    VM.DESCRIPTION
                )
                voltageRange = yield protocol.sendCommand(
                    'get-channel-parameter',
                    channel,
                    VM.VOLTAGE_RANGE
                )
                voltageRange = self.vrngk2v(voltageRange)
                
                decimalPlaces = int(-1*log10(voltageRange)) + 1
                formatString = '%.' + str(decimalPlaces if decimalPlaces > 0 else 0) + 'f'
                tiles[channel].setText(
                    '%s\t%s\t%s V' % (
                        description,
                        channel,
                        (
                            formatString
                        ) % voltageRange
                    )
                )
            
            # to bring up channel edit dialogue
            def rightClicked(listWidget,p):
                item = listWidget.itemAt(p)
                if item is None: return
                channel = item.data(self.ID_ROLE)
                editDialog = ChannelEditDialog(protocol,channel,colors[channel],self)
                editDialog.colorChanged.connect(partial(colorChanged,channel))
                editDialog.show()
            
            # to update a channel's color
            def colorChanged(channel,color):
                colors[channel] = color
                tiles[channel].setBackground(color)
                plots[channel].setPen(
                    pg.mkPen(
                        color,
                        width=2
                    )
                )
            
            # the main execution loop
            @inlineCallbacks
            def loop():
                # get latest values
                voltages = yield protocol.sendCommand('get-voltages')
                for channel, voltage in voltages.items():
                    if self.newBufferVal == True: onBufferUpdate()
                    xData, yData = data[channel]
                    yData = np.delete(yData,0)
                                #scale = yield protocol.sendCommand(
                                #    'get-channel-parameter',
                                #    channel,
                                #    VM.VOLTAGE_RANGE
                                #)
                                #scale = self.vrngk2v(scale)
                    yData = np.append(yData,np.asarray(voltage))
                    plots[channel].setData(
                        xData,
                        yData
                    )
                    data[channel] = (xData, yData)
                
                # log values, if requested
                if recordToggle.isToggled():
                    nextLine = ()
                    for channel in recording:
                        nextLine.append(voltages[channel])
                    self.LogFile.update(nextLine)
                
                # update selected list
                for channel in channels:
                    tile = tiles[channel]
                    if tile.checkState() is QtCore.Qt.CheckState.Checked:
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
                
                # wait for server's callback rate (nom. 10Hz), iterate
                callbackRate = yield protocol.sendCommand('get-callback-rate')
                yield sleep(1.0 / callbackRate)
                loop()

            # define overall layout: graph to left of control panel
            QtGui.QWidget.__init__(self)
            self.setLayout(QtGui.QHBoxLayout())
            
            # define plot
            plotWidget = pg.PlotWidget()
            self.layout().addWidget(plotWidget,1)
            
            # define controls panel
            controlsLayout = QtGui.QVBoxLayout()
            self.layout().addLayout(controlsLayout)
                       
            # channel list
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
            
            # iterate through channels on server and populate dictionaries for data, colors, and plots
            channels = yield protocol.sendCommand('get-channels')
            channels = sorted(channels,key = lambda channel: int(re.search('\d+$',channel).group()))
            data =  {}
            colors =  {}
            plots =  {}
            tiles = {}
            for index, channel in enumerate(channels):
                data[channel] = (np.arange(self.HISTORY), np.zeros(self.HISTORY))
                colors[channel] = QtGui.QColor.fromHsv(
                    int(255*float(index)/len(channels)),
                    255,
                    255
                )
                plots[channel] = pg.PlotDataItem(
                    data[channel][0],
                    data[channel][1],
                    name=channel,
                    pen=pg.mkPen(colors[channel], width=2)
                )
                description = yield protocol.sendCommand(
                    'get-channel-parameter',
                    channel,
                    VM.DESCRIPTION
                )
                listWidgetTile = QtGui.QListWidgetItem()                
                listWidgetTile.setData(self.ID_ROLE,channel)
                listWidgetTile.setBackground(QtGui.QBrush(colors[channel]))
                listWidgetTile.setCheckState(QtCore.Qt.CheckState.Unchecked)
                listWidget.addItem(listWidgetTile)
                tiles[channel] = listWidgetTile
                setText(channel)
            
            # when a channel is updated, update its associated tile
            def onChannelParameterChanged(channel,parameter,value):
                setText(channel)
            protocol.messageSubscribe(
                'channel-parameter-changed',
                partial(
                    apply,
                    onChannelParameterChanged
                )                
            )
            
            # set up buffer function and spinbox
            def onBufferUpdate():
                oldBufferSize = data[channels[0]][0].size
                newBufferSize = bufferSpin.value()
                change = newBufferSize - oldBufferSize
                
                if change > 0:
                    backendToAdd = np.zeros(change)
                    for index, channel in enumerate(channels):
                        data[channel] = (
                            np.arange(newBufferSize),
                            np.hstack((backendToAdd,data[channel][1]))
                        )
                
                if change < 0:
                    for index, channel in enumerate(channels):
                        data[channel] = (
                            np.arange(newBufferSize),
                            np.delete(data[channel][1],np.arange(abs(change)))
                        )
                
                self.newBufferVal = False
            
            def newBufferToggle():
                self.newBufferVal = True
            
            bufferSpin = QtGui.QSpinBox()
            bufferSpin.setRange(1,100000)
            bufferSpin.setValue(self.HISTORY)
            controlsLayout.addWidget(LabelWidget('buffer',bufferSpin))
            bufferSpin.editingFinished.connect(newBufferToggle)
            
            # set up recording functions and buttons
            checked = []
            recording = []            
            recordToggle = ToggleObject()
            def onRecordStartRequested():
                # build a list of selected channels, record only those, set text color to red
                for channel in channels:
                    tile = tiles[channel]
                    if tile.checkState() is QtCore.Qt.CheckState.Checked:
                        recording.append(channel)
                        tile.setForeground(
                            QtGui.QBrush(
                                QtGui.QColor('red')
                            )
                        )
                
                # initialize logfile in today's folder / voltmeter / start time
                relPath, fileName = filenameGen(self.MEASUREMENT_TYPE)
                absPath = os.path.join(POOHDATAPATH,relPath)
                checkPath(absPath)
                logName = os.path.join(absPath,fileName+'.txt')
                self.LogFile = LogFile(logName)
                headerLine = ()
                for channel in recording:
                    headerLine.append(tiles[channel].text().replace('\t','_'))
                self.LogFile.update(headerLine)
                recordToggle.toggle()
            recordToggle.activationRequested.connect(onRecordStartRequested)
            
            def onRecordStopRequested():
                while recording:
                    tiles[recording.pop()].setForeground(
                        QtGui.QBrush(
                            QtGui.QColor('black')
                        )
                    )
                recordToggle.toggle()
            recordToggle.deactivationRequested.connect(onRecordStopRequested)
            
            # add record & stop buttons to layout
            controlsLayout.addWidget(ToggleWidget(recordToggle,('record','stop')))
            
            loop()   
        init()
        
    def closeEvent(self, event):
        event.accept()
        quit()


@inlineCallbacks
def main():
    protocol = yield getProtocol(URL)
    widget = VoltMeterWidget(protocol)
    container.append(widget)
    widget.show()
    widget.setWindowTitle('voltmeter gui ' + ('debug ' if DEBUG else 'real '))


if __name__ == '__main__':
    container = []
    main()
    reactor.run()
