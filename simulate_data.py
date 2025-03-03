import csv
import time
import random

# Simulated sensor data file
filename = "simulated_sensor_data.csv"

# Define the number of sensors
NUM_SENSORS = 3  # Adjust this based on your needs

# Define the time interval between data recordings (in seconds)
TIME_INTERVAL = 1.0  

# Function to generate simulated sensor data
def generate_sensor_data():
    return [round(random.uniform(20, 30), 2) for _ in range(NUM_SENSORS)]  # Simulating temperature-like data

# Create the CSV file and write the header
with open(filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp"] + [f"Sensor_{i+1}" for i in range(NUM_SENSORS)])  # Column headers

print(f"Simulated Arduino sensor data recording started... (Writing to {filename})")

# Continuously write data to the file
try:
    while True:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        sensor_data = generate_sensor_data()
        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp] + sensor_data)
        print(f"Recorded: {timestamp}, Data: {sensor_data}")
        time.sleep(TIME_INTERVAL)  # Simulating the delay between readings
except KeyboardInterrupt:
    print("\nSimulation stopped by user.")
