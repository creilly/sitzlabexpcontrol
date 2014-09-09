'''
this is our config file for the stepper motors.

stepper motors are identified by global variables (allcaps) equal to strings

pulse_channel is the channel on which steps are generated.
counter_channel is the channel that counts these steps.

config is a dictionary of dictionaries, where each entry is a stepper motor
with the necessary parameters as key/val pairs in that dictionary

'''

PDL = 'pdl'
KDP = 'kdp'
BBO = 'bbo'
LID = 'lid'
POL = 'polarizer'

import os.path
from config.filecreation import SMLOGSPATH


SM_CONFIG = {
    PDL : {
        'name':'pdl',
        'enable_channel':None,
        'pulse_channel':'/dev2/port0/line6',   #'dev1/ctr1',
        'direction_channel':'/dev2/port0/line4',   #'/dev1/port0/line2',
        'counter_channel':'dev2/ctr7',
        'backlash':0,
        'step_rate':200.0,
        'log_file':os.path.join(SMLOGSPATH,'pdl_log.txt'),
        'pts_of_int':{},
        'guiOrder':1
    },
    KDP : {
        'name':'kdp',
        'enable_channel':None,
        'pulse_channel':'dev2/ctr4',                #to inrad: green -> Ch1StepWrite
        'direction_channel':'/dev2/port0/line2',    #to inrad: blue -> Ch1DirWrite
        'counter_channel':'dev2/ctr3',              #to inrad: black -> Ch1StepRead  &&  brown -> Ch1DirRead
        'step_rate':175.0,
        'backlash':285,
        'log_file':os.path.join(SMLOGSPATH,'kdp_log.txt'),
        'pts_of_int':{},
        'guiOrder':2
    },
    BBO : {
        'name':'bbo',
        'enable_channel':None,
        'pulse_channel':'dev2/ctr1',                #to inrad: purple -> Ch2StepWrite    
        'direction_channel':'dev2/port0/line1',     #to inrad: grey -> Ch2DirWrite
        'counter_channel':'dev2/ctr2',              #to inrad: red -> Ch2StepRead  &&  orange -> Ch2DirRead
        'step_rate':800.0,
        'backlash':195,
        'log_file':os.path.join(SMLOGSPATH,'bbo_log.txt'),
        'pts_of_int':{},
        'guiOrder':3
    },
    LID : {
        'name':'lid',
        'enable_channel':'/dev1/port0/line0',
        'pulse_channel':'dev2/port0/line7',
        'direction_channel':'dev2/port0/line5',
        'counter_channel':'dev2/ctr6', #direction in: dev1/port0/line6; steps in: dev1/pfi8
        'step_rate':500.0,
        'backlash':1525,
        'log_file':os.path.join(SMLOGSPATH,'lid_log.txt'),
        'pts_of_int':{
            'scatter':-27650, #193600,
            'sputter':65950, #100000,
            'LEED':112950, #53000,
            'LIPD':160950, #5000,
            'maximum':200000,
            'minimum':-100000
            },
        'guiOrder':4
    },
    POL : {
        'name':'polarizer',
        'enable_channel':'/dev1/port0/line3',
        'pulse_channel':'/dev1/port0/line4',
        'direction_channel':'/dev1/port0/line2',
        'counter_channel':'dev1/ctr0', #direction in: dev1/port0/line6; steps in: dev1/pfi8
        'step_rate':100.0,
        'backlash':20,
        'log_file':os.path.join(SMLOGSPATH,'polarizer_log.txt'),
        'pts_of_int':{},
        'guiOrder':5
    }
}


REMPI_POI = {
    'v0 Q0':24195.6,
    'v0 Q1':24209.4,
    'v0 Q2':24236.1,
    'v0 Q3':24276.0,
    'v1 Q1':24666.4,
    'v0 S0':24149.8,
    'v0 S1':24132.4,
    'v0 S2':24129.2,
    'v0 S3':24140.4    
}

ANGLE_POI = {
    '0':0.0
}