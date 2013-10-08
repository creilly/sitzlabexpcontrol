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
    def __init__(self,position=0):
        self.busy = False
        self.queue = []
        self.lock = Lock()

    def setPosition(self,position,callback=lambda:None):
        if self.busy:
            with self.lock:
                self.queue.append((position,callback))
            return
        self.busy = True
        self._setPosition(
            position,
            partial(
                self.onPositionSet,
                callback,
            )
        )

    def onPositionSet(self,callback):        
        callback()
        with self.lock:
            if self.queue:
                position, callback = self.queue.pop(0)
                self._setPosition(
                    position,
                    partial(
                        self.onPositionSet,
                        callback
                    )
                )
                return
        self.busy = False

    # OVERRIDE THESE METHODS

    def _setPosition(self,position,callback):
        callback()

    def getPosition(self):
        return 0

    def setStepRate(self,rate):
        pass

    def getStepRate(self): return -1

class DirectionStepperMotor(BaseStepperMotor):
    FORWARDS = 0
    BACKWARDS = 1
    def __init__(self,backlash=0,direction=FORWARDS):
        self.backlash = backlash
        self._setDirection(direction)
        BaseStepperMotor.__init__(self)

    def getPosition(self):
        return self._getPosition() + (1 if self.direction is self.BACKWARDS else 0) * self.backlash

    def _setPosition(self,position,callback):
        delta = position - self.getPosition()
        if delta is 0:
            self.onPositionSet(callback)
            return
        direction = self.FORWARDS if delta > 0 else self.BACKWARDS
        if direction is not self._getDirection():
            self._setDirection(direction)
        steps = abs(delta) + (self.backlash if direction is not self.direction else 0)
        self._generateSteps(steps,callback)

    def getDirection(self): return self._getDirection()

    def _getPosition(self): return 0
    def _setDirection(self,direction): pass
    def _getDirection(self,direction): return self.FORWARDS
    def _generateSteps(self,steps,callback): callback()

class DigitalLineDirectionStepperMotor(DirectionStepperMotor):
    def __init__(
            self,
            direction_channel,
            backlash=0,
            direction=DirectionStepperMotor.FORWARDS
    ):
        self.direction_task = DOTask()
        self.direction_task.createChannel(direction_channel)
        self._setDirection(direction)
        DirectionStepperMotor.__init__(self,backlash,direction)

    def _setDirection(self,direction):
        self.direction_task.writeState(
            {
                self.FORWARDS:True,
                self.BACKWARDS:False
            }[direction]
        )
        self.direction = direction

    def _getDirection(self): return self.direction

class CounterStepperMotor(DigitalLineDirectionStepperMotor):
    def __init__(
            self,
            counter_channel,
            direction_channel,
            initial_position=0,
            backlash=0,
            direction=DirectionStepperMotor.FORWARDS    
    ):
        self.counter_task = CITask()
        self.counter_task.createChannel(counter_channel)
        self.counter_task.start()
        DigitalLineDirectionStepperMotor.__init__(
            self,
            direction_channel,
            backlash,
            direction
        )

    def _getPosition(self):
        return self.counter_task.readCounts()

class PulseGeneratorStepperMotor(CounterStepperMotor):
    def __init__(
            self,
            step_channel,
            counter_channel,
            direction_channel,
            step_rate=500.0,
            initial_position=0,
            backlash=0,
            direction=DirectionStepperMotor.FORWARDS    
    ):
        self.step_task = COTask()
        self.step_task.createChannel(step_channel)
        self.setStepRate(step_rate)
        CounterStepperMotor.__init__(
            self,
            counter_channel,
            direction_channel,
            initial_position,
            backlash,
            direction
        )

    def _generateSteps(self,steps,callback):
        self.step_task.generatePulses(steps,callback)

    # set pulse rate in Hz
    def setStepRate(self,rate):
        self.step_task.configureTiming(0.5 / rate,0.5 / rate)

    def getStepRate(self):
        highTime, lowTime = self.step_task.getTimingConfiguration()
        period = highTime + lowTime
        rate = 1.0 / period
        return rate

class DigitalLineStepperMotor(CounterStepperMotor):
    def __init__(
            self,
            step_channel,
            counter_channel,
            direction_channel,
            step_rate=500.0,
            initial_position=0,
            backlash=0,
            direction=DirectionStepperMotor.FORWARDS
    ):
        self.step_task = DOTask()
        self.step_task.createChannel(step_channel)
        self.step_task.writeState(False)
        self.setStepRate(step_rate)
        CounterStepperMotor.__init__(
            self,
            counter_channel,
            direction_channel,
            initial_position,
            backlash,
            direction
        )

    def _generateSteps(self,steps,callback):
        this = self                    
        class GenerateSteps(Thread):
            def run(self):
                for i in range(steps):
                    for state in (True,False):
                        this.step_task.writeState(state)
                        sleep(.5 / this.step_rate)
                callback()
        GenerateSteps().start()

    def setStepRate(self,step_rate): self.step_rate = step_rate

    def getStepRate(self): return self.step_rate

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
                steps = int(
                    float(
                        abs(
                            position - this.position
                        )
                    ) / this.INTERVAL / this.rate
                )
                positions = list(
                    linspace(
                        this.position,position,steps if steps > 2 else 2
                    )
                )
                for newPosition in positions:
                    this.position = int(newPosition)
                    sleep(this.INTERVAL)
                callback()
        Gradual().start()     

    # set pulse rate in Hz
    def setStepRate(self,rate):
        self.rate = rate

    def getStepRate(self):
        return self.rate

class BlockingStepperMotor:
    def __init__(self,stepperMotor):        
        self.stepperMotor = stepperMotor

    def setPosition(self,position):
        def onPositionSet():
            self.blockingBusy = False
        self.stepperMotor.setPosition(position,onPositionSet)
        self.blockingBusy = True
        while(self.blockingBusy):continue

if __name__ == '__main__':
    import sys
    import daqmx
    def select_from_list(list,prompt):
        while True:
            print prompt
            print '\n'.join(
                '\t%d\t%s' % (index,item)
                for index, item in
                enumerate(list)
            )            
            try:
                index = int(raw_input('-->: '))
            except ValueError:
                print 'input must be number'
                continue
            if index not in range(len(list)):
                print 'input must be between 0 and %d' % len(list)
                continue
            else:
                break
        return list[index]
    
    print '<---- STEPPER MOTOR CONFIGURATION --->'
    pulse_generator = 'pulse generator'
    digital_line = 'digital line'
    step_tasks = {
        pulse_generator:daqmx.CO,
        digital_line:daqmx.DO
    }
    step_task = step_tasks[
        select_from_list(
            step_tasks.keys(),
            'select step mode'
        )
    ]
    if 'config' in sys.argv:    
        channels = (
            select_from_list(
                daqmx.getPhysicalChannels(
                    select_from_list(
                        daqmx.getDevices(),
                        'select %s device' % role_name
                    )
                )[role_task],
                'select %s channel' % role_name
            )
            for role_task, role_name in
            (
                (step_task,'step'),
                (daqmx.CI,'read'),
                (daqmx.DO,'direction')
            )
        )
    else:
        exit()
    sm = {
        daqmx.DO:DigitalLineStepperMotor,
        daqmx.CO:PulseGeneratorStepperMotor
    }[step_task](*channels)
    print '<--- END CONFIGURATION --->'
    def log(x): print x
    while True:
        goto = int(raw_input('goto (q to quit): \n'))
        sm.setPosition(goto,lambda:log(sm.getPosition()))
        


