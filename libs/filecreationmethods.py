'''by stevens4, mod: 2013-06-13
last update: switched over to using full os method functionality so these
methods should be OS independent

some simple functions to help with creation of files on our network drive

our data is organized thusly:
    Z:\data\[chamber]\[date]\[measurementType]\[time]
        [chamber] = pooh, tigger, or piglet
        [date] = date data was saved
        [measurementType] = measurements specific to that experiment, 
            eg. popBottle (populations of gas from a bottle) or kdpScans
        [time] = time data was saved
'''

import csv
import datetime
import os
import numpy as np

#generates a relative path and filename according to our data structure given a measurement type
def filenameGen(measurementType):
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    time = datetime.datetime.now().strftime("%H%M")
    path = os.path.join(date,measurementType)
    filename = time
    return path, filename

#checks if absolute path exists, if path doesn't exist, will be created
def checkPath(path):
    if not os.path.exists(path):
        print "Making "+str(path)
        os.makedirs(path)

#given a measurementType (string), dataArray (numpyArray), and parentPath (path)
#save a CSV file according to our data structure (see above)
def saveCSV(measurementType,dataArray,parentPath,description=None):
    path, filename = filenameGen(measurementType)
    path = os.path.join(parentPath,path)
    checkPath(path)
    np.savetxt(os.path.join(path,filename+(('_%s' % description) if description is not None else '')+".csv"), dataArray, delimiter=",")
