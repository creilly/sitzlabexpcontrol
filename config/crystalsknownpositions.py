'''
this is our config file for the kdp & bbo crystals. it serves as
a lookup table of positions for the crystalcalibrator.lookupTable
method.


for the two dictionaries: the key:value pairs are 
pdl_dial:kdp_steps(bbo_steps)

each dictionary must have a special 'zero' key that specifies the
wavelength for which 0 KDP(BBO) steps would be tuned. this can be
computed by using http://www.arachnoid.com/polysolve/ to fit the
positions data set (after normalizing the dial reading) to a 3rd 
order poly and using the 0th order term.

!!!these dictionaries must only be collected in the same day!!!
if you must add/modify you should recollect the entire dictionary!

'''

ZERO = 'zero'


CC_LOOKUP_KDP = {
    ZERO:-1327.9981,
    24280:-2950,
    24276.8:-2840,
    24250:-1910,
    24236.5:-1410,
    24209.9:-430,
    24196.5:75,
    24190:285
}

CC_LOOKUP_BBO = {
    ZERO:5301.38787,
    24280:-11490,
    24276.8:-11060,
    24250:-7480,
    24236.5:-5620,
    24209.9:-1860,
    24196.5:40,
    24190:980
}
