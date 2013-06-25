'''
by stevens4. last mod: 2013/06/20

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

from sitz import readConfigFile, ConfigSectionMap, compose, printConfigDict

CONFIG = 'delayGeneratorServerConfig.ini'
dgDict = {}

def getConfig():
    config = readConfigFile(CONFIG)
    serverOptions = config["GlobalServerProperties"]
    del config["GlobalServerProperties"]
    print config
    print 'Configuring a server with these properties: '
    print '\n'.join('\t%s:\t%s' % (key, value) for key, value in serverOptions.items())
    return serverOptions, config

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
        self.dispatch('delay-changed',(dgName,delay))

@inlineCallbacks
def main():
    serverOptions, dgOptions = getConfig()
    url = serverOptions["url"]
    
    printConfigDict(dgOptions)
    
    configList = dgOptions.keys()
    if type(configList) is not list: configList = [configList] #if it is only 1 element, convert to list
    configList += ["Done"]

    while True:
        dgToAdd = yield selectFromList(configList,"Which delay generator to add?")
        if dgToAdd == "Done" or configList == ["Done"]: break
        if dgOptions[dgToAdd]["__name__"].startswith("Fake"):
            dgDict[dgOptions[dgToAdd]["__name__"]] = FakeDelayGenerator(dgOptions[dgToAdd]["usb_chan"])
        else:
           dgDict[dgOptions[dgToAdd]["__name__"]] = DelayGenerator(dgOptions[dgToAdd]["usb_chan"])
        configList.pop(configList.index(dgToAdd))
        

    
    runServer(WAMP = DelayGeneratorWAMP, URL = url,debug = True, outputToConsole=True)

    
    
if __name__ == '__main__':
    main()
    reactor.run()
