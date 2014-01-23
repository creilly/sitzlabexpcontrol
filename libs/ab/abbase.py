"""
some utility functions for network /
asynchronous programmingr
"""

from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from twisted.internet import reactor
from twisted.internet.threads import deferToThread
from functools import partial
import sys
from sitz import SITZ_RPC_URI, SITZ_MESSAGE_URI, compose

def sleep(secs):
    """
    non-blocking version of time.sleep

    @param secs: time to sleep (in seconds)
    @type secs: float

    @returns: Deferred that returns a result    
        of C{None} after specified delay
    """
    d = Deferred()
    reactor.callLater(secs, d.callback, None)
    return d

def getUserInput(prompt):
    """
    non-blocking version of raw_input

    @returns: Deferred that returns raw
        user input
    """
    return deferToThread(partial(raw_input,'%s:\t' % prompt))
    
@inlineCallbacks
def getValidatedInput(
        validator = lambda x: True,
        warning = 'invalid input',
        getInput = partial(getUserInput,'enter input: ')
):
    """
    get validated input from user.

    @param validator: function I{f(x)} that
        takes in data returned by B{getInput}.
        if B{validator} returns false, issue
        additional request to B{getInput},
        otherwise return input to caller of
        B{getValidatedInput}.

    @param warning: printed to screen when
        presented with invalid input
    @type warning: string

    @param getInput: invoked to retrieve
        user input. default is
        L{getUserInput} with prompt
        of 'enter input'
    @type getInput: callable
    """
    result = yield getInput()
    if not validator(result):
        print warning
        result = yield getValidatedInput(validator,warning,getInput)
    returnValue(result)

def getDigit(prompt='enter digit'):
    return getValidatedInput(
        lambda input: input.isdigit(),
        'must be digit',
        partial(getUserInput,prompt)        
    ).addCallback(int)

def isType(type,input):
    """
    boolean test of data type

    @param type: data type

    @param input: object to be tested
    """
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
    """
    get the index of user-selected
    object contained in a list

    @param l: list from which the index of
        an object is selected.

    @returns: integer index of selected object
    """
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
    """
    get an object selected by a user from
    a list.
    """
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

if __name__ == '__main__':
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
    from twisted.internet import reactor
    testInput()
    reactor.run()
    
