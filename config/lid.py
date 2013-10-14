'''
this is our config file for the lid.

it is a simple dictionary of 4 named positions of
the lid and the counter values for each

values are from sheng's config.txt on pooh's D:\forlab\rotator\
'''


LID_POSITIONS = {
    'scatter':193600,
    'sputter':100000,
    'LEED':53000,
    'LIPD':5000
}
 
DEBUG_LID_CONFIG = {
    'logfile':'debuglidlog.txt',
    'relay_channel':'alpha/port0/line3'
}

LID_CONFIG = {
    'logfile':'lidlog.txt',
    'relay_channel':'dev3/port0/line3',
    'step_channel':'dev3/port0/line7',
    'counter_channel':'dev3/ctr6',
    'direction_channel':'dev3/port0/line5',
    'step_rate':500.0,
    'backlash':1525
}