from PySide import QtGui, QtCore

#by stevens4, given a dictionary, populates a combo out of the values and emits
#the associated key via the choiceMade signal.
class DictComboBox(QtGui.QComboBox):
    choiceMade = QtCore.Signal(object)
    def __init__(self,itemsDict):
        #subclass combobox to pick from the values in dictionary and emit key
        self.itemsDict = itemsDict
        QtGui.QComboBox.__init__(self)
        for item in self.itemsDict.values(): self.addItem(item)
 
        def madeChoice(index):
            self.choiceMade.emit(self.itemsDict.keys()[index])
        
        self.currentIndexChanged.connect(madeChoice)

    def getCurrentKey(self):
        return self.itemsDict.keys()[self.currentIndex()]
        
 