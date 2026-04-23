## This was edited on 27032026 to stop the 'negative' derivative peaks from being counted as no signal

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

def PeakAcceptance(RawData, SmoothedData, PkProminence=0.6, PkHeight=0.1, Plots=False):
    AcceptedPulseList = []
    AcceptedIndices = []
    PeakIndexList = []
    SmoothedDerivativeList = []
    PileupCounter = 0
    BadTriggerCounter = 0
    UnstableBackgroundCounter = 0
    PulseCounter = 0
    for TriggerIndex, (RawPulse, SmoothedPulse) in enumerate(zip(RawData, SmoothedData)):
        derivative = np.gradient(SmoothedPulse)
       
        PeakIndex, PeakProperties = find_peaks(derivative, prominence=PkProminence, height=PkHeight)
        N_Peaks = len(PeakIndex)

        ## start of added code
        PeakIndex_pos, PeakProperties_pos = find_peaks(derivative, prominence=PkProminence, height=PkHeight)
        PeakIndex_neg, PeakProperties_neg = find_peaks(-derivative, prominence=PkProminence, height=PkHeight)
        PeakIndex = np.sort(np.concatenate([PeakIndex_pos, PeakIndex_neg]))
        N_Peaks = len(PeakIndex)
        ## end of added code
        
        # Check for data sets without a pulse
        if N_Peaks == 0:        
            BadTriggerCounter += 1
            if Plots and BadTriggerCounter<5:      
                fig, (ax1, ax2) = plt.subplots(1,2, figsize=(6, 2))
                ax1.plot(RawPulse)
                ax1.plot(SmoothedPulse)
                ax1.set_title("No Pulse")
                ax2.plot(derivative)
                plt.show()    
        # Check for pile up (data sets with multiple peaks)
        elif N_Peaks >1:
            PileupCounter +=1
            if Plots and PileupCounter<5:
                print("Multiple Pulses")
                fig, (ax1, ax2) = plt.subplots(1,2, figsize=(6, 2))
                ax1.plot(RawPulse)
                ax1.plot(SmoothedPulse)
                ax1.scatter(PeakIndex, SmoothedPulse[PeakIndex], marker="x", color="red", zorder=10)
                ax1.set_title("No Pulse")
                ax2.plot(derivative)
                plt.show() 
                ##print(PeakProperties)

                ## start of new code
                print("Pos properties:", PeakProperties_pos)
                print("Neg properties:", PeakProperties_neg)
                ## end of new code
                
        # Check for data sets where pre-pulse signal hasn't returned to baseline
        elif N_Peaks == 1:
            
            ## if np.argmin(SmoothedPulse)>np.argmax(SmoothedPulse):

            ## start of added code
            pulse_is_positive = len(PeakIndex_pos) >= len(PeakIndex_neg)
            if pulse_is_positive:
                unstable = np.argmin(SmoothedPulse) > np.argmax(SmoothedPulse)
            else:
                unstable = np.argmax(SmoothedPulse) > np.argmin(SmoothedPulse)
            if unstable:
            ## end of added code
                
                UnstableBackgroundCounter +=1
                if Plots and UnstableBackgroundCounter<5:
                    fig, ax = plt.subplots(1,1, figsize=(3, 2))
                    ax.plot(RawPulse)
                    ax.plot(SmoothedPulse)
                    ax.set_title("Baseline Instability")
                    plt.show()
            else:
                AcceptedPulseList.append(RawPulse)
                SmoothedDerivativeList.append(derivative)
                PeakIndexList.append(PeakIndex)
                AcceptedIndices.append(TriggerIndex)
                PulseCounter +=1
                if Plots and PulseCounter<5:
                    fig, (ax1, ax2) = plt.subplots(1,2, figsize=(6, 2))
                    ax1.plot(RawPulse)
                    ax1.plot(SmoothedPulse)
                    ax1.scatter(PeakIndex, SmoothedPulse[PeakIndex], marker="x", color="red", zorder=10)
                    ax1.set_title("Accepted Pulse")
                    ax2.plot(derivative)
                    plt.show()    
                    ##print(PeakProperties)

                    ## start of new code
                    print("Pos properties:", PeakProperties_pos)
                    print("Neg properties:", PeakProperties_neg)
                    ## end of new code
          
    Counters = [BadTriggerCounter, PileupCounter, UnstableBackgroundCounter, PulseCounter]
    CounterNames = ["Data Sets with no Pulse:", "Pulses Rejected for Pileup:", "Pulses Rejected for Baseline Instability:", "Accepted Pulses:"]
    for name, count in zip(CounterNames, Counters): print(name, count)
    if BadTriggerCounter + PileupCounter + UnstableBackgroundCounter + PulseCounter != len(RawData):
        print("Warning: Missing Pulses")
    return AcceptedPulseList, SmoothedDerivativeList, PeakIndexList, AcceptedIndices

