from PySide import QtGui
'''

creates a widget that has a frame with a \
titled label around your contents

'''
class LabelWidget(QtGui.QGroupBox):
    def __init__(self,label,contents=None):
        QtGui.QGroupBox.__init__(self,label)
        if isinstance(contents,QtGui.QLayout):
            self.setLayout(contents)
        elif isinstance(contents,QtGui.QWidget):
            l = QtGui.QVBoxLayout()
            l.addWidget(widget)
            g.setLayout(l)
