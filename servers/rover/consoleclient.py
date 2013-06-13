from functools import partial
from sitz import SitzException
from wsclient import run, sendCommand, log
from time import sleep
import pprint

class RoverException(Exception): pass

def getInput(level,*prompts):
    input =  raw_input(
        '\n'.join( [('\t' * level) + prompt for prompt in (prompts + ('-> ',))])
    )
    if input == '`': raise RoverException
    return input
    
state = {}

def _setProperty(element,id,property,value):
    sendCommand(
        'set property',
        {
            'element':element,
            'id':id,
            'property':property,
            'value':value
        },
        callback = lambda d: None
    )

def _getState():
    def callback(newState):
        global state
        state = newState
    sendCommand('get state',callback = callback)

def getState():
    _getState()
    pprint.pprint(state)

def catchInterrupt(foo):
    while True:
        try:
            foo()
        except RoverException:
            break
        except KeyError:
            print 'not a correct argument'
            break
        except SitzException, e:
            print e.message

def setProperty():
    
    def getElement():
        _getState()
        elements = {
            's':'switch',
            'r':'sensor',
            'i':'interlock'
        }
        element = elements[getInput(1,'element: ','(s)witch, senso(r), (i)nterlock').lower()]
        catchInterrupt(partial(getID,element))
              
    def getID(element):
        _getState()
        id =  getInput(2,'%s id: ' % element, ', '.join(state[element].keys()))
        catchInterrupt(partial(getProperty,element,id))

    def getProperty(element,id):
        _getState()
        property = getInput(3,'property:',', '.join(state[element][id].keys())).lower()
        catchInterrupt(partial(getValue,element,id,property))

    def getValue(element,id,property):
        _getState()
        current = state[element][id][property]
        value = getInput(4,'value:','current: ' + str(current))
        _setProperty(element,id,property,type(current)(value) if type(current) is not bool else (True if value.lower() == 'true' else False))
        _getState()


    catchInterrupt(partial(getElement))
    
commands = {
    's':getState,
    'p':setProperty
}

def hook(ws):
    getState()
    def getCommand():
        commands[getInput(0,'command:','get (s)tate, set (p)roperty').lower()]()
    catchInterrupt(getCommand)

run(hook)