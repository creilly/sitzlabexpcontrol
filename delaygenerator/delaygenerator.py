'''
by stevens4. last update on 2013/06/19 by stevens4
an object that has several methods for communicating over USB to
a delay generator circuit. user specifies a USB port to communicate on
at initialization. user then calls the setDelay method with a time in
nanoseconds to delay by. these methods will convert this to a binary format
in number of CLOCKPERIOD cycles and any additional finer time constant
AD9501TIMECONST. Originally designed for use with M. Gostein's Delay Generator
which requires 28bits (which is why everything is padded to 28bits) and with
DelayGenPython.ino loaded onto the Arduino.

Computer --USB--> arduino --ribbon--> M. Gostein's circuit --coax--> lasers

'''

import serial

CLOCKPERIOD = 50 #in nanoseconds
AD9501TIMECONST = .2 #in nanoseconds (eg. 200picoseconds)

class DelayGenerator:
    def __init__(self,usbChan):
        self.timeToDelay = 0
        self.ser = serial.Serial(usbChan,9600,timeout=5)

    def __enter__(self):
        return self
        
    def writeToUSB(self,strToWrite):
        self.ser.write(strToWrite)
        echo = self.ser.readline().replace('\r\n','')
        if echo == strToWrite: return True
        if echo != strToWrite: return False
        
    def convertDelay(self,timeToDelay):
        #split requested delay to the clock and the AD9501, convert to binary
        #clean up binary string and pad to specified length (clock = 20bits, AD9501 = 8bits)
        clockCycles = int(timeToDelay/CLOCKPERIOD)
        clockCyclesBinary = bin(clockCycles).rpartition('b')[2].rjust(20,'0')
        AD9501Intervals = int((timeToDelay % CLOCKPERIOD) / AD9501TIMECONST)
        AD9501IntervalsBinary =  bin(AD9501Intervals).rpartition('b')[2].rjust(8,'0')
        stringToSend = clockCyclesBinary+AD9501IntervalsBinary
        return stringToSend

    def setDelay(self,timeToDelay,callback=lambda:None):
        #get a timeToDelay, calculate # of 50ns clock cycles and 
        #the number of 10ps intervals, convert these to binary, send
        #these strings to channel via usb, fire callback when device replies
        self.timeToDelay = timeToDelay
        stringToSend = self.convertDelay(self.timeToDelay)
        if self.writeToUSB(stringToSend):
            print 'Write Succeeded!'
            self.onDelaySet(callback)
        else:
            print 'Write Failed!'

    def onDelaySet(self,callback):        
        callback()

    def getDelay(self):
        return self._timeToDelay
        
    def close(self):
        self.ser.close()

