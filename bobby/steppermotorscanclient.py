from abclient import getProtocol
from consoleclient import ConsoleClient, runConsoleClient, consoleCommand
from abbase import log, getType, selectFromList, getDigit
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred, succeed
from twisted.internet import reactor
from twisted.internet.threads import deferToThread
from sitz import VOLTMETER_SERVER
from scan import Scan, StepperMotorScanInput, VoltMeterScanOutput
from steppermotorserver import getStepperMotorNameURL

class StepperMotorScanClient(ConsoleClient):
    __ccname__ = 'stepper motor scan client'    

    def __init__(self,scan):
        self.scan = scan
        ConsoleClient.__init__(self)        

    @consoleCommand('perform scan','performs scan of stepper motor while monitoring voltage')
    @inlineCallbacks
    def performScan(self):
        start = yield getType(int,'enter starting position: ')
        stop = yield getType(int,'enter ending position: ')
        step = yield getDigit('enter number of steps to move between acquisitions: ')
        wait = yield getType(float,'enter time (in seconds) to wait between acquisitions: ')
        def onStep(position,power):
            print '%05d: %s' % (position,'+' * abs(int(1000 * power)))
            return succeed(True)
        yield self.scan.doScan(start,stop,step,wait,onStep)

@inlineCallbacks
def main():
    smName, smURL = yield getStepperMotorNameURL()
    smp = yield getProtocol(smURL)
    vmp = yield getProtocol(VOLTMETER_SERVER)
    channels = yield vmp.sendCommand('get-channels')
    channel = yield selectFromList(channels,'select channel to monitor during scan')
    smsi = StepperMotorScanInput(smp)
    vmso = VoltMeterScanOutput(vmp,channel)
    StepperMotorScanClient.__ccname__ = '(%s) sm scan' % smName
    runConsoleClient(StepperMotorScanClient,Scan(smsi,vmso))    
if __name__ == '__main__':
    main()
    reactor.run()
