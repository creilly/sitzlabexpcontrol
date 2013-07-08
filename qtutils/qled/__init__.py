from PySide import QtGui, QtCore
from functools import partial
import sys
from os import path

fullPath = partial(path.join,path.dirname(__file__))
LED_ON = fullPath('led_on.png')
LED_OFF = fullPath('led_off.png')

class LEDWidget(QtGui.QLabel):

    def __init__(self, initialState = False):
        QtGui.QLabel.__init__(self)
        self.ledOn = QtGui.QPixmap(LED_ON)
        self.ledOff = QtGui.QPixmap(LED_OFF)
        self.toggle(initialState)

        self.isToggled = partial(getattr,self,'toggled')

    def toggle(self,state=None):
        if state is None:
            state = not self.toggled
        self.toggled = state
        self.setPixmap(self.ledOn if state else self.ledOff)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    widget = QtGui.QWidget()
    led = LEDWidget(True)
    widget.setLayout(QtGui.QHBoxLayout())
    widget.layout().addWidget(led)
    QtCore.QTimer.singleShot(2000,lambda:led.toggle(False))
    widget.show()
    sys.exit(app.exec_())
