from config.steppermotor import PDL, KDP, BBO, SM_CONFIG
from qtutils.dictcombobox import DictComboBox

CRYSTALS = {
    id: SM_CONFIG[id]['name'] for id in (KDP,BBO)
}

class TrackingWidget(QtGui.QWidget):
    def __init__(self,trackingProtocol,stepperMotorProtocol):
        # initialize wavelength display
        lcd = QtGui.QLCDNumber(7)
        # get handle to pdl stepper motor
        pdl = StepperMotorClient(PDL,stepperMotorProtocol)
        # updates wavelength display with current wavelength
        def updateWavelength():
            wavelength = yield trackingProtocol.getWavelength()
            lcd.display(wavelength)
        # update display on pdl position change
        pdl.addListener(pdl.POSITION,lambda _:updateWavelength())
        # also update display on calibration changes
        trackingProtocol.messageSubscribe(
            'calibration-changed',
            updateWavelegnth
        )

        ## crystal calibration ##
        
        tuningGB = QtGui.QGroupBox('tune crystal')
        tuningLayout = QtGui.QHBoxLayout()
        tuningGB.setLayout(tuningLayout)

        # button to tune calibration #

        tuningButton = QtGui.QPushButton('set tuned')

        tuningLayout.addWidget(tuningButton)

        # combo box to select crystal #

        tuningCombo = DictComboBox(CRYSTALS)
        