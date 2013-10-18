'''
by stevens4. last mod: 2013/09/30

updated to allow for 'run all' command; config file now has a default delay 'delay'

updated to meet new configuration standard where ../config/delaygenerator.py has a
dictionary of all the required parameters

constructs a server to manage multiple delay generator objects. the objects are stored
in a dictionary with the key set to the NAME option under delayGeneratorServerConfig.ini.
each is an instance of a DelayGenerator object that handles the communication via USB to the
physical delay generator.

'''

from delaygenerator import DelayGenerator, FakeDelayGenerator

from functools import partial

from ab.abserver import BaseWAMP, command, runServer
from ab.abbase import getDigit, selectFromList, sleep

from twisted.internet.defer  import Deferred, inlineCallbacks, returnValue
from twisted.internet  import reactor
from twisted.internet.task import LoopingCall

import pprint

from config.delaygenerator import SERVER_CONFIG, DG_CONFIG, DEBUG_SERVER_CONFIG, DEBUG_DG_CONFIG

from sitz import compose, printDict, DELAY_GENERATOR_SERVER, DEBUG_DELAY_GENERATOR_SERVER

dgDict = {}

import sys
print sys.argv
DEBUG = len(sys.argv) > 1 and 'debug' in sys.argv
AUTORUN = len(sys.argv) > 1 and 'auto' in sys.argv
print 'debug: %s' % DEBUG
print 'autorun: %s' % AUTORUN

def addDelayGenerator(options):
    return DelayGenerator(options["usb_chan"])

class DelayGeneratorWAMP(BaseWAMP):
    __wampname__ = 'delay generator server'
    MESSAGES = {
        'delay-changed':'notify when delay changes'
    }

    def initializeWAMP(self):
        self.dgDict = dgDict
        BaseWAMP.initializeWAMP(self)
    
    @command('get-delays','query delay of ALL delay generators and return dict')
    def getDelays(self):
        return {name:dg.getDelay() for name,dg in self.dgDict.items()}

    @command('set-delay','set delay of specified delay generator')
    def setDelay(self,dgName,delay):
        self.dgDict[dgName].setDelay(delay)
        self.updateConfig()
        self.dispatch('delay-changed',(dgName,delay))
    
    def updateConfig(self):
        #writes all delay generators' delays to a file in config/ for reference
        lastConfName='../config/lastDelayConfigDEBUG.txt' if DEBUG else '../config/lastDelayConfig.txt'
        confFile = open(lastConfName,'w')
        for name, dg in self.dgDict.items():
            confFile.write(name+' '+str(dg.getDelay())+'\n')
        confFile.close()
        

def createDelayGenerator(name,dgOptions,dgDictionary):
    if name == "Done" or name == "Run All":
        return dgDictionary
    print 'created: ' + name + ' with a delay of ' + str(dgOptions['delay'])
    if DEBUG:
        dgDictionary[name] = FakeDelayGenerator(dgOptions)
    else:
        dgDictionary[name] = DelayGenerator(dgOptions)
    return dgDictionary
    
@inlineCallbacks
def main():
    url = DELAY_GENERATOR_SERVER if not DEBUG else DEBUG_DELAY_GENERATOR_SERVER
    dgOptions = DG_CONFIG if not DEBUG else DEBUG_DG_CONFIG
    print '\n\n\n'

    printDict(dgOptions)
    
    configList = dgOptions.keys()
    if type(configList) is not list: configList = [configList] #if it is only 1 element, convert to list
    configList += ["Run All"]
    configList += ["Done"]

    while True:
        print '\n\n\n'
        if len(configList) <= 2: break
        if AUTORUN:
            dgToAdd = "Run All"
        else:
            dgToAdd = yield selectFromList(configList,"Which delay generator to add?")
        if dgToAdd == "Done" or configList == ["Run All","Done"]: break
        if dgToAdd == "Run All":
            for thisDG in dgOptions.keys():
                dgDict.update(createDelayGenerator(thisDG,dgOptions[thisDG],dgDict))
                configList.pop(configList.index(thisDG))
        else:
            dgDict.update(createDelayGenerator(dgToAdd,dgOptions[dgToAdd],dgDict))
        configList.pop(configList.index(dgToAdd))
        
    runServer(
        WAMP = DelayGeneratorWAMP,
        URL = url,
        debug = True,
        outputToConsole=True
    )
    
if __name__ == '__main__':
    main()
    reactor.run()
