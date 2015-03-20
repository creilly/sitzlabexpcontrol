'''
by stevens4

This is a tutorial program. This is the simplest program that gets voltages from a voltmeter server.

General design: (read bottom to top)
    - "if __name__ == '__main__':"
        + as long as you are running this program i.e. "python simple.py", do these things
        + as opposed to importing it
    - main(): 
        + define a protocol (a url that accepts plain text commands)
        + define a client object (object that has methods mapped to protocol's commands)
        + measure how often the server will have new voltages to be read (callback rate)
        + get these new voltages and print them while running
    - getVoltages():
        + voltages: a deferred that will have the new voltages once the server calls back (yield makes it be the voltages)
        + wait until the server has new voltages
        + return the values as a dictionary
    - the paragraphs above this are the imported functions, dictionary, and objects needed to run
    
    - general considerations & some notes:
        + the inlineCallbacks decorator is needed on any function that has a yield
        + yields are used so that command doesn't "block": the program can continue to function while waiting for new voltages
        + yields cannot be used outside a function and thus cannot be used in ipython
        + a program will need a function to define the protocol & client (in this case main()) that need yields, thus this function needs inlineCallbacks
        + this function will only need to be run once (not in a loop)
        + once that is done, you'll want to get parameters or values from a server periodically (in this case getVoltages()) that also needs inlineCallbacks
'''

# server calls
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from ab.abclient import getProtocol
from ab.abbase import sleep
from voltmeter.voltmeterclient import VoltMeterClient

# configuration parameters
from config.voltmeter import VM_SERVER_CONFIG


@inlineCallbacks
def getRange(vmClient,chan):
    from daqmx.task.ai import VoltMeter as VM
    rangeKey = VM.PARAMETERS[2][0]
    setRangeKey = yield vmClient.getChannelParameter(chan,rangeKey)
    range = VM.VOLTAGE_RANGES[setRangeKey][1]
    returnValue(range)

@inlineCallbacks
def getVoltages(vmClient,timeBetweenNewVoltages):
    voltages = yield vmClient.getVoltages()
    yield sleep(timeBetweenNewVoltages)
    returnValue(voltages)

@inlineCallbacks
def main():
    URL = VM_SERVER_CONFIG['url']
    protocol = yield getProtocol(URL)
    client = VoltMeterClient(protocol)
    callbackRate = yield client.getCallbackRate()
    timeBetweenNewVoltages = 1.0/callbackRate
    chanList = yield client.getChannels()
    chan = chanList[0]
    range = yield getRange(client,chan)
    print range
    
    while True:
        newVoltages = yield getVoltages(client,timeBetweenNewVoltages)
        print newVoltages

if __name__ == '__main__':
    main()
    reactor.run()
