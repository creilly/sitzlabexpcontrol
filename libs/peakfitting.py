'''
by stevens4, last mod: 2013-06-10
takes in a dataArray, determines where the peaks are, determines initial fit parameters
then does a least squares fit to a gaussian and plots the results
if no dataArray is specified then a file browser will open

returns a list of pyqtgraph PlotItems of fitted curves and the 
final fitted parameters w/ reduced chi-squared
'''

import numpy as np
from scipy.optimize import curve_fit
from Tkinter import Tk
from tkFileDialog import askopenfilename
import matplotlib.pyplot as mplot
from scipy import signal
from scipy import optimize
from scipy import stats
import pyqtgraph as pg



def gauss(x, cent, amp, sigma, off):
    return amp*np.exp(-(x-cent)**2/(2*sigma**2)) + off
''' 
def gauss(x, p):
    return p[1]*np.exp(-(x-p[0])**2/(2*p[2]**2)) + p[3]
'''
def residuals(p, yMeas, x):
    err = yMeas - gauss(x,p)
    return err
    
def peakWalk(yValues,startLoc):
    if yValues[startLoc] < yValues[startLoc+1]:
        startLoc = peakWalk(yValues,startLoc+1)
    elif yValues[startLoc] < yValues[startLoc-1]:
        startLoc = peakWalk(yValues,startLoc-1)
    return startLoc


def peakWalkDown(yValues,peakLoc,halfLoc,n):
    if halfLoc >= len(yValues) or halfLoc <= 0:
        return halfLoc
    if yValues[halfLoc] >= n*yValues[peakLoc]:
        halfLoc = peakWalkDown(yValues,peakLoc,halfLoc+1,n)
    return halfLoc


def specAnalysis(dataArray=None,filename=None,quiet=True,extPlot=False):
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    
    #set up options for a file browser for user to pick file if no dataArray is specified
    if dataArray == None:
        fileOpts = options = {}
        options['filetypes'] = [('all files', '.*'), ('comma-separated values', '.csv')]
        options['initialdir'] = 'Z:\data\pooh'
        filename = askopenfilename(**fileOpts) # show an "Open" dialog box and return the path to the selected file
        print(filename)
        filename = "Z:\data\pooh\TestDataFile.csv"
        #parse this datafile for xValues and yValues. file MUST BE CSV!!
        dataArray = np.genfromtxt(filename, delimiter=',', skip_header=1, usecols=(0,1,2))

    #determine a typical peak width by 'walking' the brightest peak
    brightSpot = np.where(dataArray[ : ,1] == np.amax(dataArray[ : ,1]))[0][0]
    typHalfWidthInd = peakWalkDown(dataArray[ : ,1],brightSpot,brightSpot+1,.5)
    typHalfWidth = abs(dataArray[brightSpot,0]-dataArray[typHalfWidthInd,0])
    
    #if not quiet: print brightSpot, typHalfWidth
    
    #use this function to identify the peak locations, for a range of peak widths use from half the brightest width to twice this
    peakIndex = signal.find_peaks_cwt(dataArray[ : ,1],np.arange(2.5*typHalfWidth,3*typHalfWidth),noise_perc=0)
    #if not quiet: print dataArray[peakIndex]

    #define the list of lists of initial parameters for the least squares fitting
    initParams = []
    peakLocs = []
    
    #determine the offset guess first, all will use the same, being the average of the 10th percentile of data
    minima = dataArray[np.where(dataArray[ : ,1] <= .1*np.mean(dataArray[ : ,1])),1]
    if len(minima) > 1:
        off = np.mean(minima)
    else:
        off = (dataArray[0,1]+dataArray[len(dataArray)-1,1])/2
    
    #determine the center, amplitude, and width parameters for each peak by 'walking' up to the crest
    #then 'walking down' to the half-amplitude position
    for pkInd in peakIndex:
        peakLoc = peakWalk(dataArray[ : ,1],pkInd)
        cent, amp = dataArray[peakLoc,0:2]
        amp = amp - off
        #print 'width: '+str(np.where(dataArray[ : ,1] >= .5*amp).size())
        halfMaxLoc = peakWalkDown(dataArray[ : ,1],peakLoc,peakLoc+1,.5)
        if halfMaxLoc == len(dataArray): halfMaxLoc = halfMaxLoc - 1
        sigma = .8*(dataArray[halfMaxLoc,0]-dataArray[peakLoc,0])
        
        peakLocs.append(peakLoc)
        initParams.append([cent.tolist(), amp.tolist(), sigma, off.tolist()])

    if quiet == False:    
        print '\n\nInitial Fit Parameters: '
        template = "{0:13}|{1:13}|{2:15}|{3:11}" # column widths
        print template.format("center", "amplitude", "sigma", "offset") # header
        for initParam in initParams: 
            print template.format(*initParam)
        print '\n \n'

    initCurves = []
    
    if extPlot == True:
        #generate a plot of the data w/ errorbars
        plotTitle = "Spectrum "+str(filename)
        plotWidget = pg.plot(title=plotTitle)
        plotLegend = pg.LegendItem(offset=(400,50))
        plotLegend.setParentItem(plotWidget.getPlotItem())
        x = dataArray[ : ,0]
        y = dataArray[ : ,1]
        dataPlotItem = plotWidget.plot(x, y, pen=None, symbol='+')
        plotLegend.addItem(dataPlotItem, 'Data')
        errorBars = pg.ErrorBarItem(x=dataArray[ : ,0],y=dataArray[ : ,1],top=dataArray[ : ,2],bottom=dataArray[ : ,2],beam=.05)
        plotWidget.addItem(errorBars)
        for initPar in initParams:
            #plot the curve based on the inital parameters
            initCurve = pg.PlotDataItem(dataArray[ : ,0], gauss(dataArray[ : ,0], *initPar), pen='b')
            initCurves.append(initCurve)
            plotWidget.addItem(initCurve)
        dummy = raw_input("Press enter to quit.")
           
           
        
    resultFitPar = []
    fitCurves = []
    
    if quiet == False:
        print '\nFitted Parameters: '
        template2 = "{0:13}|{1:13}|{2:15}|{3:11}|{4:11}" # column widths
        print template2.format("center", "amplitude", "sigma", "offset", "rChi2") # header
    
    #generate a curve for each peak based on the initParams on the canvas, same for fitParams version
    for i in range(len(peakIndex)):
        #fit the peak over 90th percentile of values
        fitRangeEndPt = peakWalkDown(dataArray[ : ,1],peakLocs[i],peakLocs[i]+1,.2)-1
        fitWidth = 2*(fitRangeEndPt-peakLocs[i])
        fitRange = range(peakLocs[i]-fitWidth,peakLocs[i]+fitWidth)
        fitRange = filter(lambda x: x >= 0, fitRange)
        fitRange = filter(lambda x: x<len(dataArray), fitRange)
        
        #do a least-squares fit starting with the inital parameters & plot result
        try:
            fitParamsNumpy, covMatr = optimize.curve_fit(gauss, dataArray[fitRange,0], dataArray[fitRange,1], p0=initParams[i], sigma=dataArray[fitRange,2])
            failed = False
        except RuntimeError:
            if not quiet: print 'No good fit found! Throwing this one out.'
            failed = True
        if failed: continue
        
        #fitParams, success = optimize.leastsq(residuals, initParams[i], args=(dataArray[fitRange,1],dataArray[fitRange,0]))
        fitX = np.linspace(dataArray[fitRange[0],0],dataArray[fitRange[-1],0],1000)
        fitCurve = pg.PlotDataItem(fitX, gauss(fitX, *fitParamsNumpy), pen='g')
      
        #calculate the chi-square
        degOFree = len(fitRange)-1-4
        chi2, pval = stats.chisquare(dataArray[fitRange,1],gauss(dataArray[fitRange,0],*fitParamsNumpy),degOFree)
        redChi2 = chi2/degOFree

        fitParams = fitParamsNumpy.tolist()
        fitParams.append(redChi2)
        if not quiet: print template2.format(*fitParams)
        
        resultFitPar.append(fitParams)
        fitCurves.append(fitCurve)
        
    if extPlot == True:
        for fitCurve in fitCurves: plotWidget.addItem(fitCurve)
        plotLegend.addItem(initCurve, 'Inital Guess')
        plotLegend.addItem(fitCurve, 'Fitted Result')


    return fitCurves, resultFitPar
    



    
def main():
    #for testing purposes, override the file open protocol by specifying a datafile here
    #filename = "Z:\\data\\pooh\\2013-05-22\\populationsBottle\\SS_H2J03_052213_2.csv"
    #filename = "Z:\\data\\pooh\\2013-06-10\\thirdHarmonicPower\\1723.csv"
    filename = "Z:\\data\\pooh\\TestDataFile.csv"
    dataArray = np.genfromtxt(filename, delimiter=',', skip_header=1, usecols=(0,1,2))
    plotWidget,fitParams = specAnalysis(dataArray=dataArray, filename=filename, quiet=False, extPlot=True)
    
    dummy = raw_input("Press enter to quit.")

    
if __name__ == '__main__':
    main()