'''
this is our config file for the voltmeters (aka: analog inputs).



config is a dictionary of dictionaries, where each entry is a stepper motor
with the necessary parameters as key/val pairs in that dictionary

'''

DYEPM = 'dye power meter'
XPM = 'xtals power meter'
IONINTEG = 'ion integrator'
KDPTHERM = 'kdp thermocouple'
DEV0 = 'virtual analog input'


VM_SERVER_CONFIG = {
    'url':'ws://172.17.13.201:8789',
    'samplingRate':10000,
    'callbackRate':20,
    'trigChannel':'/dev1/pfi0',
    'trigEdge':'falling'
}

VM_DEBUG_SERVER_CONFIG = {
    'url':'ws://localhost:8789',
}

VM_DEBUG_CONFIG = {
    DEV0:{
        'physicalChannel':'alpha/ai0',
        'name':'virtual vm channel 1',
        'minVal':0.0,
        'maxVal':5.0
        }
    }


VM_CONFIG = {
    DYEPM:{
        'physicalChannel':'dev1/ai4',
        'name':'gated integrator (dye)',
        'minVal':0.0,
        'maxVal':5.0,
        'terminalConfig':'differential'
        },
    XPM:{
        'physicalChannel':'dev1/ai7',
        'name':'xtals power meter',
        'minVal':0.0,
        'maxVal':0.1,
        'terminalConfig':'differential'
        },
    IONINTEG:{
        'physicalChannel':'dev1/ai6',
        'name':'gated integrator (ions)',
        'minVal':0.0,
        'maxVal':10.0,
        'terminalConfig':'default'
        },
    KDPTHERM:{
        'physicalChannel':'dev1/ai5',
        'name':'thermocouple',
        'minVal':0.0,
        'maxVal':0.1,
        'terminalConfig':'default'
        }
}
