import tkinter as tk
from tkinter import ttk
import random
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk  # Import Pillow for image handling
import os

# Variables for GUI configuration
refresh_time = 1000  # ms (1 second)
GUI_title = "Fase Provincial - II Concurso Nacional de Puentes Agustín de Betancourt - ETSICCP GRANADA"
logo_folder = "logos"
logo_ugr_name = "ugr.png"
logo_etsiccp_name = "etsiccp.png"
logo_grupo_puentes_name = "grupo_puentes.png"

# Simulated Sensor Data
sensor_data_1 = []
sensor_data_2 = []
pause = False  # Variable to track if data updates are paused

# Function to simulate sensor readings


def generate_sensor_data():
    "This function must be substituted by the ARDUINO code to read the sensors"
    return round(random.uniform(20, 30), 2)

# Function to update the graphs


def update_graph(frame):
    global sensor_data_1, sensor_data_2, pause

    if pause:  # If paused, do not update the graph
        return

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

# Function to toggle pause/display


def toggle_pause():
    global pause
    pause = not pause  # Toggle state
    # Change button text
    pause_button.config(text="Display" if pause else "Pause")


# Tkinter GUI Setup
root = tk.Tk()
root.title("Arduino Sensor Data Viewer")

# Make the window start maximized
root.state('zoomed')

# Configure grid system to be responsive
root.grid_rowconfigure(1, weight=1)  # Allows graphs to stretch
root.grid_columnconfigure(0, weight=1)  # Makes main column expand

# 1. HEADER (Title + Logos)
# Create container
header_container = tk.Frame(root)
header_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

# Create LEFT, CENTER, and RIGHT frames inside the header
logo_frame_left = tk.Frame(header_container)
logo_frame_left.pack(side=tk.LEFT, anchor=tk.N)
title_frame = tk.Frame(header_container)
title_frame.pack(side=tk.LEFT, expand=True)
logo_frame_right = tk.Frame(header_container)
logo_frame_right.pack(side=tk.RIGHT, anchor=tk.N)

# Set the title (Center position within the header container)
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

# 2. MAIN GRAPHS (Matplotlib)
# Create fig and embed Matplotlib figure in Tkinter
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 6))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")  # Expand with window

# 3. BOTTOM BUTTOM (Pause/Update Button)
# Create a container frame for bottom widgets (Pause Button)
bottom_container = tk.Frame(root)
bottom_container.grid(row=2, column=0, sticky="sew", padx=10, pady=5)

# Make sure the bottom row does not take too much space
root.grid_rowconfigure(2, weight=0)

# Pause Button (Bottom-Right)
pause_button = ttk.Button(bottom_container, text="Pause", command=toggle_pause)
pause_button.pack(side=tk.RIGHT, padx=10)

# Run Matplotlib animation
ani = FuncAnimation(fig, update_graph, interval=refresh_time,
                    cache_frame_data=False)  # Update every second

# Handle GUI closing and KeyboardInterrupt (Ctrl+C)


def close_app():
    print("\n[INFO] Closing application...")
    ani.event_source.stop()
    root.quit()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_app)  # Handle window close event

# Run Tkinter main loop
try:
    root.mainloop()
except KeyboardInterrupt:
    close_app()
