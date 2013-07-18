'''
this is our config file for the kdp & bbo crystals. it serves as
a lookup table of positions for the crystalcalibrator.searchLookupTable
method.


for the two dictionaries: the key:value pairs are 
pdl_dial:kdp_steps(bbo_steps)


!!!these dictionaries must only be collected in the same day!!!
if you must add/modify you should recollect the entire dictionary!

'''

CC_LOOKUP_KDP = (
    (24190.0,285),
    (24196.5,75),
    (24209.9,-430),
    (24236.5,-1410),
    (24250.0,-1910),
    (24276.8,-2840),
    (24280.0,-2950)
)

CC_LOOKUP_BBO = (
    (24190.0,980),
    (24196.5,40),
    (24209.9,-1860),
    (24236.5,-5620),
    (24250.0,-7480),
    (24276.8,-11060),
    (24280.0,-11490)    
)
