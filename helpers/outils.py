
import serial
import time
import datetime


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
                    delta_t, hx711_value, voltage = data.split()
                    # Store data in queue
                    data_queue.put(
                        (int(delta_t), int(hx711_value), float(voltage)))
            except ValueError:
                print("[ERROR] Formato de datos incorrecto:", data)
                continue  # Skip bad data

def update_graph(frame):
    """Function to update the graphs"""
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
        # print("[WARNING] No se pudo leer datos, reutilizando último valor.")
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
    ax1.plot(time_data[-n_readings:], sensor_data_1[-n_readings:],
             label="Célula de carga", color="blue")
    ax1.set_title("Carga aplicada")
    ax1.set_xlabel("Tiempo (s)")
    ax1.set_ylabel("BITS (kg)")
    ax1.legend(loc="lower left")

    # Update second graph
    ax2.clear()
    ax2.plot(time_data[-n_readings:], sensor_data_2[-n_readings:],
             label="Potenciómetro", color="red")
    ax2.set_title("Medida de deformación en centro de vano")
    ax2.set_xlabel("Tiempo (s)")
    ax2.set_ylabel("VOLTAJE (mm)")
    ax2.legend(loc="lower left")

    if not (voltage is None and hx711_value is None):
        delta_t = datetime.datetime.now().timestamp() - last_timestamp
        last_timestamp = datetime.datetime.now().timestamp()
        print(
            f"Tiempo: {delta_t} | Peso (HX711): {hx711_value} | Voltaje (Potenciómetro): {voltage:.2f} V | Δt: {delta_t:.2f} s")

    fig.tight_layout()

def toggle_pause():
    """Function to toggle pause/display"""
    global pause
    pause = not pause  # Toggle state
    pause_button.config(text="Display" if pause else "Pause")  # Change button text

def close_app():
    """Handle GUI closing and KeyboardInterrupt"""
    print("\n[INFO] Closing application...")
    ani.event_source.stop()
    if ser:
        ser.close()
    root.quit()
    root.destroy()
