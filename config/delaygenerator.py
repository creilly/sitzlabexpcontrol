'''
this is our config file for the delay generators.


config is a dictionary of dictionaries, where each entry is a delay generator
with the necessary parameters as key/val pairs in that dictionary

'''

FAKE1 = 'fake delay gen 1'
FAKE2 = 'fake delay gen 2'
MG_PROBE_QSW = 'm gostein delay gen'
MAV_PUMP_LAMP = 'pump laser lamps'
MAV_PUMP_QSW = 'pump laser q-switch'
MAV_PROBE_LAMP = 'probe laser lamps'
MAV_PROBE_QSW = 'probe laser q-switch'
MAV_HV_PULSER = 'high voltage pulser'

SERVER_CONFIG = {
    'host_machine_ip':'ws://172.17.13.201:9002',
    'serve_on_port':'9002',
    'url':'ws://172.17.13.201:9002'
    }

DEBUG_SERVER_CONFIG = {
    'host_machine_ip':'ws://localhost:9002',
    'serve_on_port':'9002',
    'url':'ws://localhost:9002'
    }

    
DG_CONFIG = {
    MG_PROBE_QSW:{
        'usb_chan':'COM3',
        'delay':3800000.
        },
    MAV_PUMP_LAMP:{
        'usb_chan':'COM3',
        'delay':3800000.
        },
    MAV_PUMP_QSW:{
        'usb_chan':'COM3',
        'delay':3800000.
        },
    MAV_PROBE_LAMP:{
        'usb_chan':'COM3',
        'delay':3800000.
        },
    MAV_PROBE_QSW:{
        'usb_chan':'COM3',
        'delay':3800000.
        },
    MAV_HV_PULSER:{
        'usb_chan':'COM3',
        'delay':3800000.
        },

}

DEBUG_DG_CONFIG = {
    FAKE1:{
        'usb_chan':None,
        'delay':10000.
        },
    FAKE2:{
        'usb_chan':None,
        'delay':3000000.
        }
}