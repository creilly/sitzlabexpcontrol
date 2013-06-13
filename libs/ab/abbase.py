from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from twisted.internet import reactor
from twisted.internet.threads import deferToThread
from functools import partial
import sys
from sitz import SITZ_RPC_URI, SITZ_MESSAGE_URI, compose

def sleep(secs):
    d = Deferred()
    reactor.callLater(secs, d.callback, None)
    return d

@inlineCallbacks
def getUserInput(prompt):
    result = yield deferToThread(partial(raw_input,prompt))
    returnValue(result)

@inlineCallbacks
def getValidatedInput(
        validator = lambda x: True,
        warning = 'invalid input',
        getInput = partial(getUserInput,'enter input')
):
    result = yield getInput()
    if not validator(result):
        print warning
        result = yield getValidatedInput(validator,warning,getInput)
    returnValue(result)

@inlineCallbacks
def getDigit(prompt='enter digit: '):
    result = yield getValidatedInput(
        lambda input: input.isdigit(),
        'must be digit',
        partial(getUserInput,prompt)        
    )
    returnValue(int(result))

def isType(type,input):
    try:
        type(input)
        return True
    except ValueError:
        return False

@inlineCallbacks
def getType(type,prompt=None):
    if prompt is None: prompt = 'enter %s: ' % type.__name__
    result = yield getValidatedInput(
        partial(isType,type),
        'must be castable into type %s' % type.__name__,
        partial(getUserInput,prompt)
    )
    returnValue(type(result))
        
@inlineCallbacks
def getFloat(prompt='enter float: '):
    result = yield getType(float,prompt)
    returnValue(result)

LIST_PROMPT = 'select index from list: '
# returns selected list index
@inlineCallbacks
def getListIndex(l,prompt=LIST_PROMPT):
    print prompt
    print '\n'.join('\t%d: %s' % (i,str(d)) for i, d in enumerate(l))
    index = yield getValidatedInput(
        lambda index: index < len(l),
        'input must be less than %d' % len(l),
        partial(getDigit,'-->: ')
    )
    returnValue(index)

@inlineCallbacks
def selectFromList(l,prompt=LIST_PROMPT):
    index = yield getListIndex(l,prompt)
    returnValue(l[index])

def parseCommandLineURL():
    formatWarning = 'format is IP and PORT (i.e. "python xxx.py 204 8788" for 172.17.13.204:8788)'
    if len(sys.argv) < 3:
        print formatWarning
        exit(0)    
    IP, PORT = sys.argv[1], sys.argv[2]
    if any(map(lambda d: not d.isdigit(),(IP,PORT))):
        print formatWarning
        exit(0)
    return 'ws://172.17.13.%s:%s' % (IP,PORT)

def log(x): print x

def uriFromCommand(command):
    return SITZ_RPC_URI + command

def uriFromMessage(message):
    return SITZ_MESSAGE_URI + message

@inlineCallbacks
def testInput():
    digit = yield getDigit()
    chars = [chr(i + 65) for i in range(5)]
    char = yield selectFromList(chars)
    num = yield getFloat()
    lists = [range(i) for i in range(4)]
    l = yield selectFromList(lists)
    number = yield getType(int)
    print digit, char, num, l
    reactor.stop()  

if __name__ == '__main__':
    from twisted.internet import reactor
    testInput()
    reactor.run()
    
