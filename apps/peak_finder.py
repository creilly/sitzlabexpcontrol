
class Peaker:
    FORWARDS,BACKWARDS = 0,1
    def __init__(self,setter,getter,backlash=0,direction=FORWARDS):
        self.setter,self.getter,self.backlash,self.direction = (
            setter,getter,backlash,direction
        )
    def setPosition(self,position):
        return self.setter(
            position - {
                self.FORWARDS:1.,
                self.BACKWARDS:-1.
            }[self.direction] * self.backlash
    def getPosition(self): 
    def onStart(self,start_position):
        return self.setter(
            position - {
                self.FORWARDS:1.,
                self.BACKWARDS:-1.
            }[self.direction] * self.backlash
        
    def onEnd(self,end_position): return True

class StepperMotorPeaker(Peaker):
    def __init__(self,sm_client,backlash):
        self.sm_client = sm_client
        

@inlineCallbacks
def main():
    widget = QtGui.QWidget()
    container.append(widget)

    vm_prot = yield getProtocol(VOLT_METER_SERVER)
    vm_client = VoltMeterClient(vm_prot)
    

main()
reactor.run()
