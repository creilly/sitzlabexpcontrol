# reads in specified files, calculates an average & standard deviation at each angle, writes that to a csv

import numpy as np
from os import path, listdir


DIRECTORY = 'Z:/data/pooh/2015-03-14/S3/polSweepDiffZeroed'
SEPARATOR = '\t'
OUTPUT_NAME = '../diffZeroed_avg.csv'

files = listdir(DIRECTORY)

aveDataMatrix = None
stdDataMatrix = None


for file in files:
    if not 'pol_sweep' in file: continue
    filename = path.join(DIRECTORY, file)
    thisData = np.loadtxt(filename, delimiter=SEPARATOR, usecols=(1,2,3))
    thisData = thisData[thisData[:,0].argsort()]
    #print thisData
    if aveDataMatrix == None:
        angles, ave, std = np.hsplit(thisData,3)
        aveDataMatrix = np.hstack((angles, ave))
        stdDataMatrix = np.hstack((angles, std))
    else:
        aveDataMatrix = np.hstack((aveDataMatrix, np.hsplit(thisData,3)[1]))
        stdDataMatrix = np.hstack((stdDataMatrix, np.hsplit(thisData,3)[2]))
        
       
avgData = np.empty((len(aveDataMatrix),2))
for i,line in enumerate(aveDataMatrix):
    angle = line[0]
    values = line[range(1,len(line))]
    avgData[i] = (angle, np.mean(values))

stdData = np.empty((len(stdDataMatrix),2)) 
for i,line in enumerate(stdDataMatrix):
    angle = line[0]
    values = line[range(1,len(line))]
    combinedSTD = 0.
    for j,val in enumerate(values):
        combinedSTD += val**2 + (aveDataMatrix[i,1] - avgData[i,1])**2
        #              sigma_set^2   + (mu_set - mu_total)^2
        #see: http://stats.stackexchange.com/questions/55999/is-it-possible-to-find-the-combined-standard-deviation
        
    stdData[i] = (angle, np.sqrt(combinedSTD/len(files)))

combData = np.hstack((avgData, np.hsplit(stdData,2)[1]))

outputFilename = path.join(DIRECTORY, OUTPUT_NAME)
np.savetxt(outputFilename, combData, delimiter=",")

