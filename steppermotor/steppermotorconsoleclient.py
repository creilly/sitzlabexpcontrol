from abclient import getProtocol
from consoleclient import ConsoleClient, runConsoleClient, consoleCommand
from abbase import log, getType
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from twisted.internet import reactor
from steppermotorclient import StepperMotorClient
from steppermotorserver import getStepperMotorURL, getStepperMotorOptions

class StepperMotorConsoleClient(ConsoleClient):
    __ccname__ = 'stepper motor client'    
    def __init__(self,client):
        self.client = client
        ConsoleClient.__init__(self)
    @consoleCommand('get position','query the position of the stepper motor')
    def getPosition(self):
        return self.client.getPosition()

    @consoleCommand('set position','sets the position of the stepper motor')
    @inlineCallbacks
    def _setPosition(self):
        position = yield getType(int,'input position: ')
        yield self.client.setPosition(position)

    @consoleCommand('set step rate','set the stepping rate of the motor')
    @inlineCallbacks
    def _setStepRate(self):
        rate = yield getType(float,'enter stepping rate (in Hz): ')
        yield self.client.setStepRate(rate)

    @consoleCommand('get step rate','get the stepping rate of the motor')
    def _getStepRate(self):
        return self.client.getStepRate()

@inlineCallbacks
def main():
    options = yield getStepperMotorOptions()
    url = yield getStepperMotorURL(options)
    StepperMotorClient.__ccname__ = '(%s) sm client' % options['name']
    protocol = yield getProtocol(url)
    smc = StepperMotorClient(protocol)
    runConsoleClient(
        StepperMotorConsoleClient,
        smc
    )
if __name__ == '__main__':
    main()
    reactor.run()
