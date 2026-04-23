import numpy as np
import matplotlib.pyplot as plt
import scipy.sparse as sparse
from scipy.sparse.linalg import splu

#def SaturationCheck(DataFile, SaturationLevel, PlotRejects=False):
    #SaturatedPulseCounter = 0
    #AcceptedPulseList = []
    #DataFile = list(DataFile)
    #for i in range(len(DataFile)):
        #Check for saturation
        #if max(abs(DataFile[i]))>SaturationLevel: 
            #SaturatedPulseCounter +=1
            #Option to plot saturated pulses (maximum of five)
            #if PlotRejects and SaturatedPulseCounter<5:
                #plt.plot(DataFile[i])
                #plt.show()
        #For non-saturated pulses
        #else: 
            #AcceptedPulseList.append(DataFile[i])
    #return AcceptedPulseList, SaturatedPulseCounter

#def BackgroundCorrection(PulseList, N_BGPoints=100): 
    #for i in range(len(PulseList)):
        #Subtract Background based on average of first N data points           
        #PulseList[i] = (PulseList[i] - np.average(PulseList[i][0:N_BGPoints]))
        #Make Pulse Positive
        #if max(PulseList[i], key=abs)<0: PulseList[i] = -PulseList[i]
    #return PulseList

def WhittakerSmooth(ShapingAmpPulses, lmbd, order=2):
    #https://github.com/mhvwerts/whittaker-eilers-smoother/blob/master/whittaker_smooth.py
    SmoothedShapingPulses = []
    for i in range(len(ShapingAmpPulses)):
        y = ShapingAmpPulses[i]
        m = len(y)
        E = sparse.eye(m, format='csc')
        assert not (order < 0), "d must be non negative"
        shape     = (m-order, m)
        diagonals = np.zeros(2*order + 1)
        diagonals[order] = 1.
        for i in range(order):
            diff = diagonals[:-1] - diagonals[1:]
            diagonals = diff
        offsets = np.arange(order+1)
        D = sparse.diags(diagonals, offsets, shape, format='csc')  
        coefmat = E + lmbd * D.conj().T.dot(D)
        z = splu(coefmat).solve(y)
        SmoothedShapingPulses.append(z)
    return SmoothedShapingPulses 