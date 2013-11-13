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
from time import sleep

CLOCKPERIOD = 50 #in nanoseconds
AD9501TIMECONST = .2 #in nanoseconds (eg. 200picoseconds)



class DelayGenerator:
    def __init__(self,confDict):
        self.hardwareVersion = confDict['dg_version']
        self.timeToDelay = confDict['delay']
        idToLookFor = confDict['ard_id']
        self.COMPort = self.findCOMPort(idToLookFor)
        self.ser = serial.Serial(self.COMPort,9600,timeout=5)
       
    def findCOMPort(self,idToFind):
        import win32com.client
        wmi = win32com.client.GetObject ("winmgmts:")
        for usb in wmi.InstancesOf("Win32_SerialPort"):
            if usb.PNPDeviceID.split("\\")[2] == idToFind:
                name = usb.Name.split("(")[1]
                return name.strip(")")

    def writeToUSB(self,strToWrite):
        self.ser.write(strToWrite)
        sleep(.01) #give the arduino 10milliseconds to respond, it is not instantaneous
        echo = self.ser.readline().replace('\r\n','') #under both versions of the sketch, the ardy echoes the result
        if echo == str(strToWrite): return True
        if echo != str(strToWrite): return False
        
    #this is specifically for the arduino mega operating MGostein's DG, Mav's DG takes the time in ns directly
    def convertDelay(self,timeToDelay):
        #split requested delay to the clock and the AD9501, convert to binary
        #clean up binary string and pad to specified length (clock = 20bits, AD9501 = 8bits)
        clockCycles = int(timeToDelay/CLOCKPERIOD)
        clockCyclesBinary = bin(clockCycles).rpartition('b')[2].rjust(20,'0')
        AD9501Intervals = int((timeToDelay % CLOCKPERIOD) / AD9501TIMECONST)
        AD9501IntervalsBinary =  bin(AD9501Intervals).rpartition('b')[2].rjust(8,'0')
        stringToSend = clockCyclesBinary+AD9501IntervalsBinary
        return stringToSend

    def setDelay(self,timeToDelay):
        #get a timeToDelay, calculate # of 50ns clock cycles and 
        #the number of 10ps intervals, convert these to binary, send
        #these strings to channel via usb, fire callback when device replies
        self.timeToDelay = timeToDelay
        if self.hardwareVersion == "gostein":
            stringToSend = self.convertDelay(self.timeToDelay)
        elif self.hardwareVersion == "maverick":
            stringToSend = str(self.timeToDelay)
        return self.writeToUSB(stringToSend)

    def getDelay(self):
        return self.timeToDelay
        
    def close(self):
        self.ser.close()


class FakeDelayGenerator(DelayGenerator):
    def __init__(self,confDict):
        self.timeToDelay = confDict['delay']

    def writeToUSB(self,strToWrite):
        print "This is when I'd write to the USB, but I'm not because I'm a big ol' liar."
        print strToWrite
        echo = strToWrite
        if echo == strToWrite: return True
        if echo != strToWrite: return False
    
    def close(self):
        print "What are you thinking? There is no USB device to close!"
        