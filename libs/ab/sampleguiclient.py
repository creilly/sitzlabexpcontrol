import sys
from PySide import QtGui
import qt4reactor

app = QtGui.QApplication(sys.argv)
qt4reactor.install()

from twisted.internet import reactor

from abclient import getProtocol
from abbase import parseCommandLineURL
from sitz import TEST_STEPPER_MOTOR_SERVER

from functools import partial

widget = QtGui.QWidget()
button = QtGui.QPushButton('get commands',parent = widget)

def onConnect(protocol):        
    def onClick():
        def onCommands(commands):
            QtGui.QMessageBox.information(widget,'commands','<br>'.join('%s: %s' %(name,desc) for name, desc in commands.items()))
        protocol.sendCommand('commands').addCallback(onCommands)
    button.clicked.connect(onClick)

getProtocol(parseCommandLineURL()).addCallback(onConnect)

widget.show()

reactor.runReturn()
app.exec_()
