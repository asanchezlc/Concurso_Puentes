
import json
import os
import matplotlib.pyplot as plt

folder = "data"

file = os.listdir(folder)[-1]

with open(os.path.join(folder, file)) as f:
    data = json.load(f)

time = data['time']
raw_mass = data['raw_mass']
raw_deflection = data['raw_deflection']
processed_mass = data['processed_mass']
processed_deflection = data['processed_deflection']

print('h')

fig, ax = plt.subplots()

ax.plot(time, raw_deflection, label='raw_mass')
ax.plot(time, processed_deflection, label='processed_deflection')
ax.legend()

fig, ax = plt.subplots()

ax.plot(time, raw_mass, label='raw_mass')
ax.plot(time, processed_mass, label='processed_mass')
ax.legend()
