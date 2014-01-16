'''
this is our config file for scantypes/configuration combobox in some guis

it is a dictionary of dictionaries, the first level key is the name of the
configuration as it appears to the users. the dictionary below that is a
series of key/value pairs of settings you want to be enabled when this
configuration is activated.

'''


SCAN_TYPES = {
    'none':{
        'smCombo':None,
        'voltmeter':None,
        'measurementType':None
    },
    'popBottle':{
        'smCombo':'pdl',
        'voltmeter':'gated integrator (ions)',
        'measurementType':'popBottle'
    },
    'popPiglet':{
        'stepper motor':'pdl',
        'voltmeter':'gated integrator (ions)',
        'measurementType':'popPiglet'
    },
    'popBeam':{
        'stepper motor':'pdl',
        'voltmeter':'gated integrator (ions)',
        'measurementType':'popBeam'
    },
    'pdlPower':{
        'stepper motor':'pdl',
        'voltmeter':'gated integrator (dye)',
        'measurementType':'pdlPower'
    },
    'thirdHarmonicPower':{
        'stepper motor':'pdl',
        'voltmeter':'xtals power meter',
        'measurementType':'thirdHarmonicPower'
    },
    'bboScan':{
        'stepper motor':'bbo',
        'voltmeter':'xtals power meter',
        'measurementType':'bboScan'
    },
    'kdpScan':{
        'stepper motor':'kdp',
        'voltmeter':'xtals power meter',
        'measurementType':'kdpScan'
    },
    'lineshape-Q0':{},
    'lineshape-Q1':{},
    'lineshape-Q2':{},
    'lineshape-Q3':{},
    'ProbeQSwDelay',
    'BeamProfile'
}  