'''
this is our config file for the lid.

it is a simple dictionary of 4 named positions of
the lid and the counter values for each

values in comments are from sheng's config.txt on pooh's D:\forlab\rotator\

actual values are based on finding the scattering position using the probe laser
(see Stevens lab notebook #2 on 2/11/14) and extrapolating the same deltas from
sheng's positions but inverting the direction
'''


LID_POSITIONS = {
    'scatter':-27650, #193600,
    'sputter':65950, #100000,
    'LEED':112950, #53000,
    'LIPD':160950 #5000
}
 
DEBUG_LID_CONFIG = {
    'logfile':'debuglidlog.txt',
    'relay_channel':'alpha/port0/line3'
}

LID_CONFIG = {
    'logfile':'lidlog.txt',
    'relay_channel':'dev1/port0/line0',
    'step_channel':'dev2/port0/line7',
    'counter_channel':'dev2/ctr6',
    'direction_channel':'dev2/port0/line5',
    'step_rate':500.0,
    'backlash':1525
}