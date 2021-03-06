'''
update on 2013/06/24 by stevens4: rectified language of IntervalScanInput \
such that first and last points are referred to as 'start' and 'stop' to \
avoid confusion with 'start' and 'stop' actions of a scan.

some input objects for use with the scan object. to use either an interval \
or list scan, specify an 'agent' which is an object that accepts a position \
input, eg. a StepperMotorProtocol.setPosition() ???? chris, can you confirm?


'''

class AgentScanInput:
    def __init__(self,agent):
        self.agent = agent

    def next(self):
        position = self.nextPosition()
        return None if position is None else self.agent(position)

    def nextPosition(self):
        return None

    def setAgent(self,agent):
        self.agent = agent

class IntervalScanInput(AgentScanInput):
    def __init__(self,agent,start,stop,step):
        AgentScanInput.__init__(self,agent)
        self.start, self.stop, self.step = start, stop, step        
        self.position = None

    def nextPosition(self):
        polarity = self.start < self.stop
        if self.position is None:
            self.position = self.start
        elif self.position == self.stop:
            self.position = None
        else:
            self.position += self.step * (1 if polarity else -1)
            if (self.position < self.stop) is not polarity:
                self.position = self.stop
        return self.position 
    
    def reset(self):
        self.position = None

class ListScanInput(AgentScanInput):
    def __init__(self,agent,positions):
        AgentScanInput.__init__(self,agent)
        self.positions = positions

    def nextPosition(self):
        return self.positions.pop(0) if self.positions else None