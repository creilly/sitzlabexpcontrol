'''
this is our config file for the delay generators.


config is a dictionary of dictionaries, where each entry is a delay generator
with the necessary parameters as key/val pairs in that dictionary

'''

GLOBAL = 'global'
FAKE1 = 'fake delay gen 1'
FAKE2 = 'fake delay gen 2'
MGDELAY = 'm gostein delay gen'
PUMPLAMP = 'pump laser lamps'
PUMPQSW = 'pump laser q-switch'
PROBELAMP = 'probe laser lamps'
PROBEQSW = 'probe laser q-switch'


DG_CONFIG = {
    GLOBAL:{
        'host_machine_ip':'localhost',
        'serve_on_port':'9002',
        'url':'ws://localhost:9002'
        },
    MGDELAY:{
        'usb_chan':'COM3'
        },
    FAKE1:{
        'usb_chan':None
        },
    FAKE2:{
        'usb_chan':None
        }
}