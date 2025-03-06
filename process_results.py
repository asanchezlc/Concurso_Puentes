
import json
import os
import matplotlib.pyplot as plt
import helpers.outils as outils

folder = "data"

file = os.listdir(folder)[-1]

with open(os.path.join(folder, file)) as f:
    data = json.load(f)

time_raw = data['time']
raw_mass = data['raw_mass']
raw_deflection = data['raw_deflection']
processed_mass = data['processed_mass']
processed_deflection = data['processed_deflection']

# Filter mass peaks
threshold_mass_peaks = 50
time, processed_mass, processed_deflection = time_raw[1:], processed_mass[1:], processed_deflection[1:]
valid_indices = outils.manual_find_peaks(processed_mass, threshold_mass_peaks)
time = [time[i] for i in valid_indices]
processed_mass = [processed_mass[i] for i in valid_indices]
processed_deflection = [processed_deflection[i] for i in valid_indices]

fig, ax = plt.subplots()

ax.plot(time_raw, raw_mass, label='raw_mass')
ax.plot(time_raw, raw_deflection, label='raw_deflection')
ax.legend()

fig, ax = plt.subplots()

ax.plot(time, processed_mass, label='processed_mass')
ax.plot(time, processed_deflection, label='processed_deflection')
ax.legend()
