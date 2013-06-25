class AgentScanInput:
    def __init__(self,agent):
        self.agent = agent

    def next(self):
        position = self.nextPosition()
        return None if position is None else self.agent(position)

    def nextPosition(self):
        return None

class IntervalScanInput(AgentScanInput):
    def __init__(self,agent,start,stop,step):
        AgentScanInput.__init__(self,agent)
        self.start, self.stop, self.step = start, stop, step        
        self.position = None

    def nextPosition(self):
        polarity = self.start < self.stop
        if self.position is None:
            self.position = self.start            
        else:
            self.position += self.step * (1 if polarity else -1)
        if (self.position < self.stop) is not polarity:
            self.position = None
        return self.position

class ListScanInput(AgentScanInput):
    def __init__(self,agent,positions):
        AgentScanInput.__init__(self,agent)
        self.positions = positions

    def nextPosition(self):
        return self.positions.pop(0) if self.positions else None