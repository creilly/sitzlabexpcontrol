from steppermotorserver import StepperMotorWAMP, getConfig, getStepperMotor
from twisted.internet.defer import inlineCallbacks
from abserver import command, runServer
from abbase import getType, selectFromList

class PDLWAMP(StepperMotorWAMP):
    SLOPE = 0.02400960384
    @inlineCallbacks
    def initializeWAMP(self,stepperMotor):
        surfOffset = yield getType(float,'enter SURF wavelength: ')        
        crystalOffset = stepperMotor.getPosition()
        self.offsets = crystalOffset, surfOffset
        StepperMotorWAMP.initializeWAMP(self,stepperMotor)
    @command('get-wavelength','return wavelength of dye laser (in quarter angstroms)')
    def getWavelength(self):
        return self.SLOPE * (self.getPosition()-self.offsets[0]) + self.offsets[1]
    @command('set-wavelength','set wavelength of dye laser (in quarter angstroms)')
    def setWavelength(self,wavelength):
        return self.setPosition(
            int(
                (wavelength - self.offsets[1]) / self.SLOPE - self.offsets[0]
            )
        )
        
@inlineCallbacks
def main():
    smKey = yield selectFromList(
        ('PDL','TestStepperMotor2'),
        'select wavelength stepper motor'
    )
    options = getConfig()[smKey]
    runServer(
        WAMP = PDLWAMP,
        URL = options['url'],
        args = [
            getStepperMotor(
                options
            )
        ],
        debug=True,
        outputToConsole=True
    )
    
if __name__=='__main__':
    from twisted.internet import reactor
    main()
    reactor.run()
