from PySide import QtGui, QtCore

class SqueezeRow(QtGui.QWidget):
    LEFT,RIGHT = 0,1
    def __init__(self,widget,align=RIGHT):
        QtGui.QWidget.__init__(self)
        
        layout = QtGui.QHBoxLayout()
        self.setLayout(layout)

        layout.addStretch(1)

        layout.insertWidget(
            {
                self.LEFT:0,
                self.RIGHT:1
            }[align],
            widget,
            0
        )