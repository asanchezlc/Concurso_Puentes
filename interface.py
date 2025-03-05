import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk  # Import Pillow for image handling
import os
import serial
import threading
import time

import datetime
import queue
import copy

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
"""

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
time_data = []
data_mass = []
data_deflections = []
pause = False  # Variable to track if data updates are paused
ser = None  # Serial connection

# Create a global Queue to store incoming serial data
data_queue = queue.Queue()

def from_bits_to_deflection(bits):
    """
    Function Duties:
        Converts potentiometer bits to deflection (mm)

    Potentiometer:
        It provides an output electric current ranging from I0 to If;
        I0 corresponds to lengt=0 and If to length=L. It is powered with
        15 V.
        - L: 500 mm
        - I0: 4 mA
        - If: 20 mA

    Electronic circuit (shunt resistor): with arduino we measure voltage
        (not current) so we need to convert it to current using Ohm's Law.
        To do so, we use a resistor which properly scales the current to
        the Arduino voltage range (0-5V); in this case, R=240 so that
        20mA * R = 4.8 V
        - R: 240 Ohm

    Arduino ADC:
        The arduino analog pin has an integrated ADC which converts the
        voltage from 0 to Vcc to a digital value from 0 to 2^n_bits - 1
        - n_bits: 10 (Arduino ADC)
    """
    # Potentiometer characteristics
    L = 500  # mm
    I0 = 4  # mA
    If = 20  # mA

    # Shunt circuit
    R = 240  # Ohm  (used for forming the shunt circuit)

    # ADC (Arduino)
    Vcc = 5  # V
    n_bits = 10  # 10-bit ADC (Arduino ADC)
    bits_max = 2**n_bits - 1  # Maximum value for 10 bits

    # Deflection obtention
    V = bits * Vcc / bits_max  # from bits to voltage
    I = V / R  # Ohm's Law
    deflection = (I * 1000 - I0) / (If - I0) * L  # Linear response; 1000 conversion A -> mA

    return deflection  # mm


def from_bits_to_kg(bits):
    """
    Function Duties:
        Converts the bits measured by the HX711 to kg.

    Load Cell:
        It provides an output voltage ranging from 0 mV to
        Vcc * Sensitivity (= 10 mV)
        - Sensitivity: 2 mV/V
        - Vcc: 5 V
        - Max Load: 1000 kg

    HX711:
        It measures from - sensitivity_hx711 to + sensitivity_hx711
        (e.g. +-20mV); It amplifies this signal by a gain factor. It
        produces an output given in bits from -2^(n_bits-1) to 2^(n_bits-1) - 1
        - n_bits: 24
        - Gain: 128
        - sensitivity_hx711: 20 mV
        - inverted_sign: the connection may be inverted; if so, the sign is inverted
    """
    # Load cell characteristics
    sensitivity = 2  # mV/V (load cell)
    Vcc = 5  # V
    max_load = 1000  # kg

    # HX711
    n_bits = 24  # 24-bit ADC (HX711)
    gain = 128
    sensitivity_hx711 = 20  # mV (+-20mV)
    bits_max = 2**(n_bits-1) - 1  # Maximum positive value for signed 24-bit ADC
    hx711_V_range = gain * sensitivity_hx711 * 0.001  # V (positive and negative values)
    inverted_sign = True

    # Weight obtention
    V = bits * hx711_V_range / bits_max  # amplified measured V
    V = V / gain  # original V (before gain)
    kg = V * 1000 / (sensitivity * Vcc) * max_load  # Load cell has a linear response

    if inverted_sign:
        kg = -kg

    return kg


def from_t_ms_to_s(t_ms):
    """Converts time from ms (from arduinio) to s"""
    return t_ms / 1000


def connect_arduino():
    """Function to establish serial connection"""
    global ser
    try:
        ser = serial.Serial(arduino_port, baud_rate, timeout=1)
        print(f"[INFO] Conectado a {arduino_port}")
        time.sleep(2)  # Wait for Arduino to be ready
    except serial.SerialException:
        print(f"[ERROR] No se pudo abrir el puerto {arduino_port}")
        ser = None  # No active connection


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
                    delta_t, bits_hx711, bits_potentiometer = data.split()
                    # Store data in queue
                    data_queue.put(
                        (int(delta_t), int(bits_hx711), int(bits_potentiometer)))
            except ValueError:
                print("[ERROR] Formato de datos incorrecto:", data)
                continue  # Skip bad data


def update_graph(frame):
    """Function to update the graphs"""
    global time_data, data_mass, data_deflections, pause, last_timestamp

    if pause or ser is None:  # If paused or no serial connection, do not update
        return

    # Retrieve the latest available data from the queue
    if len(time_data) > 0:
        t = time_data[-1]
    else:
        t = 0
    while not data_queue.empty():
        delta_t, bits_hx711, bits_potentiometer = data_queue.get()
        delta_t = from_t_ms_to_s(delta_t)
        mass = from_bits_to_kg(bits_hx711)
        deflection = from_bits_to_deflection(bits_potentiometer)
        t = delta_t + t
        time_data.append(t)
        data_mass.append(mass)
        data_deflections.append(deflection)
    else:
        if len(time_data) > 0:
            # print("[WARNING] No se pudo leer datos, reutilizando último valor.")
            t, mass, deflection = time_data[-1], data_mass[-1], data_deflections[-1]
        else:  # First measurement
            t, mass, deflection = 0, 0, 0  # Default values if no previous data

        time_data.append(t)
        data_mass.append(mass)
        data_deflections.append(deflection)

    n_readings = 200

    # Update first graph
    ax1.clear()
    ax1.plot(time_data[-n_readings:], data_mass[-n_readings:],
             label="Célula de carga", color="blue")
    ax1.set_title("Carga aplicada")
    ax1.set_xlabel("Tiempo (s)")
    ax1.set_ylabel("Masa (kg)")
    ax1.legend(loc="lower left")
    ax1.set_ylim([0, max(data_mass) + 5])

    # Update second graph
    ax2.clear()
    ax2.plot(time_data[-n_readings:], data_deflections[-n_readings:],
             label="Potenciómetro", color="red")
    ax2.set_title("Medida de deformación en centro de vano")
    ax2.set_xlabel("Tiempo (s)")
    ax2.set_ylabel("Flecha (mm)")
    ax2.set_ylim([0, max(data_deflections) + 5])
    ax2.legend(loc="lower left")

    if not (mass is None and deflection is None):
        delta_t = datetime.datetime.now().timestamp() - last_timestamp
        last_timestamp = datetime.datetime.now().timestamp()
        print(
            f"Tiempo: {t:.0f} | Peso (HX711): {mass:.3f} kg | Voltaje (Potenciómetro): {deflection:.3f} mm | Δt: {delta_t:.4f} s")

    fig.tight_layout()


def close_app():
    """Handle GUI closing and KeyboardInterrupt"""
    print("\n[INFO] Closing application...")
    ani.event_source.stop()
    if ser:
        ser.close()
    root.quit()
    root.destroy()


def toggle_pause():
    """Function to toggle pause/display"""
    global pause
    pause = not pause  # Toggle state
    # Change button text
    pause_button.config(text="Display" if pause else "Pause")


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
ani = FuncAnimation(fig, update_graph, interval=refresh_time,
                    cache_frame_data=False)


#


root.protocol("WM_DELETE_WINDOW", close_app)

# Start Arduino reading in a separate thread
threading.Thread(target=read_arduino_data, daemon=True).start()

# Run Tkinter main loop
try:
    root.mainloop()
except KeyboardInterrupt:
    close_app()
