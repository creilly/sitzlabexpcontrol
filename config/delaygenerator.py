'''
this is our config file for the delay generators.


config is a dictionary of dictionaries, where each entry is a delay generator
with the necessary parameters as key/val pairs in that dictionary

the ard_id numbers are unique to the specific arduino used inside that delay generator
this is part of the USB specification. delaygeneratorserver will build a dictionary
mapping COM port number to these ID numbers each time it is run. the COM numberings
are permanent for an installation of an OS but random the first time the delay
generators are plugged in. you should never need to change these ID numbers unless you
re-purpose a delay generator then update all the other parameters and name.

'''

FAKE1 = 'fake delay gen 1'
FAKE2 = 'fake delay gen 2'
MG_PROBE_QSW = 'm gostein delay gen'
MAV_PUMP_LAMP = 'pump laser lamps'
MAV_PUMP_QSW = 'pump laser q-switch'
MAV_PROBE_LAMP = 'probe laser lamps'
MAV_PROBE_QSW = 'probe laser q-switch'
MAV_NOZZLE = 'nozzle'

SERVER_CONFIG = {
    #'host_machine_ip':'ws://172.17.13.201:9002',
    'host_machine_ip':'ws://localhost:9002',
    'serve_on_port':'9002',
    'url':'ws://localhost:9002',
    # 'url':'ws://172.17.13.201:9002'
    }

DEBUG_SERVER_CONFIG = {
    'host_machine_ip':'ws://localhost:9002',
    'serve_on_port':'9002',
    'url':'ws://localhost:9002'
    }

    
DG_CONFIG = {
    MG_PROBE_QSW:{
        'usb_chan':'COM3',
        'ard_id': None,
        'delay':3800000.,
        'partner':None,
        'rel_part_delay': None,
        'run_by_default':False,
        'dg_version': 'gostein'
        },
    MAV_NOZZLE:{
        'usb_chan':'COM6',
        'ard_id':'55330343731351906041',
        'delay':2842450.,
        'partner':None,
        'rel_part_delay':None,
        'run_by_default':True,
        'dg_version': 'maverick'
        },
    MAV_PUMP_LAMP:{
        'usb_chan':'COM3',
        'ard_id':'5533834353935150E1D1',
        'delay':3607400.,
        'partner':MAV_PUMP_QSW,
        'rel_part_delay':227550.,
        'run_by_default':True,
        'dg_version': 'maverick'
        },
    MAV_PUMP_QSW:{
        'usb_chan':'COM7',
        'ard_id': '5533834353935120E1D0',
        'delay':3834950.,
        'partner':MAV_PUMP_LAMP,
        'rel_part_delay':-227550.,
        'run_by_default':True,
        'dg_version': 'maverick'
        },
    MAV_PROBE_LAMP:{
        'usb_chan':'COM5',
        'ard_id': '55330343731351C0A1B1',
        'delay':3604150.,
        'partner':MAV_PROBE_QSW,
        'rel_part_delay':232400.,
        'run_by_default':True,
        'dg_version': 'maverick'
        },
    MAV_PROBE_QSW:{
        'usb_chan':'COM4',
        'ard_id': '55338343539351109290',
        'delay':3836550.,
        'partner':MAV_PROBE_LAMP,
        'rel_part_delay':-232400.,
        'run_by_default':False,
        'dg_version': 'maverick'
        }

}

DEBUG_DG_CONFIG = {
    FAKE1:{
        'ard_id':None,
        'delay':10000.,
        'partner':FAKE2,
        'rel_part_delay':220000.,
        'run_by_default':True,
        'dg_version': 'maverick'
        },
    FAKE2:{
        'ard_id':None,
        'delay':230000.,
        'partner':FAKE1,
        'rel_part_delay':-220000.,
        'run_by_default':True,
        'dg_version': 'maverick'
        }
}