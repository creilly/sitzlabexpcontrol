import daqmx

_elements = {}

class RoverElement(object):
    props = []
    def __init__(self,state = {}):
        for prop in self.props:
            setattr(self,prop,state[prop])

    def toDict(self):
        return {
            prop:getattr(self,prop) for prop in self.props
        }

class Switch(RoverElement):
    
    INTERLOCK = True
    USER = False

    props = [
        'id',
        'name',
        'channel',
        'mode', # INTERLOCK or USER?
        'user', # USER on or off?
        'interlock', # INTERLOCK on or off?
        'fail' # Did we trip a interlock?
    ]
    
    def __init__(self,state):
        super(Switch,self).__init__(state)
        self.connect()

    def connect(self):
        taskName = self.id
        daqmx.createDOTask(taskName)
        self.task = daqmx.getTask(taskName)
        self.task.createChannel(self.channel,self.name)

    def write(self,state):
        daqmx.getTask(self.id).writeState(state)

    def getComputed(self):
        if self.fail: return False
        if self.mode is self.INTERLOCK: return self.interlock
        if self.mode is self.USER: return self.interlock

_elements['switch'] = Switch

class Interlock(RoverElement):
    
    FAIL_IF_ABOVE = True
    FAIL_IF_BELOW = False

    props = [
        'id',
        'name',
        'switch',
        'sensor',
        'defeated',
        'threshold',
        'polarity' # FAIL_IF_ABOVE or FAIL_IF_BELOW?
    ]

_elements['interlock'] = Interlock

class Sensor(RoverElement):
    props = [
        'id',
        'name',
        'channel'
    ]
    
    def __init__(self,state):
        super(Sensor,self).__init__(state)
        self.connect()

    def connect(self):
        taskName = self.id
        daqmx.createAITask(taskName)
        self.task = daqmx.getTask(taskName)
        self.task.createChannel(self.channel,self.name)

    def readSample(self):
        return self.task.readSample(str(self.id))

_elements['sensor'] = Sensor

class ElementDict(object):

    def __init__(self,elementClass,elements):
        self.ids = []
        for id,element in elements.items():
            self.ids.append(id)
            setattr(self,id,elementClass(element))

    def elements(self):
        return {id:getattr(self,id) for id in self.ids}

    def toDict(self):
        return {
            id:element.toDict() for id,element in self.elements().items()
        }            

class RoverState(object):

    dicts = _elements.keys()

    def __init__(self,state):
        for element in self.dicts:
            setattr(self,element,ElementDict(_elements[element],state[element]))

    def toDict(self):
        return {d:getattr(self,d).toDict() for d in self.dicts}

    @staticmethod
    def emptyState():
        return RoverState(
            {
                element:{} for element in _elements.keys()
            }
        )