
import serial
import time
import datetime

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


def connect_arduino(port, baud_rate):
    """
    Function Duties:
        Establish a serial connection and return the Serial object.
    Input: (check .ino file to see the port and baud rate)
        port: COM port where the Arduino is connected
        baud_rate: communication speed (e.g. 9600)
    Output:
        ser: Serial object or None if the connection fails
    """
    try:
        ser = serial.Serial(port, baud_rate, timeout=1)
        print(f"[INFO] Conectado a {port}")
        time.sleep(2)  # Wait for Arduino to be ready
        return ser
    except serial.SerialException:
        print(f"[ERROR] No se pudo abrir el puerto {port}")
        return None  # No active connection



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
    ax1.set_title("Carga Aplicada")
    ax1.set_xlabel("Tiempo (s)")
    ax1.set_ylabel("Masa (kg)")
    ax1.legend(loc="lower left")
    ax1.set_ylim([0, max(data_mass) + 5])

    # Update second graph
    ax2.clear()
    ax2.plot(time_data[-n_readings:], data_deflections[-n_readings:],
             label="Potenciómetro", color="red")
    ax2.set_title("Flecha en Centro de Vano")
    ax2.set_xlabel("Tiempo (s)")
    ax2.set_ylabel("Flecha (mm)")
    ax2.set_ylim([0, max(data_deflections) + 5])
    ax2.legend(loc="lower left")

    if not (mass is None and deflection is None):
        delta_t = datetime.datetime.now().timestamp() - last_timestamp
        last_timestamp = datetime.datetime.now().timestamp()
        print(
            f"Tiempo: {t:.0f} | Peso (HX711): {mass:.3f} kg | Voltaje (Potenciómetro): {deflection:.3f} mm | Δt: {delta_t:.4f} s")

    fig_left.tight_layout()


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