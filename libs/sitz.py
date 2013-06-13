from copy import copy
from datetime import datetime
import ConfigParser

class SitzException(Exception): pass

# get timestamp for file names with optional appended name
def getTimeStampFileName(name=None,extension='dat'):
    dateFormatList = ['%' + c for c in ('Y','m','d','H','M','S')]
    if name is not None: dateFormatList.append(name)
    dateFormatString = '-'.join(dateFormatList)
    return '%s.%s' % (
        datetime.strftime(
            datetime.now(),
            dateFormatString
        ),
        extension
    )


#FUNCTION COMPOSITION (USEFUL FOR CALLBACKS)
def compose(func_1, func_2):
    """
    compose(func_1, func_2) -> function

    The function returned by compose is a composition of func_1 and func_2.
    That is, compose(func_1, func_2)(5) == func_1(func_2(5))
    """
    if not callable(func_1):
        raise TypeError("First argument to compose must be callable")
    if not callable(func_2):
        raise TypeError("Second argument to compose must be callable")

    def composition(*args, **kwargs):
        return func_1(func_2(*args, **kwargs))
    return composition

=======
class SitzException(Exception): pass
    
TAG = '__tag__'
def tagger(collectionName,tag=TAG):
    class metaclass(type):
        def __new__(cls,name,bases,attrs):
            commands = bases[0].__dict__.get(collectionName,[])
            attrs[collectionName] = commands
            for value in attrs.values():
                if hasattr(value,tag):
                    commands.append(
                        {
                            tagger.CALLABLE: value,
                            tagger.NAME: getattr(value,tag)[0],
                            tagger.DESCRIPTION: getattr(value,tag)[1]
                        }
                    )                    
            return type.__new__(cls,name,bases,attrs)
        
    def decorator (name,description="no description"):
        def foo (bar):
            setattr(bar,tag,(name,description))
            return bar
        return foo
    return decorator, metaclass
    
tagger.CALLABLE = 0
tagger.NAME = 1
tagger.DESCRIPTION = 2

#functions for reading config files
def readConfigFile(fileToRead):
    Config = ConfigParser.ConfigParser()
    Config.read(fileToRead)
    return Config._sections

def ConfigSectionMap(config, section):
    dict = {}
    options = config.options(section)
    for option in options:
        try:
            dict[option] = config.get(section, option)
            if dict[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict[option] = None
    return dict

SITZ_RPC_URI = 'http://localhost/sitzRPC#'
SITZ_MESSAGE_URI = 'http://localhost/sitzMESSAGE#'

TEST_VOLTMETER_SERVER = 'ws://172.17.13.204:8789'
VOLTMETER_SERVER = 'ws://172.17.13.201:8789'
TEST_STEPPER_MOTOR_SERVER = 'ws://172.17.13.204:8788'
STEPPER_MOTOR_SERVER = 'ws://172.17.13.201:8788'
MESSAGE_SERVER = 'ws://172.17.13.204:8790'
SCAN_SERVER = 'ws://172.17.13.201:8787'
INSPECTOR_SERVER = 'ws://172.17.13.204:9001'
TEST_MANAGER_SERVER = 'ws://172.17.13.204:9002'
