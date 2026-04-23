import numpy as np
import matplotlib.pyplot as plt

def PulseBoundaries(derivative, PeakIndex, window, threshold):
    #Locate pulse boundaries where derivative returns to baseline

    # ---- Find pulse start (scan backwards from peak) ----
    # Start at the peak index and move left (toward index 0)
    # Stop once we reach `window` to avoid invalid slicing.
    for i in range(PeakIndex[0], window, -1):
        # Compute mean derivative in the window immediately to the left
        # of the current index. This smooths noise fluctuations.
        local_mean = np.mean(derivative[i-window:i])
               
        # If derivative has returned close to baseline level,
        # we assume this marks the start of the pulse.
        if local_mean < threshold:
            # Define pulse start as the midpoint of that window.
            # This centers the boundary estimate
            PulseStart = i - window//2
            break
    # If the loop completes without finding a boundary,
    # the `for-else` construct triggers this return.
    else: return None, None

    # ---- Find pulse end (scan forwards from peak) ----
    # Move right from the peak toward the end of the array.
    # Stop early enough so slicing does not exceed array bounds.
    for i in range(PeakIndex[0], len(derivative)-window):
        # Compute mean derivative in the window immediately to the right.
        local_mean = np.mean(derivative[i:i+window])
        # If derivative returns below threshold, pulse tail has ended.
        if local_mean < threshold:
            # Again, choose midpoint of window as boundary.
            PulseEnd = i + window//2
            break
    else: return None, None
    
    # Return detected boundaries
    return PulseStart, PulseEnd

def PulseHeight(PulseData, PulseStart, PulseEnd, OutsideROI=100):
    #Define baseline and top of pulse, i.e. before the pulse rises and after it settles
    Baseline = PulseData[(PulseStart-OutsideROI):PulseStart]
    Top      = PulseData[PulseEnd:(PulseEnd+OutsideROI)]

    #Calculate pulse height (difference between top and baseline levels)
    PH = np.mean(Top) - np.mean(Baseline)   
    
    #Calculate standard error on pulse height
    PH_Err = np.sqrt((np.std(Top)/np.sqrt(len(Top)))**2 + 
                      (np.std(Baseline)/np.sqrt(len(Baseline)))**2)

    return PH, PH_Err, np.mean(Baseline), np.mean(Top)

def RiseTime(PulseData, PeakIndex, PH, Time, window=20):
    PeakIndex=int(PeakIndex)
    
    #Calculate thresholds for 10% and 90% of the pulse height
    h10 = 0.1 * PH
    h90 = 0.9 * PH

    #Initialise crossing times to None in case no crossing is found
    t10 = None
    t90 = None

    # Find 10% crossing:
    # Search backwards from the peak, using a rolling average to smooth noise
    # Crossing time is the midpoint of the window where the threshold is first crossed
    for i in range(PeakIndex, window, -1):
        if np.mean(PulseData[i-window:i]) < h10:
            t10 = Time[i+int(0.5*window)]
            break

    # Find 90% crossing
    # Search forwards from the peak, using a rolling average to smooth noise
    # Crossing time is the midpoint of the window where the threshold is first crossed
    for i in range(PeakIndex, len(PulseData)-window):
        if np.mean(PulseData[i:i+window]) > h90:
            t90 = Time[i+int(0.5*window)]
            break

    #Returns None if either crossing was not found, or if the crossings are in the wrong order
    if t10 is None or t90 is None or t90 <= t10: return None, None, None
    
    #Rise time is the 10%-90% interval scaled to the full 0%-100% amplitude
    #i.e. divide by 0.8 to convert from 10-90% duration to 0-100% equivalent
    RT = (t90 - t10) / 0.8

    return RT, t10, t90

def SinglePulseCharacterisation(RawPulse, SmoothedPulse, SmoothedDerivative, PeakIndex, Time, 
                                 BoundaryWindow, BoundaryThreshold, OutsideROI, PlotNumber, 
                                 RejectCounter=0, PlotCounter=0):
    # Locate the start and end indices of the pulse using the smoothed derivative
    PulseStart, PulseEnd = PulseBoundaries(SmoothedDerivative, PeakIndex, window=BoundaryWindow, threshold=BoundaryThreshold)
    
    # Reject pulse if boundaries could not be found
    if PulseStart is None: 
        # Plot the first five rejected pulses for diagnostics
        if PlotNumber > 0 and RejectCounter < 5:
            print("Pulse boundaries not found")
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3))
            # Show raw and smoothed pulse alongside the derivative used for boundary detection
            ax1.plot(Time, RawPulse)
            ax1.plot(Time, SmoothedPulse)
            ax2.plot(Time, SmoothedDerivative)
            plt.show()
    if PulseStart is None: return None #It crashes if this is in the loop before
    
    # Compute pulse height and its uncertainty from the smoothed pulse
    PH, PH_Err, MeanBaseline, MeanTop = PulseHeight(SmoothedPulse, PulseStart, PulseEnd, OutsideROI=OutsideROI)
    # Reject pulse if height is non-positive (e.g. noise or inverted pulse)
    if PH <= 0: return None
    
    # Subtract baseline so the pulse starts from zero, as required by RiseTime
    CorrectedPulse = SmoothedPulse - MeanBaseline
    # Extract rise time and the times at which the 10% and 90% thresholds are crossed
    RT, t10, t90 = RiseTime(CorrectedPulse, PeakIndex, PH, Time)
    
    # Reject pulse if rise time extraction failed (e.g. thresholds not crossed)
    if RT is None:         
        # Plot the first few failed pulses for diagnostics
        if PlotNumber > 0 and RejectCounter < 5:
            print("Rise time extraction failed")
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(Time, CorrectedPulse)
            plt.show()
    if RT is None: return None #It crashes if this is in the loop before
    
    # Plot accepted pulses up to the requested PlotNumber limit
    if PlotNumber > 0 and PlotCounter < PlotNumber:
        fig, ax = plt.subplots(1, 1, figsize=(5, 3))
        ax.plot(Time, RawPulse, linewidth=0.5)
        ax.plot(Time, SmoothedPulse, linewidth=0.5)
        # Mark the peak location
        ax.scatter(Time[PeakIndex], SmoothedPulse[PeakIndex], color="black", marker="x", zorder=10)
        # Shade the baseline regions on either side of the pulse used for averaging
        ax.fill_between((Time[PulseStart-OutsideROI], Time[PulseStart]), (MeanTop, MeanTop), color="grey", alpha=0.5, linewidth=0)
        ax.fill_between((Time[PulseEnd],   Time[PulseEnd+OutsideROI]),   (MeanTop, MeanTop), color="grey", alpha=0.5, linewidth=0)
        ax.set_title(f"Pulse Height = {PH:.2f}, Rise Time = {RT:.2f} µs")
        # Horizontal lines marking the baseline and top levels
        ax.axhline(MeanBaseline, color="blue")
        ax.axhline(MeanTop,      color="blue")
        # Dotted lines marking the 10% and 90% rise time thresholds
        ax.axhline(0.1*PH, linestyle=":", color="blue")
        ax.axhline(0.9*PH, linestyle=":", color="blue")
        # Vertical lines marking the times at which the 10% and 90% thresholds are crossed
        ax.axvline(t10, color="red")
        ax.axvline(t90, color="red")
        ax.set_xlim(Time[PulseStart-OutsideROI], Time[PulseEnd+OutsideROI])
        plt.suptitle("Accepted Pulse")
        plt.tight_layout()
        plt.show()
    
    return PH, RT, PH_Err

def AlphaPulsePeakCharacterisation(ValidPulsesRaw, ValidPulsesSmoothed, SmoothedDerivatives, PeakIndices, Time_microsec, BoundaryWindow=10, BoundaryThreshold=0.05, OutsideROI=100, PlotNumber=0):
    # Initialise lists to collect results across all pulses
    AcceptedIndices = []
    RiseTimes = []
    PulseHeights = []
    PulseHeightErrors = []
    # Track how many pulses have been plotted and rejected
    PlotCounter = 0
    RejectCounter = 0
    
    # Iterate over each pulse, pairing raw, smoothed, derivative and peak index
    for raw, smooth, deriv, pk in zip(ValidPulsesRaw, ValidPulsesSmoothed, SmoothedDerivatives, PeakIndices):
        # Characterise the pulse, returning None if it fails any quality checks
        result = SinglePulseCharacterisation(raw, smooth, deriv, pk, Time_microsec, RejectCounter=RejectCounter, PlotCounter=PlotCounter, BoundaryWindow=BoundaryWindow, BoundaryThreshold=BoundaryThreshold, OutsideROI=OutsideROI, PlotNumber=PlotNumber)
        
        if result is None: 
            RejectCounter += 1
        else:
            # Increment plot counter for each accepted pulse
            PlotCounter += 1 

            AcceptedIndices.append(PlotCounter)  # index into ValidPulsesRaw
            
            # Unpack results and store
            rise, height, err = result
            RiseTimes.append(rise)
            PulseHeights.append(height)
            PulseHeightErrors.append(err)
    
    print("Number of Pulses Provided: "+str(len(ValidPulsesRaw)))
    print("Number of Rejected Pulses: "+str(RejectCounter))
    print("Number of Usable Pulses: "+str(len(RiseTimes)))
    if len(RiseTimes) != len(ValidPulsesRaw)-RejectCounter: print("Warning: Missing Pulses")
    # Return results as numpy arrays for downstream analysis
    return (np.array(RiseTimes), np.array(PulseHeights), RejectCounter, np.array(PulseHeightErrors), np.array(AcceptedIndices))