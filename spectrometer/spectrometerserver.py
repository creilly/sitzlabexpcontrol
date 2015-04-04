from ab.abserver import BaseWAMP, command, runServer
from twisted.internet.defer  import Deferred, inlineCallbacks, returnValue
from twisted.internet  import reactor

import sys
from os import path

from config.serverURLs import SPECTROMETER_SERVER, TEST_SPECTROMETER_SERVER
import time
import datetime

#import numpy as np  !!! do NOT use numpy on servers. numpy arrays cannot be communicated over ip !!!

# for spectrometer hardware
import oceanoptics

DEBUG = len(sys.argv) > 1 and sys.argv[1] == 'debug'

INTEGRATION_TIME = .100 #seconds
RAW = False


class SpectrometerWAMP(BaseWAMP):
    UPDATE = .1 # duration between spectrum notifications
    __wampname__ = 'stepper motor server'
    MESSAGES = {
        'new-spectrum-available':'notify when new spectrum captured'
    }

    def initializeWAMP(self):
        # define read and write locks
        self.rlock = None
        self.wlock = None
        
        # connect to the spectrometer
        self.raw = bool(RAW)
        self.spectrometer = oceanoptics.USB2000plus()
        self.spectrometer.integration_time(time_sec=INTEGRATION_TIME)
        self.wl = list(self.spectrometer.wavelengths())
        self.sp = list(self.spectrometer.intensities())
        
        # read new values off of spectrometer, lock while reading or writing
        @inlineCallbacks
        def capture():
            yield self.rlock 
            self.wlock = Deferred()
            self.sp = list(self.spectrometer.intensities())
            time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            self.latestTime = time
            self.wlock.callback(None)
            self.wlock = None
            reactor.callLater(.1,capture)
            
        reactor.callInThread(capture)
        
        ## complete initialization
        BaseWAMP.initializeWAMP(self)
        
    @command('get-latest-spectrum','get a new spectrum')
    @inlineCallbacks
    def returnLatest(self):
        yield self.wlock
        self.rlock = Deferred()
        self.rlock.callback(None)
        self.rlock = None
        returnValue(self.sp)
    
    @command('get-wavelengths','get the spectrometers range')
    def returnWave(self):
        return self.wl
    
    @command('get-last-time','get the timestamp for the current spectrum')
    def returnTime(self):
        return self.latestTime
    
    @command('set-integration-time','set a new integration time in ms')
    def setIntegTime(self,newTime):
        print 'here'
        self.spectrometer.integration_time(time_sec=newTime)
        

def main():
    runServer(
        WAMP = SpectrometerWAMP, 
        URL = SPECTROMETER_SERVER if not DEBUG else TEST_SPECTROMETER_SERVER,
        debug = True,
        outputToConsole = False)
    
if __name__ == '__main__':
    main()
    reactor.run()
