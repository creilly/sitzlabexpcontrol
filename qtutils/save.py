'''
by stevens4

creates a widget that has a save button that will write dataArray to filename
'''


from PySide import QtGui


class SaveWidget(QtGui.QWidget):
    def __init__(self):
        saveLayout = QtGui.QVBoxLayout()
        self.setlayout(saveLayout)
        
        self.dataArray = None
        self.filename = None
        
        def getData(self):
            self.dataArray = np.asarray(
                [self.x,self.y,self.err],
                dtype=np.dtype(np.float32)
            )
            
        
        def onSaveClicked(self):
            self.getData()
            
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