import numpy as np

from twisted.internet import reactor
from twisted.internet.defer import Deferred, inlineCallbacks

from ab.abclient import getProtocol
from ab.abbase import selectFromList

from config.serverURLs import STEPPER_MOTOR_SERVER, VOLTMETER_SERVER, DELAY_GENERATOR_SERVER
from config.steppermotor import POL
from config.filecreation import POOHDATAPATH
from config.delaygenerator import MAV_PUMP_QSW, MAV_PROBE_QSW


from voltmeter.voltmeterclient import VoltMeterClient
from steppermotor.steppermotorclient import StepperMotorClient
from delaygenerator.delaygeneratorclient import DelayGeneratorClient

from filecreationmethods import filenameGen, checkPath, LogFile

from os import path

import signal


def pause(signal, frame):
    raw_input("Paused!\nPress enter to resume")
    return

signal.signal(signal.SIGINT,pause)


OFFSET = 15600 #steps = 0deg value
SLOPE = 100. #steps/degree

def degrees_to_steps(degrees):
    return SLOPE * degrees + OFFSET

def steps_to_degrees(steps):
    return (steps - OFFSET) / SLOPE


BELL = chr(7)

REPEAT = 2

ANGLE_START = 0
ANGLE_STOP = 90
ANGLE_STEP = 30

TIME_START = -50
TIME_STOP = +550
TIME_STEP = 15

WAIT_FOR_TUNE = True

SHOTS = 50

numAngPoints = (ANGLE_STOP-ANGLE_START+1)/ANGLE_STEP
numTimePoints = (TIME_STOP-TIME_START+1)/TIME_STEP
acqPerPoint = SHOTS/10.
timeAngMove = ANGLE_STEP*SLOPE/500.
totalTime = ((numTimePoints*acqPerPoint) + timeAngMove)*numAngPoints
print 'ETA is: '+str(REPEAT*totalTime/60.)+' minutes.'


@inlineCallbacks
def onReady():
    vm_prot = yield getProtocol(VOLTMETER_SERVER)
    sm_prot = yield getProtocol(STEPPER_MOTOR_SERVER)
    dg_prot = yield getProtocol(DELAY_GENERATOR_SERVER)

    vm = VoltMeterClient(vm_prot)
    sm = StepperMotorClient(sm_prot,POL)
    dg = DelayGeneratorClient(dg_prot)

    delays = yield dg.getDelays()
    pumpTime = delays[MAV_PUMP_QSW]
    
    times = np.arange(TIME_START+pumpTime,TIME_STOP+pumpTime+TIME_STEP,TIME_STEP)

    angles = np.arange(ANGLE_START,ANGLE_STOP+ANGLE_STEP,ANGLE_STEP)
    
    channels = yield vm.getChannels()
    channel = yield selectFromList(channels,'pick the mcp channel')
    
    trans = yield selectFromList(['Q3','S3','Q1'],'pick the transition you are at')
    bsang = yield selectFromList(['020','110'],'pick the angle of the beam splitter')
    
    for i in range(REPEAT):
        for angle in np.concatenate((angles,angles[::-1])):
            yield sm.setPosition(int(degrees_to_steps(angle)))
            angleStr = str(angle).zfill(3)
            relPath, fileName = filenameGen(path.join(trans,'TimeOfFlight','BS'+str(bsang),'HWP'+angleStr))
            absPath = path.join(POOHDATAPATH,relPath)
            checkPath(absPath)
            logName = path.join(absPath,fileName+'.tsv')
            thisLog = LogFile(logName)
            for time in times[::-1]:
                yield dg.setPartnerDelay(MAV_PROBE_QSW, int(time))
                voltage, std = yield vm.getNVoltages(channel,SHOTS)
                stdom = std/np.sqrt(SHOTS)
                print (angle,time-pumpTime,voltage,stdom)
                thisLog.update([time,voltage,stdom])
            thisLog.close()
            print BELL
            if WAIT_FOR_TUNE:
                pause(None,None)    
    reactor.stop()
onReady()
reactor.run()

