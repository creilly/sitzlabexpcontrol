from sitz import SitzException
from functools import partial

from daqmx import CO,DO,CI
from daqmx.task.co import COTask
from daqmx.task.do import DOTask
from daqmx.task.ci import CITask

from filecreationmethods import LogFile

from threading import Lock, Thread
from numpy import linspace
from time import sleep

from config.filecreation import SMLOGSPATH

class BaseStepperMotor:

    TASK_CLASSES = {
        CO:COTask,
        DO:DOTask,
        CI:CITask
    }

    # MAKE SURE TO CALL THIS IF YOU OVERRIDE    
    def __init__(self,tasks=None):
        self.busy = False
        self.queue = []
        self._tasks = tasks if tasks else []
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
    
    def destroy(self): 
        for task in self._tasks:
            task.clearTask()

            
class EnabledStepperMotor(BaseStepperMotor):
    ENABLED = 1
    DISABLED = 0
    def __init__(
        self,
        enable_channel=None,
        tasks=None
    ):
        self.enable_channel = enable_channel
        self.enabled = self.DISABLED 
        if enable_channel is not None:
            self.enable_task = DOTask()
            self.enable_task.createChannel(enable_channel)
        elif enable_channel is None:
            self.enable()
        tasks = (tasks if tasks is not None else []) + ([self.enable_task] if self.enable_channel is not None else [])
        BaseStepperMotor.__init__(
            self,
            tasks=tasks
        )
    
    
    def getEnableStatus(self):
        enb_str = {self.ENABLED:'enabled',self.DISABLED:'disabled'}[self._getEnableStatus()]
        return enb_str

    def enable(self):
        self._setEnableStatus(self.ENABLED)
    
    def disable(self):
        self._setEnableStatus(self.DISABLED)
        
    def toggleStatus(self):
        if self._getEnableStatus() == self.ENABLED: self.disable()
        elif self._getEnableStatus() == self.DISABLED: self.enable()
        
    def _getEnableStatus(self):
        return self.enabled
    
    def _setEnableStatus(self,state):
        if self.enable_channel is None:
            self.enabled = True
            return
        elif self.enable_channel is not None:
            self.enable_task.writeState(
                {
                    self.ENABLED:True,
                    self.DISABLED:False
                }[state]
            )
            self.enabled = state
    
    def _setPosition(self,position,callback):
        if self._getEnableStatus() == self.ENABLED:
            BaseStepperMotor._setPosition(self,position,callback)
        else:
            print 'not enabled!'
    
    def destroy(self):
        self.disable()
        BaseStepperMotor.destroy(self)
            
class DirectionStepperMotor(EnabledStepperMotor):
    FORWARDS = 0
    BACKWARDS = 1
    def __init__(
        self,
        enable_channel=None,
        backlash=0,
        direction=FORWARDS,
        tasks=None
    ):
        EnabledStepperMotor.__init__(
            self,
            enable_channel=enable_channel,
            tasks=tasks
        )
        self.backlash = backlash
        self._setDirection(direction)

    def getPosition(self):
        return self._getPosition() + (1 if self._getDirection() is self.BACKWARDS else 0) * self.backlash
    
    def getDirection(self): 
        dir_str = {DigitalLineStepperMotor.FORWARDS:'FORWARDS',DigitalLineStepperMotor.BACKWARDS:'BACKWARDS'}[self._getDirection()]
        return dir_str

    def _setPosition(self,position,callback):
        if self._getEnableStatus() != self.ENABLED: 
            print 'not enabled!'
            return
        delta = position - self.getPosition()
        if delta is 0:
            self.onPositionSet(callback)
            return
        direction = self.FORWARDS if delta > 0 else self.BACKWARDS
        steps = abs(delta) + (self.backlash if direction is not self._getDirection() else 0)
        if direction is not self._getDirection():
            self._setDirection(direction)
        self._generateSteps(steps,callback)

    def _getPosition(self): return 0
    def _setDirection(self,direction): self._direction = direction
    def _getDirection(self): return self._direction
    def _generateSteps(self,steps,callback): callback()

    
class DigitalLineDirectionStepperMotor(DirectionStepperMotor):
    def __init__(
        self,
        direction_channel,
        enable_channel=None,
        backlash=0,
        direction=DirectionStepperMotor.FORWARDS,
        tasks=None
    ):
        self.direction_task = DOTask()
        self.direction_task.createChannel(direction_channel)
        DirectionStepperMotor.__init__(
            self,
            enable_channel=enable_channel,
            backlash=backlash,
            direction=direction,
            tasks = ((tasks if tasks is not None else []) + [self.direction_task])
        )     

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
        enable_channel=None,
        initial_position=0,
        backlash=0,
        direction=DirectionStepperMotor.FORWARDS,
        tasks=None
    ):
        self.counter_task = CITask()
        #subtract out the backlash from the logged position to maintain consistency with DirectionStepperMotor.getPosition()
        if direction == DirectionStepperMotor.BACKWARDS: 
            initialCount = initial_position - backlash
        else:
            initialCount = initial_position
        self.counter_task.createChannel(counter_channel,initialCount=initialCount)
        self.counter_task.start()
        tasks = (tasks if tasks is not None else []) + [self.counter_task]
        DigitalLineDirectionStepperMotor.__init__(
            self,
            direction_channel,
            enable_channel=enable_channel,
            backlash=backlash,
            direction=direction,
            tasks=tasks
        )
        

    def _getPosition(self):
        counts = self.counter_task.readCounts()
        return counts

        
class LoggedStepperMotor(CounterStepperMotor):
    def __init__(
        self,
        counter_channel,
        direction_channel,
        log_file=None,
        enable_channel=None,
        backlash=0,
        tasks=None
    ):
        import os.path
        if log_file is None:
            logName = str(counter_channel).replace('/','-')+'.txt'
        else:
            logName = log_file
        self.logName = os.path.join(SMLOGSPATH,logName)
        self._openLog()
        try:
            last_date, last_position, last_direction = self._getLastPosition()
            print last_date, last_position, last_direction
        except TypeError or ValueError:
            print 'error with log file! reverting to 0 & forwards'
            last_date, last_position, last_direction = ('never',0,'FORWARDS')
        last_direction = {'FORWARDS':DigitalLineStepperMotor.FORWARDS,'BACKWARDS':DigitalLineStepperMotor.BACKWARDS}[last_direction]
        
        CounterStepperMotor.__init__(
            self,
            counter_channel,
            direction_channel,
            enable_channel=enable_channel,
            initial_position=int(last_position),
            backlash=backlash,
            direction=last_direction,
            tasks=tasks
        )
    
    def _openLog(self):
        self.log_file = LogFile(self.logName)
    
    def _closeLog(self):
        self.log_file.close()
    
    def enable(self):
        self._openLog()
        EnabledStepperMotor.enable(self)
        
    def disable(self):
        self.updateLog()
        self._closeLog()
        EnabledStepperMotor.disable(self)
    
    def _getLastPosition(self):
        return self.log_file.readLastLine()
   
    def updateLog(self):    # remember that you have to close the logfile before you can see these changes!!
        currPos = self.getPosition()
        currDir = self.getDirection()
        self.log_file.update((currPos,currDir))
        
    def destroy(self):
        self._closeLog()
        EnabledStepperMotor.destroy(self)

class PulseGeneratorStepperMotor(LoggedStepperMotor):
    def __init__(
            self,
            step_channel,
            counter_channel,
            direction_channel,
            log_file=None,
            enable_channel=None,
            step_rate=500.0,
            backlash=0,
            tasks=None
    ):
        self.step_task = COTask()
        self.step_task.createChannel(step_channel)
        self.setStepRate(step_rate)
        LoggedStepperMotor.__init__(
            self,
            counter_channel,
            direction_channel,
            log_file,
            enable_channel=enable_channel,
            backlash=0,
            tasks=((tasks if tasks is not None else []) + [self.step_task])
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


class DigitalLineStepperMotor(LoggedStepperMotor):
    import threading
    def __init__(
            self,
            step_channel,
            counter_channel,
            direction_channel,
            log_file=None,
            enable_channel=None,
            step_rate=500.0,
            backlash=0,
            tasks=None
    ):
        self.step_task = DOTask()
        self.step_task.createChannel(step_channel)
        self.setStepRate(step_rate)
        self.step_task.writeState(False)
        tasks=(tasks if tasks is not None else []) + [self.step_task]
        LoggedStepperMotor.__init__(
            self,
            counter_channel,
            direction_channel,
            log_file,
            enable_channel,
            backlash,
            tasks
        )

    def run(self,steps,callback):
        for i in range(steps):
            for state in (True,False):
                self.step_task.writeState(state)
                sleep(.5 / self.step_rate)
        callback()
        
    def _generateSteps(self,steps,callback):
        thread = Thread(target=self.run, args=(steps,callback))
        thread.start()
 
    # def _generateSteps(self,steps,callback):
        # this = self
        # class GenerateSteps(Thread):
            # def run(self):
                # for i in range(steps):
                    # for state in (True,False):
                        # this.step_task.writeState(state)
                        # sleep(.5 / this.step_rate)
                # callback()
        # GenerateSteps().start()
        

    def setStepRate(self,step_rate): self.step_rate = step_rate

    def getStepRate(self): return self.step_rate
    
class StepperMotor(PulseGeneratorStepperMotor): pass


    
class FakeStepperMotor(DirectionStepperMotor):
    INTERVAL = .20 # how often to update during excursion
    def __init__(self,position=0,rate=500):
        DirectionStepperMotor.__init__(self)
        self.position = position
        self.rate = float(rate)

    def getPosition(self):
        return self.position

    def _generateSteps(self,steps,callback):
        this = self
        class Gradual(Thread):
            def run(self):
                intervalSize = int(this.rate*this.INTERVAL)
                direction = (1 if this.getDirection() is this.FORWARDS else -1)
                for i in range(steps/intervalSize):
                    this.position += direction*intervalSize
                    sleep(this.INTERVAL)
                this.position += (steps % intervalSize)*direction
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
        


