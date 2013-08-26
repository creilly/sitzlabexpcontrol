# SEE LAB NOTEBOOK CR-1-51 for decoding of symbols
'''
alpha := laser counter
alpha_o := laser counter offset
beta := dye wavelength dial minus offset <- the offset changes only when server is started
gamma := crystal angle
delta := crystal counter
delta_o := crystal counter offset <- this changes when you 'set tuned'

polyPredict: gamma(beta) = A + B*beta + C*beta^2 + J*beta^3   - given a pdl counter, compute crystal position

h: delta(gamma) = gamma + delta_o      - given a crystal counter, return with an offset due to calibration

F: amplitude for oscillation offset (in crystal steps)

G: period for oscillation offset (in crystal steps)

'''

from config.crystalsknownpositions import CC_LOOKUP_KDP, CC_LOOKUP_BBO
from math import sin

class CrystalCalibrator(object):
    A = 0.0
    B = 42.0
    C = 0.0
    J = 0.0
    
    lookupTable = None
    
    E = 24200.0 #E is the dial value about which you are Taylor expanding for polyPredict    
    F = 100.0
    G = 0.0
    
    def __init__(self):
        self.phase = 0
        self.calibrateCrystal((24200,0))        

    def getPosition(self,beta):
        return int(
            self.h(
                self.f(
                    beta
                )
            )
        )

    def f(self,beta):
        return self.modulate(self.searchLookupTable(beta))

    def polyPredict(self,dialValue):
        normDial = dialValue - self.E
        return self.A + self.B * normDial + self.C * (normDial ** 2) + self.J * (normDial ** 3)
  
    #add offset to crystal counter representative of 'tuned position', set by calibrateCrystal
    def h(self,gamma):
        return gamma + self.delta_o
        
    def searchLookupTable(self,dialValue):
        lowMatch, highMatch = -99999, 99999
        #search through lookupTable for closest low and high matched values
        for knownDial, knownCrystal in self.lookupTable:
            diff = knownDial - dialValue
            if diff < 0 and diff > lowMatch:
                lowMatch = diff
                lowPoint = (knownDial,knownCrystal)
            if diff > 0 and diff < highMatch:
                highMatch = diff
                highPoint = (knownDial,knownCrystal)
            if diff == 0:
                return knownCrystal
        if lowMatch == -99999 or highMatch == 99999:
            print 'outside bounds of table! reverting to poly'
            return self.polyPredict(dialValue)
        #calculate the slope between these two closest points and return linearly interpolated result
        highDial, highCrystal = highPoint
        lowDial, lowCrystal = lowPoint
        slope = (highCrystal-lowCrystal)/(highDial-lowDial)
        crystalValue = slope*(dialValue-lowDial) + lowCrystal
        return crystalValue

    def modulate(self,crystalPosition):
        return crystalPosition + self.F * sin(2.0 * 3.14159 * crystalPosition / self.G + self.phase * 3.14159 / 180.0)

    # phase varies between 0 and 360 degrees
    def setPhase(self,phase):
        self.phase = phase

    def getPhase(self):
        return self.phase
   
    def calibrateCrystal(self,point):
        #surf wavelength, crystal counter = point
        beta_tilde, delta_tilde = point
        self.delta_o = delta_tilde - self.f(beta_tilde)

class KDPCrystalCalibrator(CrystalCalibrator):
    A = -1063.3514072
    B = -37.33554476
    C = -.00087387543
    J = .00060357878
    
    lookupTable = CC_LOOKUP_KDP
    
    F = 0.0
    G = 150.0
    ''' old parameters
    A = -504.120788450589
    B = -33.1515246331159
    C = 0.005625477013309
    J = 0
    '''
    
        

class BBOCrystalCalibrator(CrystalCalibrator):
    
    lookupTable = CC_LOOKUP_BBO
    
    #fit parameters in increasing order (0th to 3rd)
    A = -4307.18196969
    B = -140.63613325
    C = .06216634761159
    J = .00051704324296
    
    F = 0.0
    G = 120.0
    
    ''' old parameters
    A = -44424.4575132
    B = -143.3 #-138.667918180
    C = 0.0 #.0538565295334
    J = 0
    '''
    
   
    ''' old parameters from a fit done 5/15/13
    A = -10335.4222677693
    B = -132.88818192068
    C = 0.056018564103627
    J = -0.000217154228082    
    D = 0.02400960384
    E = 24265
    '''

class TestCrystalCalibrator(CrystalCalibrator): pass
