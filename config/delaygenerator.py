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

'''
numberings of ddgs on pooh computer, for ease of reference

        ard_id                  offset  minV    maxV
COM3:   55338343539351109290    1745    3.5     4.7
COM4:   5533834353935150E1D1    1630    2.0     3.20
COM5:   5533834353935120E1D0     968    3.3     3.88
COM6:   55330343731351C0A1B1     990    3.5     4.14
COM7:   55330343731351906041     631    2.6     3.82
'''

DG_CONFIG = {
    MAV_NOZZLE:{
        'ard_id': '55338343539351109290', #COM3
        'delay':2000000,  #2842450,
        'partner':None,
        'rel_part_delay':None,
        'run_by_default':True,
        'offset':1745,
        'minVoltage':'3.50',
        'maxVoltage':'4.70',
        'guiOrder':1
        },
    MAV_PUMP_LAMP:{
        'ard_id':'5533834353935150E1D1',  #COM4
        'delay': 2962450,      #3607400,
        'partner':MAV_PUMP_QSW,
        'rel_part_delay':227550.,
        'run_by_default':True,
        'offset':1630,
        'minVoltage':'2.00',
        'maxVoltage':'3.20',
        'guiOrder':2
        },
    MAV_PUMP_QSW:{
        'ard_id': '5533834353935120E1D0',  #COM5
        'delay':3190000, #3834950,
        'partner':MAV_PUMP_LAMP,
        'rel_part_delay':-227550.,
        'run_by_default':True,
        'offset':1000,
        'minVoltage':'3.50',
        'maxVoltage':'4.14',
        'guiOrder':3
        },
    MAV_PROBE_LAMP:{
        'ard_id': '55330343731351C0A1B1',  #COM6
        'delay':2957600, #3604150,
        'partner':MAV_PROBE_QSW,
        'rel_part_delay':232400.,
        'run_by_default':True,
        'offset':968,
        'minVoltage':'3.30',
        'maxVoltage':'3.88',
        'guiOrder':4
        },
    MAV_PROBE_QSW:{
        'ard_id':'55330343731351906041',  #COM7
        'delay':3190000, #3836550,
        'partner':MAV_PROBE_LAMP,
        'rel_part_delay':-232400.,
        'run_by_default':True,
        'offset':635,
        'minVoltage':'2.60',
        'maxVoltage':'3.8078',
        'guiOrder':5
        }
}

DEBUG_DG_CONFIG = {
    FAKE1:{
        'ard_id':None,
        'delay':10000,
        'partner':FAKE2,
        'rel_part_delay':220000.,
        'run_by_default':True,
        'guiOrder':1
        },
    FAKE2:{
        'ard_id':None,
        'delay':230000,
        'partner':FAKE1,
        'rel_part_delay':-220000.,
        'run_by_default':True,
        'guiOrder':2
        }
}




'''
to find the ard_id parameter for a new delay generator:

see: http://msdn.microsoft.com/en-us/library/aa394413(v=vs.85).aspx

start an ipython session on the host computer with the arduino attached (after you have installed the arduino driver).
execute this:

import win32com.client
wmi = win32com.client.GetObject ("winmgmts:")
for usb in wmi.InstancesOf("Win32_SerialPort"):
    print usb.DeviceID + ":\t" + usb.PNPDeviceID.split("\\")[2]
	
look through those listed IDs and find the new one. copy paste it as the ard_id value
'''