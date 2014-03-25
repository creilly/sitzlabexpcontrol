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
        'guiOrder':1
    },
    KDP : {
        'name':'kdp',
        'enable_channel':None,
        'pulse_channel':'dev2/ctr4',
        'direction_channel':'/dev2/port0/line2',
        'counter_channel':'dev2/ctr3',
        'step_rate':175.0,
        'backlash':285,
        'log_file':os.path.join(SMLOGSPATH,'kdp_log.txt'),
        'guiOrder':2
    },
    BBO : {
        'name':'bbo',
        'enable_channel':None,
        'pulse_channel':'dev2/ctr1',
        'direction_channel':'dev2/port0/line1',
        'counter_channel':'dev2/ctr2',
        'step_rate':800.0,
        'backlash':195,
        'log_file':os.path.join(SMLOGSPATH,'bbo_log.txt'),
        'guiOrder':3
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
        'guiOrder':4
    }
}
