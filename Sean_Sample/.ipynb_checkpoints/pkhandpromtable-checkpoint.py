# generate table for values for peak height and peak prominence from 0.1 to 0.9 in steps of 0.1

import numpy as np
import pandas as pd
from itertools import product
import io
import sys
import re

param_values = np.round(np.arange(0.1, 1.0, 0.1), 1)
results = {}

for PkProminence, PkHeight in product(param_values, param_values):
    # Capture printed output
    captured = io.StringIO()
    sys.stdout = captured
    
    AcceptedPulseList, SmoothedDerivativeList, PeakIndexList = PulseID.PeakAcceptance(
        CorrectedPulses, SmoothedPulses,
        PkProminence=PkProminence,
        PkHeight=PkHeight,
        Plots=False
    )
    
    sys.stdout = sys.__stdout__  # Restore normal printing
    output = captured.getvalue()
    
    # Parse the printed numbers
    def extract(pattern):
        m = re.search(pattern, output)
        return int(m.group(1)) if m else None

    results[(PkProminence, PkHeight)] = {
        'No Pulse':             extract(r'no Pulse:\s*(\d+)'),
        'Pileup':               extract(r'Pileup:\s*(\d+)'),
        'Baseline Instability': extract(r'Baseline Instability:\s*(\d+)'),
        'Accepted':             extract(r'Accepted Pulses:\s*(\d+)')
    }

# Print 2D tables
categories = ['No Pulse', 'Pileup', 'Baseline Instability', 'Accepted']

for cat in categories:
    table = pd.DataFrame(
        index=[f'Prom={p}' for p in param_values],
        columns=[f'Height={h}' for h in param_values]
    )
    for PkProminence, PkHeight in product(param_values, param_values):
        table.loc[f'Prom={PkProminence}', f'Height={PkHeight}'] = results[(PkProminence, PkHeight)][cat]
    
    print(f'\n--- {cat} ---')
    print(table.to_string())