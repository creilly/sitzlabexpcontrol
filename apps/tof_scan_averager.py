# reads in specified files, calculates an average & standard deviation at each angle, writes that to a csv

import numpy as np
from os import path, listdir, walk
import sys


DIRECTORY = path.abspath('Z:/data/pooh/2015-03-18/S3/TimeOfFlight/BS110')
SEPARATOR = '\t'

OUTPUT_RAW = True

SHOTS = 50

files = listdir(DIRECTORY)

aveDataMatrix = None
stdDataMatrix = None

subDirList = []

for i, (root, dirNames, files) in enumerate(walk(DIRECTORY)):
    if i == 0:
        outputFileNames = dirNames
    else:
        subDirList.append(root)
        

for i, subDir in enumerate(subDirList):
    if 'HWP' not in subDir: continue
    print 'adding up '+outputFileNames[i]
    output_name = outputFileNames[i]+'.csv'
    aveDataMatrix = None
    stdDataMatrix = None
    filesList = listdir(subDir)
    for file in filesList:
        filename = path.join(DIRECTORY,subDir,file)
        thisData = np.loadtxt(filename, delimiter=SEPARATOR, usecols=(1,2,3))
        thisData = thisData[thisData[:,0].argsort()]
        offset = np.mean(thisData[1:4,1])
        if aveDataMatrix == None:
            angles, ave, std = np.hsplit(thisData,3)
            aveDataMatrix = np.hstack((angles, ave-offset))
            stdDataMatrix = np.hstack((angles, std))
            rawDataMatrix = np.hstack((angles, ave-offset, std))
        else:
            aveDataMatrix = np.hstack((aveDataMatrix, np.hsplit(thisData,3)[1]-offset))
            stdDataMatrix = np.hstack((stdDataMatrix, np.hsplit(thisData,3)[2]))
            rawDataMatrix = np.hstack((rawDataMatrix, np.hsplit(thisData,3)[1]-offset, np.hsplit(thisData,3)[2]) )
    
    if OUTPUT_RAW:
        print rawDataMatrix[9]
        outputFilename = path.join(DIRECTORY, "RAW_"+output_name)
        fmtList = ['%d']  #format string for delay
        for i in range(2*len(filesList)):
            fmtList.append('%.6f')  #format string for voltage & std recorded
        np.savetxt(outputFilename, rawDataMatrix, delimiter=",", fmt=fmtList)
    
    
    #print aveDataMatrix
    avgData = np.zeros((len(aveDataMatrix),2))
    for i,line in enumerate(aveDataMatrix):
        time = line[0]
        values = line[range(1,len(line))]
        avgData[i] = (time, np.mean(values))
    
    
    stdData = np.empty((len(stdDataMatrix),2)) 
    for i,line in enumerate(stdDataMatrix):
        time = line[0]
        values = line[range(1,len(line))]
        combinedSTD = 0.
        for j,val in enumerate(values):
            val = val*np.sqrt(SHOTS) #convert STDM back to STD
            combinedSTD += SHOTS*val**2 + SHOTS*(aveDataMatrix[i,j+1] - avgData[i,1])**2
            #              sigma_set^2   + (mu_set - mu_total)^2
            #see: http://stats.stackexchange.com/questions/55999/is-it-possible-to-find-the-combined-standard-deviation
        resultingSTD = np.sqrt(combinedSTD/(SHOTS*len(files)))
        resultingSTDoM = resultingSTD/np.sqrt(SHOTS*len(files))
        stdData[i] = (time, resultingSTDoM)

    combData = np.hstack((avgData, np.hsplit(stdData,2)[1]))

    fmtList = ['%d','%.6f','%.6f']  #format string for delay
    outputFilename = path.join(DIRECTORY, output_name)
    np.savetxt(outputFilename, combData, delimiter=",", fmt=fmtList)

