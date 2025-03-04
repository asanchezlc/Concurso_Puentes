import tkinter as tk
from tkinter import ttk
import random
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk  # Import Pillow for image handling
import os
import serial
import threading
import time
import numpy as np
import datetime
import queue

# Variables for GUI configuration
refresh_time = 1000  # ms [same as Arduino readings]
GUI_title = "Fase Provincial - II Concurso Nacional de Puentes Agustín de Betancourt - ETSICCP GRANADA"
logo_folder = "logos"
logo_ugr_name = "ugr.png"
logo_etsiccp_name = "etsiccp.png"
logo_grupo_puentes_name = "grupo_puentes.png"
arduino_port = "COM7"
baud_rate = 9600

# Sensor Data
time_data = []
sensor_data_1 = []
sensor_data_2 = []
pause = False  # Variable to track if data updates are paused
ser = None  # Serial connection

# Create a global Queue to store incoming serial data
data_queue = queue.Queue()

# Function to establish serial connection
def connect_arduino():
    global ser
    try:
        ser = serial.Serial(arduino_port, baud_rate, timeout=1)
        print(f"[INFO] Conectado a {arduino_port}")
        time.sleep(2)  # Wait for Arduino to be ready
    except serial.SerialException:
        print(f"[ERROR] No se pudo abrir el puerto {arduino_port}")
        ser = None  # No active connection

# Function to read real sensor data from Arduino
def read_arduino_data():
    """Continuously reads data from Arduino and stores it in a queue."""
    global ser

    while True:
        if ser is None or not ser.is_open:
            print("[WARNING] Conexión perdida. Intentando reconectar...")
            connect_arduino()
            time.sleep(1)
            continue  # Retry connection

        if ser.in_waiting > 0:  # Check if data is available
            try:
                data = ser.readline().decode('utf-8').strip()
                if data:
                    delta_t, hx711_value, voltage = data.split()
                    data_queue.put((int(delta_t), int(hx711_value), float(voltage)))  # Store data in queue
            except ValueError:
                print("[ERROR] Formato de datos incorrecto:", data)
                continue  # Skip bad data

# Function to update the graphs
def update_graph(frame):
    global time_data, sensor_data_1, sensor_data_2, pause, last_timestamp

    if pause or ser is None:  # If paused or no serial connection, do not update
        return

    # Retrieve the latest available data from the queue
    if len(time_data) > 0:
        t = time_data[-1]
    else:
        t = 0
    while not data_queue.empty():
        delta_t, hx711_value, voltage = data_queue.get()
        t = delta_t + t
        time_data.append(t)
        sensor_data_1.append(hx711_value)
        sensor_data_2.append(voltage)
    else:
        print("[WARNING] No se pudo leer datos, reutilizando último valor.")
        if len(time_data) > 0:
            t, hx711_value, voltage = time_data[-1], sensor_data_1[-1], sensor_data_2[-1]
        else:
            t, hx711_value, voltage = 0, 0, 0  # Default values if no previous data

        if t is not None and hx711_value is not None and voltage is not None:
            time_data.append(t)
            sensor_data_1.append(hx711_value)
            sensor_data_2.append(voltage)

    n_readings = 100

    # Update first graph
    ax1.clear()
    ax1.plot(time_data[-n_readings:], sensor_data_1[-n_readings:], label="Célula de carga", color="blue")
    ax1.set_title("Carga aplicada")
    ax1.set_xlabel("Tiempo (s)")
    ax1.set_ylabel("BITS (kg)")
    ax1.legend(loc="lower left")

    # Update second graph
    ax2.clear()
    ax2.plot(time_data[-n_readings:], sensor_data_2[-n_readings:], label="Potenciómetro", color="red")
    ax2.set_title("Medida de deformación en centro de vano")
    ax2.set_xlabel("Tiempo (s)")
    ax2.set_ylabel("VOLTAJE (mm)")
    ax2.legend(loc="lower left")

    if not (voltage is None and hx711_value is None):
        delta_t = datetime.datetime.now().timestamp() - last_timestamp
        last_timestamp = datetime.datetime.now().timestamp()
        print(f"Tiempo: {delta_t} | Peso (HX711): {hx711_value} | Voltaje (Potenciómetro): {voltage:.2f} V | Δt: {delta_t:.2f} s")

    fig.tight_layout()

# Function to toggle pause/display
def toggle_pause():
    global pause
    pause = not pause  # Toggle state
    pause_button.config(text="Display" if pause else "Pause")  # Change button text

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
    logo_ugr_img = Image.open(logo_ugr_path).resize((70, 70), Image.Resampling.LANCZOS)
    logo_ugr_tk = ImageTk.PhotoImage(logo_ugr_img)
    logo_etsiccp_img = Image.open(logo_etsiccp_path).resize((70, 70), Image.Resampling.LANCZOS)
    logo_etsiccp_tk = ImageTk.PhotoImage(logo_etsiccp_img)
    logo_grupo_puentes_img = Image.open(logo_grupo_puentes_path).resize((70, 70), Image.Resampling.LANCZOS)
    logo_grupo_puentes_tk = ImageTk.PhotoImage(logo_grupo_puentes_img)

    # Add left-side logos
    logo_ugr_label = tk.Label(logo_frame_left, image=logo_ugr_tk)
    logo_ugr_label.pack(side=tk.LEFT, padx=5)
    logo_etsiccp_label = tk.Label(logo_frame_left, image=logo_etsiccp_tk)
    logo_etsiccp_label.pack(side=tk.LEFT, padx=5)

    # Add right-side logos
    logo_grupo_puentes_label = tk.Label(logo_frame_right, image=logo_grupo_puentes_tk)
    logo_grupo_puentes_label.pack(side=tk.LEFT, padx=5)
except:
    print("[ERROR] No se pudo cargar una o más imágenes de los logos.")

# 2. MAIN GRAPHS (Matplotlib)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 6))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")

# 3. BOTTOM BUTTON (Pause Button)
bottom_container = tk.Frame(root)
bottom_container.grid(row=2, column=0, sticky="sew", padx=10, pady=5)
root.grid_rowconfigure(2, weight=0)

pause_button = ttk.Button(bottom_container, text="Pause", command=toggle_pause)
pause_button.pack(side=tk.RIGHT, padx=10)

# Run Matplotlib animation
last_time = datetime.datetime.now()
last_timestamp = last_time.timestamp()  # Convert to timestamp
ani = FuncAnimation(fig, update_graph, interval=refresh_time, cache_frame_data=False)

# Handle GUI closing and KeyboardInterrupt
def close_app():
    print("\n[INFO] Closing application...")
    ani.event_source.stop()
    if ser:
        ser.close()
    root.quit()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close_app)

# Start Arduino reading in a separate thread
threading.Thread(target=read_arduino_data, daemon=True).start()

# Run Tkinter main loop
try:
    root.mainloop()
except KeyboardInterrupt:
    close_app()
