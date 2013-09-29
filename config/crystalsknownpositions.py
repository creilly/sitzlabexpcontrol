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
    (24190,3550),
    (24194.8,3360),
    (24195.8,3350),
    (24196.8,3325),
    (24208.4,2980),
    (24209.4,2910),
    (24210.4,2860),
    (24225,2350),
    (24235.1,2010),
    (24236.1,2020),
    (24237.1,2010),
    (24250,1490),
    (24274.8,650),
    (24275.8,630),
    (24276.8,620),
    (24280,480)
    )


CC_LOOKUP_BBO = (
    (24190,6610),
    (24194.8,5750),
    (24195.8,5630),
    (24196.8,5500),
    (24208.4,3780),
    (24209.4,3640),
    (24210.4,3440),
    (24225,1260),
    (24235.1,-210),
    (24236.1,-310),
    (24237.1,-430),
    (24250,-2300),
    (24274.8,-5760),
    (24275.8,-5890),
    (24276.8,-6010),
    (24280,-6510)
)


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
'''
