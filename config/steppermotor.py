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
        'direction_channel':'/dev1/port0/line2',
        'counter_channel':'dev2/ctr7',
        'backlash':0
        'step_rate':200.0,
        'initial_position':0,
    },
    KDP : {
        'name':'kdp',
        'pulse_channel':'dev2/ctr4',
        'direction_channel':'/dev2/port0/line2',
        'counter_channel':'dev2/ctr3',
        'step_rate':175.0,
        'initial_position':0,
        'backlash':285
    },
    BBO : {
        'name':'bbo',
        'pulse_channel':'dev2/ctr1',
        'direction_channel':'dev2/port0/line1',
        'counter_channel':'dev2/ctr2',
        'step_rate':800.0,
        'initial_position':0,
        'backlash':195
    }
}
