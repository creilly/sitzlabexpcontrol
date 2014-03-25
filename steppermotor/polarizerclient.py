class PolarizerClient:
    def __init__(self,polarizer_protocol):
        self.polarizer_protocol=polarizer_protocol

    def calibrateAngle(self,angle):
        return self.polarizer_protocol.sendCommand('calibrate-angle',angle)
        
    def getAngle(self):
        return self.polarizer_protocol.sendCommand('get-angle')
        
    def setAngle(self,angle):
        return self.polarizer_protocol.sendCommand('set-angle',angle)
        
    def cancelAngleSet(self):
        return self.polarizer_protocol.sendCommand('cancel-angle-set')