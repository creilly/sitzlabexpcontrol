import json
import UserDict
from sitz import SitzException
from os import path

USED_CONSTANTS_FILE = path.join(path.dirname(__file__),'daqmx_constants_used.dat')
UNUSED_CONSTANTS_FILE = path.join(path.dirname(__file__),'daqmx_constants_unused.dat')

class DAQmxConstantsDict(object):
    def __init__(self):
        with open(USED_CONSTANTS_FILE,'r') as file:
            self.dict = json.loads(file.read())
        self.unused = None

    def __getitem__(self,key):
        if key in self.dict: return self.dict[key]
        if self.unused is None:
            with open(UNUSED_CONSTANTS_FILE,'r') as file:
                self.unused = json.loads(file.read())                
        if key in self.unused:
            self.dict[key] = self.unused[key]
            with open(USED_CONSTANTS_FILE,'w') as file:
                file.write(json.dumps(self.dict,indent=2,separators=(',',': '),sort_keys=True))
            return self.dict[key]
        raise SitzException('unknown DAQmx constant: %s' % key)

constants = DAQmxConstantsDict()
        


