'''by stevens4, mod: stevens4
2014-03-04: added the logFile class with methods for reading, writing,
creating logFiles for other objects like the LoggedStepperMotor.

2013-06-13: switched over to using full os method functionality so these
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
        os.makedirs(path)

#given a measurementType (string), dataArray (numpyArray), and parentPath (path)
#save a CSV file according to our data structure (see above)
def saveCSV(measurementType,dataArray,parentPath,description=None):
    path, filename = filenameGen(measurementType)
    path = os.path.join(parentPath,path)
    checkPath(path)
    np.savetxt(os.path.join(path,filename+(('_%s' % description) if description is not None else '')+".csv"), dataArray, delimiter=",")
    
class LogFile:
    def __init__(
        self,
        logFileName
    ):
        self.logFileName = logFileName
        try:
            self.logFile = open(self.logFileName, 'r+')
        except IOError:
            self.logFile = open(self.logFileName, 'w+')
    
    def readLastLine(self):
        lines = self.logFile.readlines()
        last_line = '\n'
        i = 1
        while last_line == '\n' or i <= len(lines):
            last_line = lines[len(lines)-i]
            i += 1
        if last_line == '\n':
            last_line = 'never\t0\tforwards'
        lastLineTuple = tuple(last_line.strip().split('\t'))
        return lastLineTuple
        
    def update(self,tupleToWrite):
        timestamp = str(datetime.datetime.now())
        logElements = []
        logElements.append(timestamp)
        for element in tupleToWrite:
           logElements.append(str(element))
           #logElements.append('\t')
        logEntry = '\t'.join(logElements)
        self.logFile.write(logEntry+'\n')
    
    def close(self):
        self.logFile.close()
    
