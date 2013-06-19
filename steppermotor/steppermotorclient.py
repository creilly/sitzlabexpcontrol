from twisted.internet.defer import inlineCallbacks
from operator import contains
from scan.input import IntervalScanInput
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

class ChunkedStepperMotor(StepperMotorClient):
    def __init__(self,protocol,duration=1.0):
        StepperMotorClient.__init__(self,protocol)
        self.duration = duration
        
    @inlineCallbacks
    def setPosition(self,position):
        self.abort = False
        start = yield self.getPosition()
        stop = position
        rate = yield self.getStepRate()
        step = rate * self.duration
        def callback(_,output):
            return not output
        yield Scan(
            IntervalScanInput(
                self.setPosition,
                start,
                stop,
                step
            ),
            partial(getattr,self,'abort')
            callback
        ).start()
        position = yield self.getPosition()
        returnValue(position)
        
    def cancel(self):
        self.abort = True

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
