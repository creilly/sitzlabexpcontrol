from twisted.internet.defer import inlineCallbacks
class StepperMotorClient:
    def __init__(self,protocol):        
        self.protocol = protocol
        
    def getPosition(self):
        return self.protocol.sendCommand('get-position')
        
    def setPosition(self,position):
        return self.protocol.sendCommand('set-position',position)

        
    def setStepRate(self,rate):
        return self.protocol.sendCommand('set-step-rate',rate)

    def getStepRate(self):
        return self.protocol.sendCommand('get-step-rate')

    def setPositionListener(self,listener):
        self.protocol.messageSubscribe('position-changed',listener)

    def removePositionListener(self,listener = None):
        self.protocol.messageUnsubscribe('position-changed',listener)

    def setRateListener(self,listener):
        self.protocol.messageSubscribe('step-rate-changed',listener)

    def removeRateListener(self,listener=None):
        self.protocol.messageUnsubscribe('step-rate-changed',listener)

class PDLClient(StepperMotorClient):
    def getWavelength(self):
        return self.protocol.sendCommand('get-wavelength')
        
    def setWavelength(self,wavelength):
        return self.protocol.sendCommand('set-wavelength',wavelength)


@inlineCallbacks
def main():
    from abclient import getProtocol    
    from steppermotorserver import getConfig
    from abbase import selectFromList
    server = yield selectFromList(getConfig().keys(),'select stepper motor')
    protocol = yield getProtocol(getConfig()[server]['url'])
    client = StepperMotorClient(protocol)
    position = yield client.getPosition()
    print 'pos: %d' % position
    print 'changing position by -10'
    yield client.setPosition(position-10)
    position = yield client.getPosition()
    print 'pos: %d' % position
    print 'shutting down'
    reactor.stop()

if __name__ == '__main__':
    from twisted.internet import reactor
    main()
    reactor.run()
