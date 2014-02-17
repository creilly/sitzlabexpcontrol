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

CLOCKPERIOD = 50. #in nanoseconds
AD9501TIMECONST = .2 #in nanoseconds (eg. 200picoseconds)


class DelayGenerator:
    def __init__(self,confDict):
        self.confDict = confDict
        self.configured = False
        self.timeToDelay = confDict['delay']
        idToLookFor = confDict['ard_id']
        self.COMPort = self.findCOMPort(idToLookFor)
        if self.COMPort is None: 
			print "\n\nWARNING!!! DIDN'T FIND ARDUINO!!"
        else:
            self.ser = serial.Serial(self.COMPort,9600,timeout=5)
            while not self.configured:
                sleep(1) #wait 1s for com port to actually open and be ready to accept input/output, this might be an arduino thing
                if self.ser.readline().replace('\r\n','') == "waiting to configure":
                    print "sending configuration parameters to DDG: "
                    self.configured = self.configureDDG()
        if not self.configured: raise Exception()
        self.partneringEnabled = True
        self.setDelay(self.timeToDelay)
       
    def findCOMPort(self,idToFind):
        import win32com.client
        wmi = win32com.client.GetObject ("winmgmts:")
        for usb in wmi.InstancesOf("Win32_SerialPort"):
            #print usb.PNPDeviceID.split("\\")[2]
            if usb.PNPDeviceID.split("\\")[2] == idToFind:
                name = usb.Name.split("(")[1]
                return name.strip(")")

    def configureDDG(self):
        offset = self.confDict['offset']
        minVoltage = self.confDict['minVoltage']
        maxVoltage = self.confDict['maxVoltage']
        confString = str(offset)+" "+str(minVoltage)+" "+str(maxVoltage)
        print confString
        success = self.writeToUSB(confString)
        return True

    def setDelay(self,timeToDelay):
        #get a timeToDelay, calculate # of 50ns clock cycles and 
        #the number of 10ps intervals, convert these to binary, send
        #these strings to channel via usb, fire callback when device replies
        self.timeToDelay = long(timeToDelay)
        #print '\n\n\n'+'after round '+str(self.timeToDelay)
        stringToSend = str(self.timeToDelay)
        return self.writeToUSB(stringToSend)

    def writeToUSB(self,strToWrite):
        if self.COMPort is None:
            print 'could not find arduino!'
            return False
        else:
            self.ser.write(strToWrite)
            echo = self.ser.readline().replace('\r\n','') #the ardy echoes the result
            #print 'sent '+strToWrite
            #print 'received '+echo+'\n\n\n'
            if echo == str(strToWrite): return True
            if echo != str(strToWrite): return False
            
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
  


'''
depreciated code:

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
'''
  