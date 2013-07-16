# SEE LAB NOTEBOOK CR-1-51 for decoding of symbols
'''
this, chris, is what we call a block comment, so we don't have to go dig out CR-1-51

alpha := laser counter
alpha_o := laser counter offset
beta := dye wavelength dial minus offset <- the offset changes only when server is started
gamma := crystal angle
delta := crystal counter
delta_o := crystal counter offset <- this changes when you 'set tuned'

d := ratio of dye wavelength dial to laser counter

f: gamma(beta) = A + B*beta + C*beta^2 + J*beta^3   - given a pdl counter, compute crystal position
g: beta(alpha) = d*(alpha - alpha_o)    - given a pdl counter, return the dial value
h: delta(gamma) = gamma + delta_o      - given a crystal counter, return with an offset due to calibration

'''

from config.crystalsknownpositions import CC_LOOKUP_KDP, CC_LOOKUP_BBO

class CrystalCalibrator(object):
    A = 0.0
    B = 42.0
    C = 0.0
    J = 0.0
    
    D = 0.02400960384
    E = 24200.0
    def __init__(self):        
        self.calibrateDye((0,24222))
        self.calibrateCrystal((0,0))
        self.lookupTable = CC_LOOKUP_KDP

    def getPosition(self,alpha):
        return int(
            self.h(
                self.f(
                    self.g(alpha)
                )
            )
        )

    def f(self,beta):
        return self.searchLookupTable(beta)
        #return self.A + self.B * beta + self.C * (beta ** 2) + self.J * (beta ** 3)

    def g(self,alpha):
        return self.D * (alpha - self.alpha_o)
        
    def h(self,gamma):
        return gamma + self.delta_o
        
    def searchLookupTable(self,beta):
        dialValue = beta + self.E
        try:
            return self.lookupTable[dialValue]
        except KeyError:
            lowMatch, highMatch = -99999, 99999
            #search through lookupTable for closest low and high matched values
            for key, value in self.lookupTable.items():
                if key == 'zero': continue
                diff = key - dialValue
                if diff < 0 and diff > lowMatch:
                    lowMatch = diff
                    lowToUse = {}
                    lowToUse[key] = value
                if diff > 0 and diff < highMatch:
                    highMatch = diff
                    highToUse = {}
                    highToUse[key] = value
            if lowMatch == -99999 or highMatch == 99999:
                print 'outside bounds of table! using 3rd order poly'
                return self.f(self.g(dialValue))
            #calculate the slope between these two closest points and return linearly interpolated result
            slope = (highToUse.values()[0]-lowToUse.values()[0])/(highToUse.keys()[0]-lowToUse.keys()[0])
            newPos = slope*(dialValue-self.E)
            return self.h(newPos) #add crystal offset and return

    def calibrateDye(self,point):
        #steps, dial = point
        alpha_bar, beta_bar_prime = point
        #dial minus the universal offset E (typically 24200)
        beta_bar = beta_bar_prime - self.E
        #steps offset defined to be steps minus (dial minus offset) scaled by steps per dial value
        self.alpha_o = alpha_bar - beta_bar / self.D

    def calibrateCrystal(self,point):
        #dye counter, crystal counter = point
        alpha_tilde, delta_tilde = point
        self.delta_o = delta_tilde - self.f(self.g(alpha_tilde))

class KDPCrystalCalibrator(CrystalCalibrator):
    
    self.lookupTable = CC_LOOKUP_KDP
    
    A = -504.120788450589
    B = -33.1515246331159
    C = 0.005625477013309
    J = 0
    
    D = 0.02400960384
    E = 24444.496
        

class BBOCrystalCalibrator(CrystalCalibrator):
    
    self.lookupTable = CC_LOOKUP_BBO
    
    #fit parameters in increasing order (0th to 3rd)
    A = -44424.4575132
    B = -143.3 #-138.667918180
    C = 0.0 #.0538565295334
    J = 0

    D = 0.02400960384
    E = 24224.1476
   
    ''' old parameters from a fit done 5/15/13
    A = -10335.4222677693
    B = -132.88818192068
    C = 0.056018564103627
    J = -0.000217154228082    
    D = 0.02400960384
    E = 24265
    '''

class TestCrystalCalibrator(CrystalCalibrator): pass
