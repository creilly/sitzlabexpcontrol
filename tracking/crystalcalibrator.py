# SEE LAB NOTEBOOK CR-1-51 for decoding of symbols
class CrystalCalibrator(object):
    A = 0.0
    B = 42.0
    C = 0.0
    J = 0.0
    
    D = 0.02400960384
    E = 24200.0
    def __init__(self,dyeCalibrationPoint = (0,24222)):        
        self.calibrateDye(dyeCalibrationPoint)
        self.calibrateCrystal((0,0))

    def getPosition(self,alpha):
        return int(
            self.h(
                self.f(
                    self.g(alpha)
                )
            )
        )

    def f(self,beta):
        return self.A + self.B * beta + self.C * (beta ** 2) + self.J * (beta ** 3)

    def g(self,alpha):
        return self.D * (alpha - self.alpha_o)
        
    def h(self,gamma):
        return gamma + self.delta_o

    def calibrateDye(self,point):
        alpha_bar, beta_bar_prime = point
        beta_bar = beta_bar_prime - self.E
        self.alpha_o = alpha_bar - beta_bar / self.D

    def calibrateCrystal(self,point):
        alpha_tilde, delta_tilde = point
        self.delta_o = delta_tilde - self.f(self.g(alpha_tilde))

class KDPCrystalCalibrator(CrystalCalibrator):
    
    A = -504.120788450589
    B = -33.94 #-33.1515246331159
    C = 0.0 #0.005625477013309
    J = 0
    
    D = 0.02400960384
    E = 24444.496
        

class BBOCrystalCalibrator(CrystalCalibrator):
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
