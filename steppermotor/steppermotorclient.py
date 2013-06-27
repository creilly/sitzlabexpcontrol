from twisted.internet.defer import inlineCallbacks, returnValue
from scan import Scan
from scan.input import IntervalScanInput
from functools import partial

class StepperMotorClient:
    POSITION = 0
    RATE = 1
    MESSAGES = {POSITION:'position-changed',RATE:'step-rate-changed'}
    def __init__(self,protocol,id):        
        self.protocol = protocol
        self.id = id
        self.listeners = {message:{} for message in self.MESSAGES.keys()}

    def _sendCommand(self,command,*args):
        return self.protocol.sendCommand(command,self.id,*args)
        
    def getPosition(self):
        return self._sendCommand('get-position')
        
    def setPosition(self,position):
        return self._sendCommand('set-position',position)
        
    def setStepRate(self,rate):
        return self._sendCommand('set-step-rate',rate)

    def getStepRate(self):
        return self._sendCommand('get-step-rate')

    def getConfig(self):
        return self.protocol.sendCommand('get-configuration')

    """

    signs up listener for updates on THIS stepper motor (not all of them)

    types of message:
    
    StepperMotorClient.POSITION -> updates on position changes
    StepperMotorClient.RATE -> updates on stepping rate changes

    listener should be of the form:
    
    foo(data)

    where data is either the new position of stepping rate, depending on the message type
    """
    def addListener(self,message,listener):
        filter = partial(self._listenerFilter,listener)
        self.listeners[message][listener] = filter
        self.protocol.messageSubscribe(self.MESSAGES[message],filter)

    def removeListener(self,message,listener):
        self.protocol.messageUnsubscribe(self.MESSAGES[message],self.listeners[message].pop(listener))

    def _listenerFilter(self,listener,dataTuple):
        id, data = dataTuple
        if id == self.id:
            listener(data)

class ChunkedStepperMotorClient(StepperMotorClient):
    def __init__(self,protocol,id,duration=0.3):
        StepperMotorClient.__init__(self,protocol,id)
        self.duration = duration
        
    @inlineCallbacks
    def setPosition(self,position):
        self.abort = False
        start = yield self.getPosition()
        stop = position
        rate = yield self.getStepRate()
        step = rate * self.duration
        def onStep(input,output):
            print 'i:%s,\to:%s' % (input,output)
            return not self.abort
        yield Scan(
            IntervalScanInput(
                partial(
                    StepperMotorClient.setPosition,
                    self
                ),
                start,
                stop,
                step
            ).next,
            lambda:None,
            lambda a,b: not self.abort
        ).start()
        position = yield self.getPosition()
        returnValue(position)
        
    def cancel(self):
        self.abort = True
    
@inlineCallbacks
def main():
    from sitz import TEST_STEPPER_MOTOR_SERVER
    from ab.abbase import getUserInput, sleep
    from ab.abclient import getProtocol
    from twisted.internet.defer import Deferred
    ## connect to server
    protocol = yield getProtocol(TEST_STEPPER_MOTOR_SERVER)
    ## get sm configuration
    config = yield protocol.sendCommand('get-configuration')
    delta = 2000
    for id in config.keys():
        # create client
        client = ChunkedStepperMotorClient(protocol,id)

        ## register for position updates
        def log(prompt,x): print '%s: %s' % (prompt,x)
        listener = partial(log,'update for client %s' % client.id)
        client.addListener(client.POSITION,listener)

        ## change positions
        position = yield client.getPosition()
        delta /= 2
        yield client.setPosition(position + delta)

    position = yield client.getPosition()
    # demonstrate canceling capabilities
    delta = -10000
    d = Deferred()
    def onPositionChanged(newPosition):
        if d.called:
            print 'canceling!'
            client.cancel()
            client.removeListener(client.POSITION,onPositionChanged)
        else:
            print 'new pos: %d' % newPosition
    client.removeListener(client.POSITION,listener)
    client.addListener(client.POSITION,onPositionChanged)
    print ''
    yield sleep(.5)
    print 'starting long journey: press enter to quit'
    yield sleep(1.5)
    print ''
    e = client.setPosition(position+delta)
    yield getUserInput('')
    d.callback(None)
    yield e
    print 'shutting down'
    reactor.stop()

if __name__ == '__main__':
    from twisted.internet import reactor
    main()
    reactor.run()
