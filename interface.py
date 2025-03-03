import tkinter as tk
from tkinter import ttk
import random
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk  # Import Pillow for image handling

# Simulated Sensor Data
sensor_data_1 = []
sensor_data_2 = []

# Function to simulate sensor readings
def generate_sensor_data():
    return round(random.uniform(20, 30), 2)

# Function to update the graphs
def update_graph(frame):
    global sensor_data_1, sensor_data_2

    # Append new simulated data
    sensor_data_1.append(generate_sensor_data())
    sensor_data_2.append(generate_sensor_data())

    # Limit to last 100 readings
    if len(sensor_data_1) > 100:
        sensor_data_1.pop(0)
    if len(sensor_data_2) > 100:
        sensor_data_2.pop(0)

    # Update first graph
    ax1.clear()
    ax1.plot(sensor_data_1, label="Célula de carga", color="blue")
    ax1.set_title("Carga aplicada")
    ax1.set_xlabel("Tiempo (s)")
    ax1.set_ylabel("Masa (kg)")
    ax1.legend(loc="lower left")

    # Update second graph
    ax2.clear()
    ax2.plot(sensor_data_2, label="Potenciómetro", color="red")
    ax2.set_title("Medida de deformación en centro de vano")
    ax2.set_xlabel("Tiempo (s)")
    ax2.set_ylabel("Flecha (mm)")
    ax2.legend(loc="lower left")

    fig.tight_layout()

# Tkinter GUI Setup
root = tk.Tk()
root.title("Arduino Sensor Data Viewer")
root.geometry("1000x700")  # Increased height to accommodate logos

# Title Label
title_label = ttk.Label(root, text="II Concurso Nacional de Puentes Agustín de Betancourt - Fase Provincial - ETSICCP GRANADA", font=("Arial", 16))
title_label.pack(pady=10)

# Create a Matplotlib Figure with two subplots side by side
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 6))

# Embed Matplotlib figure in Tkinter
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

# Create a container frame for logos (spanning full width at bottom)
logo_container = tk.Frame(root)
logo_container.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=10)  # Ensures alignment at the same level

# Create left and right frames inside the container
logo_frame_left = tk.Frame(logo_container)
logo_frame_left.pack(side=tk.LEFT, anchor=tk.S)  # Align left logos

logo_frame_right = tk.Frame(logo_container)
logo_frame_right.pack(side=tk.RIGHT, anchor=tk.S)  # Align right logo

# Load images
logo_ugr_path = "logos/ugr.png"
logo_etsiccp_path = "logos/etsiccp.png"
logo_grupo_puentes_path = "logos/grupo_puentes.png"

logo_ugr_img = Image.open(logo_ugr_path)
logo_ugr_img = logo_ugr_img.resize((100, 100), Image.Resampling.LANCZOS)
logo_ugr_tk = ImageTk.PhotoImage(logo_ugr_img)

logo_etsiccp_img = Image.open(logo_etsiccp_path)
logo_etsiccp_img = logo_etsiccp_img.resize((100, 100), Image.Resampling.LANCZOS)
logo_etsiccp_tk = ImageTk.PhotoImage(logo_etsiccp_img)

logo_grupo_puentes_img = Image.open(logo_grupo_puentes_path)
logo_grupo_puentes_img = logo_grupo_puentes_img.resize((100, 100), Image.Resampling.LANCZOS)
logo_grupo_puentes_tk = ImageTk.PhotoImage(logo_grupo_puentes_img)

# Add left-side logos
logo_ugr_label = tk.Label(logo_frame_left, image=logo_ugr_tk)
logo_ugr_label.pack(side=tk.LEFT, padx=5)

logo_etsiccp_label = tk.Label(logo_frame_left, image=logo_etsiccp_tk)
logo_etsiccp_label.pack(side=tk.LEFT, padx=5)

# Add right-side logo
logo_grupo_puentes_label = tk.Label(logo_frame_right, image=logo_grupo_puentes_tk)
logo_grupo_puentes_label.pack(side=tk.RIGHT, padx=5)

# Run Matplotlib animation
ani = FuncAnimation(fig, update_graph, interval=1000, cache_frame_data=False)  # Update every second

# Run Tkinter main loop
try:
    root.mainloop()  # Run the GUI
except KeyboardInterrupt:
    print("\n[INFO] KeyboardInterrupt detected. Closing GUI...")
    root.quit()  # Gracefully exit the GUI loop
    root.destroy()  # Ensure Tkinter window is properly closed