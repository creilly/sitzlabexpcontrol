'''
this is our config file for the voltmeters (aka: analog inputs).



config is a dictionary of dictionaries, where each entry is a stepper motor
with the necessary parameters as key/val pairs in that dictionary

'''

DYEPM, XPM, IONINTEG, KDPTHERM, DEV0 = 0,1,2,3,4

VM_SERVER_CONFIG = {
    'url':'ws://172.17.13.201:8789',
    'samplingRate':10000,
    'callbackRate':20,
    'trigChannel':'/dev1/pfi0',
    'trigEdge':'falling'
}

VM_DEBUG_SERVER_CONFIG = {
    'url':'ws://localhost:8789',
    'samplingRate':10000,
    'callbackRate':10
}

VM_DEBUG_CONFIG = {
    DEV0:{
        'physicalChannel':'beta/ai0',
        'name':'virtual vm channel 1',
        'minVal':0.0,
        'maxVal':5.0
    }
}

VM_CONFIG = {
    DYEPM:{
        'physicalChannel':'dev1/ai4',
        'name':'dye power',
        'minVal':0.0,
        'maxVal':5.0,
        'terminalConfig':'differential'
        },
    XPM:{
        'physicalChannel':'dev1/ai7',
        'name':'crystals power',
        'minVal':0.0,
        'maxVal':0.1,
        'terminalConfig':'differential'
        },
    IONINTEG:{
        'physicalChannel':'dev1/ai6',
        'name':'mpc signal',
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
