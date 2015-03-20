import numpy as np

from twisted.internet import reactor
from twisted.internet.defer import Deferred, inlineCallbacks

from matplotlib import pyplot as plt
from ab.abclient import getProtocol
from ab.abbase import selectFromList

from config.serverURLs import STEPPER_MOTOR_SERVER, VOLTMETER_SERVER
from config.steppermotor import POL
from config.filecreation import POOHDATAPATH

from voltmeter.voltmeterclient import VoltMeterClient
from steppermotor.steppermotorclient import StepperMotorClient

from filecreationmethods import filenameGen, checkPath, LogFile

from os import path

ANGLE_START = 0
ANGLE_STOP = 180
ANGLE_STEP = 5

OFFSET = 13200 #steps
SLOPE = 100. #steps/degree

SHOTS = 50

SWEEPS = 1 #number of forward AND backward scans


FORWARDS = 'forwards'
BACKWARDS = 'backwards'

def degrees_to_steps(degrees):
    return SLOPE * degrees + OFFSET

def steps_to_degrees(steps):
    return (steps - OFFSET) / SLOPE

forwards = np.arange(ANGLE_START,ANGLE_STOP,ANGLE_STEP)
backwards = forwards[::-1]

@inlineCallbacks
def onReady():
    vm_prot = yield getProtocol(VOLTMETER_SERVER)
    sm_prot = yield getProtocol(STEPPER_MOTOR_SERVER)

    vm = VoltMeterClient(vm_prot)
    sm = StepperMotorClient(sm_prot,POL)

    channels = yield vm.getChannels()
    channel = yield selectFromList(channels,'pick the mcp channel')
    
    trans = yield selectFromList(['Q3','S3','Q1'],'pick the transition you are at')
    
    bsang = yield selectFromList(['020','110'],'pick the angle of the beam splitter')
    
    # #suffix = yield selectFromList(['pump','unpump'],'are you pumping?')
    suffix = 'mBeamOff_diffZeroed'
    
    numPoints = (ANGLE_STOP-ANGLE_START+1)/ANGLE_STEP
    totalAcqTime = SWEEPS*2*(SHOTS/10.)*numPoints
    totalStepTime = ((ANGLE_STEP*SLOPE)/500.)*numPoints
    print 'ETA is: '+str((totalAcqTime + totalStepTime)/60.)+' minutes.'

    for sweep in range(SWEEPS):
        for direction in (FORWARDS,BACKWARDS):
            relPath, fileName = filenameGen(trans)
            absPath = path.join(POOHDATAPATH,relPath)
            checkPath(absPath)
            logName = path.join(absPath,fileName+'_pol_sweep_'+bsang+'_'+suffix+'.tsv')
            thisLog = LogFile(logName)
            for angle in {
                    FORWARDS:forwards,
                    BACKWARDS:backwards
                    }[direction]:
                yield sm.setPosition(int(degrees_to_steps(angle)))
                voltage, std = yield vm.getNVoltages(channel,SHOTS)
                stdom = std/np.sqrt(SHOTS)
                print (sweep,angle,voltage, stdom)
                thisLog.update([angle,voltage,stdom])
            thisLog.close()
            
    reactor.stop()    
onReady()
reactor.run()

