class WavelengthClient:
    def __init__(self,wavelength_protocol):
        self.wavelength_protocol=wavelength_protocol

    def calibrateWavelength(self,wavelength):
        return self.wavelength_protocol.sendCommand('calibrate-wavelength',wavelength)

    def calibrateCrystal(self,crystalID):
        return self.wavelength_protocol.sendCommand('calibrate-crystal',crstyalID)

    def isTracking(self):
        return self.wavelength_protocol.sendCommand('is-tracking')

    def toggleTracking(self):
        return self.wavelength_protocol.sendCommand('toggle-tracking')

    def getWavelength(self):
        return self.wavelength_protocol.sendCommand('get-wavelength')

    def setWavelength(self,wavelength):
        return self.wavelength_protocol.sendCommand('set-wavelength',wavelength)

    def cancelWavelengthSet(self):
        return self.wavelength_protocol.sendCommand('cancel-wavelength-set')




