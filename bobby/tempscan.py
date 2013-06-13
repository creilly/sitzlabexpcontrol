from sitz import VOLTMETER_SERVER, getTimeStampFileName
from scan import Scan, StepperMotorScanInput, VoltMeterScanOutput
from steppermotorserver import getConfig
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue, succeed
from abclient import getProtocol
from typewriter import overwrite
import os

START = -1900
STOP = -1500
STEP = 5
WAIT = 0.500

CALLBACK_RATE = .5
SAMPLING_RATE = 5000.0

CRYSTAL = 'KDP'

DIR = 'tempscans'

METADATA_FILE = 'metadata.dat'

PARAMETERS = '\n'.join(
    '\t%s:\t%f' % (name,val) for name,val in (
        ('wait',WAIT),
        ('callback rate',CALLBACK_RATE),
        ('sampling rate',SAMPLING_RATE)
    )
)
@inlineCallbacks
def main():
    smp = yield getProtocol(getConfig()[CRYSTAL]['url'])
    smsi = StepperMotorScanInput(smp)
    vmp = yield getProtocol(VOLTMETER_SERVER)
    vmso = VoltMeterScanOutput(vmp) # get all channels
    scan = Scan(smsi,vmso)
    channels = yield vmp.sendCommand('get-channels')
    yield vmp.sendCommand('set-callback-rate',CALLBACK_RATE)
    yield vmp.sendCommand('set-sampling-rate',SAMPLING_RATE)
    scans = 0
    while True:
        fName = getTimeStampFileName(extension='csv')
        with open(os.path.join(DIR,METADATA_FILE),'a') as g:
            g.write('%s\n%s\n' % (fName,PARAMETERS))
        f = open(os.path.join(DIR,fName),'w')
        f.write(', '.join([CRYSTAL] + channels) + '\n')
        def onStep(position,voltages):
            data = [position] + [voltages[channel] for channel in channels]
            f.write(', '.join(str(d) for d in data) + '\n')
            return succeed(True)
        yield scan.doScan(START,STOP,STEP,WAIT,onStep)
        f.close()
        scans += 1
        overwrite( '%d scans complete' % scans )

main()
reactor.run()
    
    
