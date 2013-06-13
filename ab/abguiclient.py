import sys
from PySide import QtGui, QtCore

try:
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install()
except RuntimeError: pass

from PySide.QtCore import Signal
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from abclient import getProtocol
from functools import partial

class BaseMainWindow(QtGui.QMainWindow):
    disconnected = Signal(str)
    reconnected = Signal(str)
    DISCONNECTED = 0
    RECONNECTED = 1
    def __init__(self,alertConnectivity=True):
        QtGui.QMainWindow.__init__(self)
        
        if alertConnectivity:
            self.disconnected.connect(partial(self.onConnectivityChanged,self.DISCONNECTED))
            self.reconnected.connect(partial(self.onConnectivityChanged,self.RECONNECTED))
            
        self.protocols = {}
        self.protocolActions = {}
        self.protocolsMenu = self.menuBar().addMenu('&protocols')

    @inlineCallbacks
    def getProtocol(self,url,name=None):        
        if url not in self.protocols:
            try:
                p = yield getProtocol(url)
            except Exception, e:
                QtGui.QMessageBox.information(self,'connect failed','could not connect to %s (%s)' % ('unnamed' if name is None else name,url))
                raise e
            p.onClose = lambda a, b, c: self.onProtocolDisconnect(url)
            self.protocols[url] = p
            if url not in self.protocolActions:
                if name is None:
                    name, ok = QtGui.QInputDialog.getText(self,'name connection','enter alias for %s' % url)
                    name = name if ok else url
                a = self.protocolsMenu.addAction(name)
                a.triggered.connect(partial(self.getProtocol,url))
                self.protocolActions[url] = a
            else:
                self.reconnected.emit(url)            

            action = self.protocolActions[url]
            action.setEnabled(False)
        protocol = self.protocols[url]
        returnValue(protocol)

    def onProtocolDisconnect(self,url):
        del self.protocols[url]
        action = self.protocolActions[url]
        action.setEnabled(True)
        self.disconnected.emit(url)

    def onConnectivityChanged(self,status,url):
        action = self.protocolActions[url]
        title = {
            self.DISCONNECTED:'disconnected',
            self.RECONNECTED:'reconnected'
        }
        message = {
            self.DISCONNECTED:'lost connection to %s (%s)',
            self.RECONNECTED:'reconnected to %s (%s)'
        }
        QtGui.QMessageBox.information(
            self,
            title[status],
            message[status] % (
                action.text(),
                url
            )
        )

# parent must implement BaseMainWindow
class BaseWidget(QtGui.QWidget):
    def __init__(self,parent=BaseMainWindow()):
        QtGui.QWidget.__init__(self)
        self._parent = parent
        
    def getProtocol(self,url,name=None,onDisconnect=None):
        return self._parent.getProtocol(url,name)

def runWidget(name,Widget,*args,**kwargs):
    w = Widget(*args,**kwargs)
    w._parent.setCentralWidget(w)
    w._parent.setWindowTitle(name)
    w._parent.show()
    reactor.run()

def runMainWindow(MainWindow,*args,**kwargs):
    mw = MainWindow(*args,**kwargs)
    mw.show()
    reactor.run()

def main():
    runMainWindow(BaseMainWindow)

if __name__ == '__main__':
    main()
    
