## BOILERPLATE ##
import sys
from PySide import QtGui, QtCore
if QtCore.QCoreApplication.instance() is None:    
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install()
## BOILERPLATE ##
from goto import MIN, MAX, PRECISION, SLIDER, GotoWidget
from config.steppermotor import PDL, KDP, BBO, SM_CONFIG
from qtutils.dictcombobox import DictComboBox
from qtutils.toggle import ToggleObject, ToggleWidget
from qtutils.label import LabelWidget
from qtutils.qled import LEDWidget
from steppermotorclient import StepperMotorClient
from twisted.internet.defer import inlineCallbacks
from functools import partial
from sitz import WAVELENGTH_SERVER, TEST_WAVELENGTH_SERVER, STEPPER_MOTOR_SERVER, TEST_STEPPER_MOTOR_SERVER, compose

CRYSTALS = {
    id: SM_CONFIG[id]['name'] for id in (KDP,BBO)
}

class TrackingWidget(QtGui.QWidget):
    def __init__(self,wavelengthProtocol,stepperMotorProtocol):
        QtGui.QWidget.__init__(self)
        
        self.setLayout(QtGui.QVBoxLayout())

        ##########
        ## goto ##
        ##########
        
        gotoWidget = GotoWidget(
            {
                MIN:24100,
                MAX:24500,
                PRECISION:2,
                SLIDER:2.0
            }
        )
        self.layout().addWidget(gotoWidget)

        # send command to tracking server when goto requested
        @inlineCallbacks
        def onGotoRequested(payload):
            position, deferred = payload
            yield wavelengthProtocol.sendCommand('set-wavelength',position)
            deferred.callback(None)
        gotoWidget.gotoRequested.connect(onGotoRequested)

        # handle update requests (should the position fall out of sync)
        def onUpdateReqested():
            wavelengthProtocol.sendCommand('get-wavelength').addCallback(gotoWidget.setPosition)
        gotoWidget.updateRequested.connect(onUpdateReqested)
        
        # send cancel request when goto widget requests
        gotoWidget.cancelRequested.connect(partial(wavelengthProtocol.sendCommand,'cancel-wavelength-set'))
        
        # set goto widget position on pdl position change
        StepperMotorClient(stepperMotorProtocol,PDL).addListener(
            StepperMotorClient.POSITION,
            lambda _:wavelengthProtocol.sendCommand('get-wavelength').addCallback(gotoWidget.setPosition)
        )
        
        # initialize position of goto widget
        wavelengthProtocol.sendCommand('get-wavelength').addCallback(gotoWidget.setPosition)        
                
        #########################
        ## crystal calibration ##
        #########################

        tuningGB = QtGui.QGroupBox('tune crystal')
        tuningLayout = QtGui.QHBoxLayout()
        tuningGB.setLayout(tuningLayout)

        # button to tune calibration #

        tuningButton = QtGui.QPushButton('set tuned')

        tuningLayout.addWidget(tuningButton)

        # combo box to select crystal #

        tuningCombo = DictComboBox(CRYSTALS)

        tuningLayout.addWidget(tuningCombo)

        # connect button to combo

        tuningButton.clicked.connect(
            compose(
                partial(
                    wavelengthProtocol.sendCommand,
                    'calibrate-crystal'
                ),
                tuningCombo.getCurrentKey
            )
        )

        self.layout().addWidget(LabelWidget('tuning',tuningLayout))

        #####################
        ## tracking toggle ##
        #####################

        toggleLayout = QtGui.QHBoxLayout()        

        toggle = ToggleObject()

        # toggle tracking server on toggle request
        toggle.toggleRequested.connect(
            partial(
                wavelengthProtocol.sendCommand,
                'toggle-tracking'
            )
        )

        # toggle widget upon receipt of tracking change server notification
        wavelengthProtocol.messageSubscribe(
            'tracking-changed',
            lambda _:toggle.toggle()
        )

        # create toggle widget
        toggleLayout.addWidget(ToggleWidget(toggle,('track','stop')),1)        

        # have pretty light
        led = LEDWidget()
        toggle.toggled.connect(led.toggle)

        toggleLayout.addWidget(led)

        self.layout().addWidget(LabelWidget('tracking',toggleLayout))

        # init tracking toggle
        def initTracking(tracking):
            if tracking: toggle.toggle()            
        wavelengthProtocol.sendCommand('is-tracking').addCallback(initTracking)
        
@inlineCallbacks
def main():
    import sys
    from ab.abclient import getProtocol
    DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'
    wavelengthProtocol = yield getProtocol(TEST_WAVELENGTH_SERVER)
    stepperMotorProtocol = yield getProtocol(
        TEST_STEPPER_MOTOR_SERVER if DEBUG else STEPPER_MOTOR_SERVER
    )
    #memory management nonsense
    container.append(TrackingWidget(wavelengthProtocol,stepperMotorProtocol))
    container[0].show()

if __name__ == '__main__':
    from twisted.internet import reactor
    container = []
    main()
    reactor.run()