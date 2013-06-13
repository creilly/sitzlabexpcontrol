from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:
    import sys, qt4reactor
    app = QtGui.QApplication(sys.argv)
    qt4reactor.install()
from steppermotorgui import StepperMotorWidget
from PySide import QtGui
from toggle import ClosedToggle, ToggleWidget
from twisted.internet.defer import inlineCallbacks
from qled import LEDWidget
from trackingclient import TrackingClient
from steppermotorserver import getConfig
from abclient import getProtocol
from abbase import sleep
from steppermotorclient import StepperMotorClient

DEBUG = False

def frameWidget(widget,title):
    g = QtGui.QGroupBox(title)
    l = QtGui.QVBoxLayout()
    l.addWidget(widget)
    g.setLayout(l)
    return g

def frameLayout(layout,title):
    g = QtGui.QGroupBox(title)
    g.setLayout(layout)
    return g

def getPDLWidget(client,title):
    layout = QtGui.QVBoxLayout()
    lcd = QtGui.QLCDNumber(5)
    lcd.setSmallDecimalPoint(True)
    lcd.setSegmentStyle(lcd.Flat)
    @inlineCallbacks
    def getNextDisplay():
        wavelength = yield client.getWavelength()
        lcd.display(
            '%.2f' % (wavelength-24000.0)
        )
    client.setPositionListener(lambda _:getNextDisplay())
    layout.addWidget(frameWidget(lcd,'wavelength'))
    layout.addWidget(StepperMotorWidget(client))
    getNextDisplay()
    return frameLayout(layout,title)

def getCrystalWidget(client,title):
    
    layout = QtGui.QVBoxLayout()
    layout.addWidget(StepperMotorWidget(client),1)

    trackingLayout = QtGui.QGridLayout()
    
    toggle = ClosedToggle(False)
    toggle.activated.connect(client.startTracking)
    toggle.deactivated.connect(client.stopTracking)
    
    trackingLayout.addWidget(ToggleWidget(toggle),0,0,1,3)

    led = LEDWidget(False)
    toggle.toggled.connect(led.toggle)
    trackingLayout.addWidget(led,1,0,1,1)

    calibrateButton = QtGui.QPushButton('set tuned')
    calibrateButton.clicked.connect(client.calibrateCrystal)

    trackingLayout.addWidget(calibrateButton,1,2,1,1)

    layout.addWidget(frameLayout(trackingLayout,'tracking'))
    return frameLayout(layout,title)        
        
if __name__ == '__main__':
    from twisted.internet import reactor
    from sitz import compose
    from functools import partial
    references = []
    @inlineCallbacks
    def main():
        widget = QtGui.QWidget()
        references.append(widget)
        layout = QtGui.QHBoxLayout()
        widget.setLayout(layout)
        crystalKeys = ((TrackingClient.TEST,'DEBUG'),) if DEBUG else ((TrackingClient.KDP,'KDP'),(TrackingClient.BBO,'BBO'))
        for crystalKey, title in crystalKeys:
            client = yield TrackingClient.getTrackingClient(crystalKey)
            yield client.calibrateWavelength()
            layout.addWidget(getCrystalWidget(client,title))
        layout.addWidget(
            getPDLWidget(
                client.wavelengthClient,
                'debug pdl' if DEBUG else 'pdl'
            )            
        )
        widget.setWindowTitle(
            '%s tracking client' % ('debug' if DEBUG else 'crystal')
        )
        widget.show()
    main()
    reactor.run()
    
