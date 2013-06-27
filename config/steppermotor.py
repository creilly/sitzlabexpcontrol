'''
this is our config file for the stepper motors.

stepper motors are identified by global variables (allcaps) equal to strings

config is a dictionary of dictionaries, where each entry is a stepper motor
with the necessary parameters as key/val pairs in that dictionary

'''

PDL = 'pdl'
KDP = 'kdp'
BBO = 'bbo'


SM_CONFIG = {
    PDL : {
        'name':'pdl',
        'pulse_channel':'dev1/ctr1',
        'direction_channel':'dev1/port0/line2',
        'counter_channel':'dev3/ctr7',
        'backlash':0
        },
    KDP : {
        'name':'kdp',
        'pulse_channel':'dev3/ctr4',
        'direction_channel':'dev3/port0/line2',
        'counter_channel':'dev3/ctr3',
        'backlash':285
        },
    BBO : {
        'name':'pdl',
        'pulse_channel':'dev3/ctr1',
        'direction_channel':'dev3/port0/line1',
        'counter_channel':'dev3/ctr2',
        'backlash':195
        }
    }