from websocketserver import WebSocketServer, command, runServer
import random
import math
import time

random.seed(None)

class DAQServer(WebSocketServer):

    def initialize(self):
        
        # establish connection
        print 'connecting...'
        time.sleep(.5)
        print '.......'
        time.sleep(.5)
        print 'connected!'

        self.tasks = {}
        self.devices = {
            'alpha':['ai%d' % i for i in range(5)],
            'beta':['ai%d' % i for i in range(3)],
            'gamma':['ai%d' % i for i in range(7)],
        }        

    def terminate(self):
        print 'shutting down'
        while self.tasks:
            task = self.tasks.keys()[0]
            print 'removing task: ', task
            self.removeTask(task)

    @command('devices')
    def getDevices(self,socket):
        return self.devices.keys()

    @command('create task')
    def createTask(self,socket,name):
        if name in self.tasks:
            return {'error':'name "%s" already taken' % name}
        self.tasks[name] = {
            'channels':{},
            'counter':0,
            'mean':float(random.randint(300,400)),
            'amplitude':float(random.randint(30,50)),
            'noise':random.randint(3,10),
            'length':float(random.randint(20,100))
        }

    @command('tasks')
    def getTasks(self,socket):
        return self.tasks.keys()

    @command('load task')
    def loadTask(self,socket,name):
        socket.error('no saved tasks to load')

    @command('saved tasks')
    def getSavedTasks(self,socket):
        return []
        
    @command('clear task')
    def clearTask(self,socket,task):
        self.removeTask(task)

    def removeTask(self,task):
        self.tasks.pop(task)
    
    @command('create channel')
    def createChannel(self,socket,task,physicalChannel,name):
        if name in self.tasks[task]['channels']:
            self.error(socket, 'already virtual channel with this name')
            return
        self.tasks[task]['channels'][name] = physicalChannel

    @command('virtual channels')
    def getVirtualChannels(self,socket,task):
        return self.tasks[task]['channels'].keys()

    @command('physical channels')
    def getPhysicalChannels(self,socket,device):
        return self.devices[device]

    @command('read sample')
    def readSample(self,socket,task):
        task = self.tasks[task]
        task['counter'] = task['counter'] + 1
        return task['mean'] + task['amplitude'] * math.sin( 2 * math.pi / task['length'] * task['counter']) + float(random.randint(-1 * task['noise'],task['noise']))
        

    @command('read samples')
    def readSamples(self,socket,task,numSamples):
        return self.error('not configured to read multiple samples')
        
if __name__ == "__main__":
    runServer(DAQServer(),8888) 

