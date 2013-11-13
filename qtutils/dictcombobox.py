from PySide import QtGui, QtCore

#by stevens4, given a dictionary, populates a combo out of the values and emits
#the associated key via the choiceMade signal.
class DictComboBox(QtGui.QComboBox):
    currentKeyChanged = QtCore.Signal(object)
    def __init__(self,itemsDict=None):
        if itemsDict is None:
            itemsDict = {}
        #subclass combobox to pick from the values in dictionary and emit key
        self.itemsDict = itemsDict
        QtGui.QComboBox.__init__(self)
        for item in self.itemsDict.values(): self.addItem(item)
 
        def onCurrentIndexChanged(index):
            self.currentKeyChanged.emit(self.itemsDict.keys()[index])
        
        self.currentIndexChanged.connect(onCurrentIndexChanged)
    
    def updateCombo(self,itemsDict):
        self.clear()
        self.itemsDict = itemsDict
        for item in itemsDict.values(): self.addItem(item)

    def getCurrentKey(self):
        return self.itemsDict.keys()[self.currentIndex()]
        
 