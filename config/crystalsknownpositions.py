'''
this is our config file for the kdp & bbo crystals. it serves as
a lookup table of positions for the crystalcalibrator.searchLookupTable
method.


for the two dictionaries: the key:value pairs are 
pdl_dial:kdp_steps(bbo_steps)


!!!these dictionaries must only be collected in the same day!!!
if you must add/modify you should recollect the entire dictionary!

these were collected on 8/23/13 by stevens4. see gdoc 'kdp/bbo from 8/23/13'

temp control pots were set to 7.3 & 6.25 for KDP & BBO

'''

CC_LOOKUP_KDP = (
    (24190.0,11900),
    (24196.5,11620),
    (24209.9,11220),
    (24236.5,10190),
    (24250.0,9700),
    (24276.8,8770),
    (24280.0,8660)
)

CC_LOOKUP_BBO = (
    (24190.0,-800),
    (24196.5,-1830),
    (24209.9,-3900),
    (24236.5,-7780),
    (24250.0,-9790),
    (24276.8,-13480),
    (24280.0,-13910)    
)
