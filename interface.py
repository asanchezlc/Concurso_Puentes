import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk  # Import Pillow for image handling
import os
import serial
import json
import threading
import time

import datetime
import queue
import copy

import helpers.outils as outils
"""
File Duties:

1. Connect to Arduino and read data from serial port.

In this case, data from 2 sensors is read; the arduino code is Potentiometer.ino
located in:
DOCTORADO_CODES -> ARDUINO -> Potentiometer -> Potentiometer

The data read is the following:
- Delta Time (ms): Time elapsed since last reading
- HX711 Value (bits)
- Voltage (V)

2. Update the graphs with the latest data.


IMPORTANT NOTES ABOUT CODE ARCHITECTURE:
    - The data acquisition is done in a separate thread to avoid blocking the GUI.
    - The data is stored in a queue to ensure thread safety and fast plot updating.
    - The variables raw_time, raw_mass, and raw_deflection are global and updated
      by the process_data function.

"""

def update_mass_deflection_graph(frame, fig, ax1, ax2, data_queue, raw_time, raw_mass,
                 raw_deflection, processed_mass, processed_deflection, zero_mass, zero_deflection, pause, callibration):
    """
    Function Duties:
        Updates the mass and deflection graph (which is a single figure with 2 axes)
        full list of values raw_time, raw_mass, raw_deflection
    Inputs:
        - frame: Required for FuncAnimation (unused inside the function)
        - fig: The Matplotlib figure object to update
        - ax1: First subplot (Mass vs Time)
        - ax2: Second subplot (Deflection vs Time)
        - raw_time: List storing time values
        - raw_mass: List storing mass readings
        - raw_deflection: List storing deflection readings
        - pause: Boolean indicating whether updates are paused
        - n_readings: Number of readings to display
    """
    # n_readings = 200
    if pause:
        return  # If paused, do not update

    process_data(data_queue, raw_time, raw_mass, raw_deflection, processed_mass,
                 processed_deflection)

    if len(callibration_dict) > 0:
        i = list(callibration_dict.keys())[-1]
        idx_ini = callibration_dict[i]["raw_processed_data"]["idx_ini"]
    else:
        idx_ini = 0
    # idx_ini += 1

    # Update first graph
    ax1.clear()
    ax1.plot(raw_time[idx_ini:], processed_mass[idx_ini:], label="Célula de carga", color="blue")
    # ax1.plot(raw_time[-n_readings:], processed_mass[-n_readings:], label="Célula de carga", color="blue")
    ax1.set_title("Carga Aplicada")
    ax1.set_xlabel("Tiempo (s)")
    ax1.set_ylabel("Masa (kg)")
    ax1.legend(loc="lower left")
    ax1.set_ylim([min(processed_mass[idx_ini:])-2, max(processed_mass[idx_ini:]) + 50])

    # Update second graph
    ax2.clear()
    ax2.plot(raw_time[idx_ini:], processed_deflection[idx_ini:], label="Potenciómetro", color="red")
    # ax2.plot(raw_time[-n_readings:], processed_deflection[-n_readings:], label="Potenciómetro", color="red")
    ax2.set_title("Flecha en Centro de Vano")
    ax2.set_xlabel("Tiempo (s)")
    ax2.set_ylabel("Flecha (mm)")
    ax2.set_ylim([min(processed_deflection[idx_ini:])-5, max(processed_deflection[idx_ini:]) + 5])
    ax2.legend(loc="lower left")

    print(f"Time: {raw_time[-1]:.2f} s | Raw mass: {raw_mass[-1]:.3f} kg | Raw Deflection: {raw_deflection[-1]:.3f} mm | Processed Mass: {processed_mass[-1]:.3f} kg | Processed Deflection: {processed_deflection[-1]:.3f} mm")

    fig.tight_layout()  # Adjust layout for clarity


def update_stiffness_graph(frame, fig, ax, data_queue, raw_time, raw_mass,
                           raw_deflection, processed_mass, processed_deflection, zero_mass, zero_deflection,
                           pause, callibration):
    """
    Function Duties:
        Updates the mass and deflection graph (which is a single figure with 2 axes)
        full list of values raw_time, raw_mass, raw_deflection
    Inputs:
        - frame: Required for FuncAnimation (unused inside the function)
        - fig: The Matplotlib figure object to update
        - ax1: First subplot (Mass vs Time)
        - ax2: Second subplot (Deflection vs Time)
        - raw_time: List storing time values
        - raw_mass: List storing mass readings
        - raw_deflection: List storing deflection readings
        - pause: Boolean indicating whether updates are paused
        - n_readings: Number of readings to display
    """
    # n_readings = 200
    if pause:
        return  # If paused, do not update

    process_data(data_queue, raw_time, raw_mass, raw_deflection, processed_mass,
                 processed_deflection)

    if len(callibration_dict) > 0:
        i = list(callibration_dict.keys())[-1]
        idx_ini = callibration_dict[i]["raw_processed_data"]["idx_ini"]
    else:
        idx_ini = 0
    # idx_ini += 1
    # stiffness = [m/d if d != 0 else 0 for m, d in zip(processed_mass, processed_deflection)]

    # Update first graph
    ax.clear()
    ax.scatter(processed_deflection[idx_ini:], processed_mass[idx_ini:], label="Rigidez", color="black")
    ax.set_title(f"Flecha vs Carga; Máx. Carga: {format(max(processed_mass[1:]), '.2f')}kg; Máx. Flecha: {format(max(processed_deflection[1:]), '.2f')}mm")
    ax.set_xlabel("Flecha (mm)")
    ax.set_ylabel("Carga (kg)")
    ax.legend(loc="lower right")
    x_inf = 0
    x_max = max(processed_deflection[idx_ini:] + [100])
    y_inf = 0
    y_max = max(processed_mass[idx_ini:] + [500])
    ax.set_xlim([x_inf, x_max])
    ax.set_ylim([y_inf, y_max])
    # ax.set_ylim([-1, max(stiffness) + 5])

    fig.tight_layout()  # Adjust layout for clarity



def process_data(data_queue, raw_time, raw_mass, raw_deflection,
                 processed_mass, processed_deflection) -> None:
    """
    Function Duties:
        Retrieves and processes the latest available data from the queue.
    Inputs:
        - data_queue: Queue storing incoming sensor data
        - raw_time: List storing time values
        - raw_mass: List storing mass readings
        - raw_deflection: List storing deflection readings
    Output:
        None
        They are global variables that get updated, no need to return them
    """
    global zero_mass, zero_deflection, callibration, callibration_time
    latest_t = raw_time[-1] if raw_time else 0  # Last time value or 0 if empty
    queue_time, queue_mass, queue_deflection = [], [], []

    while not data_queue.empty():
        delta_t, bits_hx711, bits_potentiometer = data_queue.get()
        delta_t = outils.from_t_ms_to_s(delta_t)
        mass = outils.from_bits_to_kg(bits_hx711)
        deflection = outils.from_bits_to_deflection(bits_potentiometer)
        latest_t += delta_t
        queue_time.append(latest_t)
        queue_mass.append(mass)
        queue_deflection.append(deflection)
    with lock:  # Avoid problems with different threads managing the same variables
        raw_time += queue_time
        raw_mass += queue_mass
        raw_deflection += queue_deflection
        processed_mass += [m - zero_mass for m in queue_mass]
        processed_deflection += [d - zero_deflection for d in queue_deflection]
    if callibration:
        zero_mass = sum(queue_mass) / len(queue_mass)
        zero_deflection = sum(queue_deflection) / len(queue_deflection)
        callibration_time = queue_time[-1] - queue_time[0]
        callibration = False

    
    # else:
    #     if len(raw_time) > 0:
    #         # print("[WARNING] No se pudo leer datos, reutilizando último valor.")
    #         t, mass, deflection = raw_time[-1], raw_mass[-1], raw_deflection[-1]
    #     else:  # First measurement
    #         t, mass, deflection = 0, 0, 0  # Default values if no previous data

    #     raw_time.append(t)
    #     raw_mass.append(mass)
    #     raw_deflection.append(deflection)


def close_app(ser):
    """
    Function Duties:
        Handle GUI closing and KeyboardInterrupt
    Input:
        ser: Serial object (from outils.connect_arduino)
    """
    print("\n[INFO] Closing application...")

    # Stop Matplotlib animation (check if ani_1 exists)
    if 'ani_1' in globals():
        ani_1.event_source.stop()

    # Close Serial Connection
    if ser is not None and ser.is_open:
        print("[INFO] Closing serial connection...")
        ser.close()

    # # Clear the queue
    # with data_queue.mutex:
    #     data_queue.queue.clear()

    root.quit()
    root.destroy()


def toggle_pause(pause):
    """
    Function Duties:
        Function to toggle pause/display
    Input:
        pause: boolean to toggle pause
    """
    pause = not pause  # Toggle state
    # Change button text
    pause_button.config(text="Display" if pause else "Pause")
    return pause


def update_pause_state():
    global pause
    pause = toggle_pause(pause)  # Store updated value


def toggle_measurement():
    """
    Function Duties:
        Toggles between "Start Measurement" and "Stop Measurement" states.
        Also triggers calibration when first started.
    """
    global measurement_running, zero_mass, zero_deflection, pause, callibration
    measurement_running = not measurement_running  # Toggle state
    if measurement_running:
        pause = True
        callibration = True
    if callibration:
        start_button.config(text="Please Wait...  ", style="Danger.TButton")  # Change button appearance
        root.update_idletasks()
        callibrate_mass_deflection(raw_time, raw_mass, raw_deflection, zero_mass, zero_deflection)

    if measurement_running:
        print("[INFO] Measurement started.")
        start_button.config(text="Stop Measurement", style="Danger.TButton")  # Change button appearance
    else:
        print("[INFO] Measurement stopped.")
        start_button.config(text="Start Measurement", style="Primary.TButton")  # Reset button
        save_data_to_file(callibration_dict)


def save_backup_data_thread(callibration_dict):
    global raw_time, raw_mass, raw_deflection, processed_mass, processed_deflection, measurement_running

    while True:
        if measurement_running:
            time.sleep(10)  # Save data every 10 seconds
            folder = os.path.join("data", "backup")
            os.makedirs(folder, exist_ok=True)

            i = list(callibration_dict.keys())[-1]
            idx_ini = callibration_dict[i]["raw_processed_data"]["idx_ini"]

            data_dict = {
                "time": raw_time[idx_ini:],
                "raw_mass": raw_mass[idx_ini:],
                "raw_deflection": raw_deflection[idx_ini:],
                "processed_mass": processed_mass[idx_ini:],
                "processed_deflection": processed_deflection[idx_ini:],
                "callibration": callibration_dict
            }

            # Save data to a JSON file
            file_name = f"data_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
            with open(os.path.join(folder, file_name), "w") as f:
                json.dump(data_dict, f, indent=4)
        else:
            time.sleep(0.2)


def save_data_to_file(callibration_dict):
    global raw_time, raw_mass, raw_deflection, processed_mass, processed_deflection

    folder = os.path.join("data")
    os.makedirs(folder, exist_ok=True)

    i = list(callibration_dict.keys())[-1]
    idx_ini = callibration_dict[i]["raw_processed_data"]["idx_ini"]

    data_dict = {
        "time": raw_time[idx_ini:],
        "raw_mass": raw_mass[idx_ini:],
        "raw_deflection": raw_deflection[idx_ini:],
        "processed_mass": processed_mass[idx_ini:],
        "processed_deflection": processed_deflection[idx_ini:],
        "callibration": callibration_dict
    }

    # Save data to a JSON file
    file_name = f"data_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    with open(os.path.join(folder, file_name), "w") as f:
        json.dump(data_dict, f, indent=4)


# def start_measurement(raw_time, raw_mass, raw_deflection):


def callibrate_mass_deflection(raw_time, raw_mass, raw_deflection, zero_mass, zero_deflection):
    global pause, callibration, callibration_time

    callibration_time = 5  # seconds
    callibration = True
    pause = True
    print(f"[INFO] Iniciando medición en {callibration_time} segundos...")
    idx_ini = len(raw_time) - 1
    t_ini = raw_time[idx_ini]
    time.sleep(callibration_time)
    process_data(data_queue, raw_time, raw_mass, raw_deflection,
                 processed_mass, processed_deflection)
    t_end = t_ini + callibration_time  # callibration_time is updated in process_data
    callibration = False
    pause = False

    # Save data in a callibration dictionary
    idx_callibration_start = len(raw_time) - 1
    i = list(callibration_dict.keys())[-1] + \
        1 if len(callibration_dict) > 0 else 0
    callibration_dict[i] = {"callibration":
                            {"t_ini_callibration": t_ini,
                             "t_end_callibration": t_end,
                             "zero_mass": zero_mass,
                             "zero_deflection": zero_deflection},
                            "raw_processed_data":
                                {"time": raw_time[idx_callibration_start],
                                 "idx_ini": idx_callibration_start}
                            }



# -----------------------------------------------------------------------------

# MAIN
# Variables for GUI configuration
refresh_time = 1000  # ms [same as Arduino readings]
GUI_title = "Fase Provincial - II Concurso Nacional de Puentes Agustín de Betancourt - ETSICCP GRANADA"
logo_folder = "logos"
logo_ugr_name = "ugr.png"
logo_etsiccp_name = "etsiccp.png"
logo_grupo_puentes_name = "grupo_puentes.png"
arduino_port = "COM12"
baud_rate = 9600

# Sensor Data
raw_time, raw_mass, raw_deflection = [0], [0], [0]  # Starting values
processed_time, processed_mass, processed_deflection = [0], [0], [0]  # Starting values
zero_time, zero_mass, zero_deflection = 0, 0, 0  # Null values for callibration
pause = False  # Variable to track if data updates are paused
callibration = False
callibration_dict = {}
measurement_running = False
ser = None  # Serial connection

# Create a global Queue to store incoming serial data
simulated = True
if simulated:
    lock = threading.Lock()
    data_queue = queue.Queue()
    threading.Thread(target=outils.simulated_data_thread, args=(data_queue,), daemon=True).start()
    threading.Thread(target=save_backup_data_thread, args=(callibration_dict,), daemon=True).start()
else:
    ser = outils.connect_arduino(arduino_port, baud_rate)
    run_arduino_thread = False
    if ser is None or not ser.is_open:  # Check connection before starting thread
        print("[WARNING] No active serial connection. Attempting to reconnect...")
        ser = outils.connect_arduino(arduino_port, baud_rate)
        if ser is None:
            print("[ERROR] Unable to establish connection. Data thread will NOT start.")
        else:
            run_arduino_thread = True
    else:
        run_arduino_thread = True

    if run_arduino_thread:
        lock = threading.Lock()  # it avoids problems with different threads managing the same variables
        data_queue = queue.Queue()
        threading.Thread(target=outils.read_arduino_data_thread, args=(ser, data_queue), daemon=True).start()
        threading.Thread(target=save_backup_data_thread, args=(callibration_dict,), daemon=True).start()


# Tkinter GUI Setup
root = tk.Tk()
root.title("Arduino Sensor Data Viewer")
root.state('zoomed')  # Start maximized

# Configure grid system
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

# 1. HEADER (Title + Logos)
header_container = tk.Frame(root)
header_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

logo_frame_left = tk.Frame(header_container)
logo_frame_left.pack(side=tk.LEFT, anchor=tk.N)
title_frame = tk.Frame(header_container)
title_frame.pack(side=tk.LEFT, expand=True)
logo_frame_right = tk.Frame(header_container)
logo_frame_right.pack(side=tk.RIGHT, anchor=tk.N)

title_label = ttk.Label(
    title_frame,
    text=GUI_title,
    font=("Arial", 18, "bold")
)
title_label.pack(pady=10)

# Set the logos as tkt images
logo_ugr_path = os.path.join(logo_folder, logo_ugr_name)
logo_etsiccp_path = os.path.join(logo_folder, logo_etsiccp_name)
logo_grupo_puentes_path = os.path.join(logo_folder, logo_grupo_puentes_name)

try:
    logo_ugr_img = Image.open(logo_ugr_path).resize(
        (70, 70), Image.Resampling.LANCZOS)
    logo_ugr_tk = ImageTk.PhotoImage(logo_ugr_img)
    logo_etsiccp_img = Image.open(logo_etsiccp_path).resize(
        (70, 70), Image.Resampling.LANCZOS)
    logo_etsiccp_tk = ImageTk.PhotoImage(logo_etsiccp_img)
    logo_grupo_puentes_img = Image.open(logo_grupo_puentes_path).resize(
        (70, 70), Image.Resampling.LANCZOS)
    logo_grupo_puentes_tk = ImageTk.PhotoImage(logo_grupo_puentes_img)

    # Add left-side logos
    logo_ugr_label = tk.Label(logo_frame_left, image=logo_ugr_tk)
    logo_ugr_label.pack(side=tk.LEFT, padx=5)
    logo_etsiccp_label = tk.Label(logo_frame_left, image=logo_etsiccp_tk)
    logo_etsiccp_label.pack(side=tk.LEFT, padx=5)

    # Add right-side logos
    logo_grupo_puentes_label = tk.Label(
        logo_frame_right, image=logo_grupo_puentes_tk)
    logo_grupo_puentes_label.pack(side=tk.LEFT, padx=5)
except:
    print("[ERROR] No se pudo cargar una o más imágenes de los logos.")

# # 2. MAIN GRAPHS (Matplotlib)
# fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 6))
# canvas = FigureCanvasTkAgg(fig, master=root)
# canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")

# MAIN CONTAINER (Splitting Left & Right Sections)
main_container = tk.Frame(root)
main_container.grid(row=1, column=0, sticky="nsew")
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

# LEFT SIDE: Original 2 Subplots (Mass & Deflection)
fig_left, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
canvas_left = FigureCanvasTkAgg(fig_left, master=main_container)
canvas_left.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

# RIGHT SIDE: Now Divided into 2 Sections (Text + Stiffness Plot)
right_container = tk.Frame(main_container)
right_container.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

# RIGHT-TOP: Small Text Area
text_frame = tk.Frame(right_container, height=50, bg="lightgray")
text_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=0)
text_frame.grid_propagate(False)  # Prevent resizing
text_label = ttk.Label(text_frame, text="Measurement Info", font=("Arial", 14, "bold"))
text_label.pack(expand=True)

# RIGHT-BOTTOM: Stiffness Plot (Larger Area)
fig_right, ax3 = plt.subplots(figsize=(8, 4))  # Single plot on the right
canvas_right = FigureCanvasTkAgg(fig_right, master=right_container)
canvas_right.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=5, pady=0)

# Make Right Side Expand Properly (More Height for Plot)
right_container.grid_rowconfigure(0, weight=2)  # Text area (small)
right_container.grid_rowconfigure(1, weight=4)  # Plot area (larger)
right_container.grid_columnconfigure(0, weight=1)

# Make Both Sides Expand Properly
main_container.grid_columnconfigure(0, weight=1)  # Left plot
main_container.grid_columnconfigure(1, weight=1)  # Right section
main_container.grid_rowconfigure(0, weight=1)



# 3. BOTTOM BUTTONS (Start Measurement & Pause Button)
bottom_container = tk.Frame(root)
bottom_container.grid(row=2, column=0, sticky="sew", padx=10, pady=5)
root.grid_rowconfigure(2, weight=0)

# Start/Stop Measurement Button (Left Side)
start_button = ttk.Button(bottom_container, text="Start Measurement", command=toggle_measurement, style="Primary.TButton")
start_button.pack(side=tk.LEFT, padx=10)

# Pause Button (Right Side)
pause_button = ttk.Button(
    bottom_container,
    text="Pause",
    command=lambda: update_pause_state()
)
pause_button.pack(side=tk.RIGHT, padx=10)

# Run Matplotlib animation
ani_1 = FuncAnimation(
    fig_left,
    lambda frame: update_mass_deflection_graph(frame, fig_left, ax1, ax2, data_queue, raw_time, raw_mass,
                                               raw_deflection, processed_mass, processed_deflection, zero_mass, zero_deflection, pause, callibration),
    interval=refresh_time,
    cache_frame_data=False
)
ani_2 = FuncAnimation(
    fig_right,
    lambda frame2: update_stiffness_graph(frame2, fig_right, ax3, data_queue, raw_time, raw_mass,
                                          raw_deflection, processed_mass, processed_deflection, zero_mass, zero_deflection, pause, callibration),
    interval=refresh_time,
    cache_frame_data=False
)

root.protocol("WM_DELETE_WINDOW", lambda: close_app(ser))
# Run Tkinter main loop
try:
    root.mainloop()
except KeyboardInterrupt:
    close_app(ser)
