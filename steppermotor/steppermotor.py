from sitz import SitzException
from functools import partial
from daqmx.task.co import COTask
from daqmx.task.do import DOTask
from daqmx.task.ci import CITask

from threading import Lock, Thread
from numpy import linspace
from time import sleep 

class BaseStepperMotor:

    # MAKE SURE TO CALL THIS IF YOU OVERRIDE    
    def __init__(self):
        self.busy = False        
        self.queue = []
        self.lock = Lock()
        self._position = 0

    def setPosition(self,position,callback=lambda:None):
        if self.busy:
            with self.lock:
                self.queue.append((position,callback))
            return
        self.busy = True
        self._setPosition(position,callback)

    def onPositionSet(self,callback):        
        callback()
        with self.lock:
            if self.queue:
                self._setPosition(*self.queue.pop(0))
                return
        self.busy = False

    # OVERRIDE THESE METHODS

    def _setPosition(self,position,callback):
        self._position = position
        self.onPositionSet(callback)

    def getPosition(self):
        return self._position

    def setStepRate(self,rate):
        pass

    def getStepRate(self): return 0.0
    
class StepperMotor(BaseStepperMotor):
    
    #BACKLASH = 155
    #BACKLASH = 285

    FORWARDS = 0
    BACKWARDS = 1
    
    def __init__(self,coChannel,doChannel,ciChannel,backlash):
        
        BaseStepperMotor.__init__(self)
        
        coTask, doTask, ciTask = COTask(), DOTask(), CITask()
        coTask.createChannel(coChannel)
        doTask.createChannel(doChannel)
        ciTask.createChannel(ciChannel)
        
        self.backlash = backlash
        
        self.direction = None        
        
        ciTask.start()
        
        self.coTask, self.doTask, self.ciTask = coTask, doTask, ciTask
        
        self.setPosition(-1)
        self.setPosition(0)
        
    def getPosition(self):
        return self.ciTask.readCounts() + (1 if self.direction is self.BACKWARDS else 0) * self.backlash

    def _setPosition(self,position,callback):
        delta = position - self.getPosition()
        direction = self.FORWARDS if delta > 0 else self.BACKWARDS
        if direction is not self.direction:
            self.doTask.writeState(
                {
                    self.FORWARDS:True,
                    self.BACKWARDS:False
                }[direction]
            )
        steps = abs(delta) + (self.backlash if direction is not self.direction else 0)
        self.coTask.generatePulses(steps,partial(self.onPositionSet,callback))
        self.direction = direction

    # set pulse rate in Hz
    def setStepRate(self,rate):
        self.coTask.configureTiming(0.5 / rate,0.5 / rate)

    def getStepRate(self):
        highTime, lowTime = self.coTask.getTimingConfiguration()
        period = highTime + lowTime
        rate = 1.0 / period
        return rate

class BlockingStepperMotor:
    def __init__(self,stepperMotor):        
        self.stepperMotor = stepperMotor

    def setPosition(self,position):
        def onPositionSet():
            self.blockingBusy = False
        self.stepperMotor.setPosition(position,onPositionSet)
        self.blockingBusy = True
        while(self.blockingBusy):continue        

class FakeStepperMotor(BaseStepperMotor):
    INTERVAL = .20 # how often to update during excursion
    def __init__(self):
        BaseStepperMotor.__init__(self)
        self.position = 0
        self.rate = 500

    def getPosition(self):
        return self.position

    def _setPosition(self,position,callback):
        this = self
        class Gradual(Thread):
            def run(self):
                steps = int(float(abs(position - this.position)) / this.INTERVAL / this.rate)
                positions = list(linspace(this.position,position,steps if steps > 2 else 2))                
                for newPosition in positions:
                    this.position = int(newPosition)
                    sleep(this.INTERVAL)
                this.onPositionSet(callback)
        Gradual().start()        

    # set pulse rate in Hz
    def setStepRate(self,rate):
        self.rate = rate

    def getStepRate(self):
        return self.rate

if __name__ == '__main__':
    # sm = StepperMotor('delta/ctr0','delta/port0/line0','delta/ctr2')
    sm = FakeStepperMotor()
    sm.setStepRate(200)
    def onPositionSet(): print 'position set. press enter to exit'
    sm.setPosition(100,onPositionSet)
    raw_input('waiting for pulses...\n')
    print 'position: %d' % sm.getPosition()
    # sm = StepperMotor('delta/ctr0','delta/port0/line0','delta/ctr2',0)
    # bsm = BlockingStepperMotor(sm)
    # print 'setting position'
    # bsm.setPosition(200)
    # print 'position set'
