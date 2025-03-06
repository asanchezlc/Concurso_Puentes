
import time
import serial
import datetime
import numpy as np

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
    inverted_sign = False

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


def read_arduino_data_thread(ser, data_queue) -> None:
    """
    Function Duties:
        Continuously reads data from Arduino and stores it in a queue.
    Input:
        ser: Serial object
        data_queue: Queue to store the data
    Output:
        None (it will be in a thread)
    """
    while True:
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



def simulated_data_thread(data_queue) -> None:
    """
    Function Duties:
        Continuously reads data from Arduino and stores it in a queue.
    Input:
        ser: Serial object
        data_queue: Queue to store the data
    Output:
        None (it will be in a thread)
    """
    import numpy as np
    while True:
        delta_t, bits_hx711, bits_potentiometer = 50, np.random.randint(0, 2**10), np.random.randint(0, 2**6)
        time_now = datetime.datetime.now().timestamp()
        bits_hx711 += time_now * 100000
        bits_potentiometer += time_now*30
        if np.random.randint(0, 1000) == 0:  # Simulate an outlier value
            bits_hx711 = 2**13
        data_queue.put(
            (int(delta_t), int(bits_hx711), int(bits_potentiometer)))
        time.sleep(delta_t / 1000)  # Convert ms to seconds


def manual_find_peaks(list_values, threshold):
    """
    Function Duties:
        Find peaks in a list of values using a threshold.
    Input:
        list_values: list of values
        threshold: minimum difference between consecutive values
    Output:
        valid_indices: indices of the peaks
    """
    # Compute differences between consecutive elements -> get outliers
    diff_before = np.abs(np.diff(list_values, prepend=np.nan))
    diff_after = np.abs(np.diff(list_values, append=np.nan))
    outliers = (diff_before > threshold) & (diff_after > threshold)

    # Get indices of non-outliers
    valid_indices = np.where(~outliers)[0]

    return valid_indices


def smooth_with_edges(data_list, step):
    data_list = np.array(data_list, dtype=np.float64)  # Ensure float for averaging
    n = len(data_list)

    if n <= 2 * step:
        return data_list  # If the list is too small, return as is

    # Compute moving average for the middle part
    smoothed_values = np.convolve(data_list, np.ones(step)/step, mode='valid')

    # Initialize output array
    result = np.zeros(n)
    
    # Compute progressive averaging for the first `step` elements
    for i in range(step):
        result[i] = np.mean(data_list[:i + step])  # Average available values before step

    # Compute progressive averaging for the last `step` elements
    for i in range(n - step, n):
        result[i] = np.mean(data_list[i - step + 1:])  # Average available values after step

    # Insert the moving average in the middle
    mid_start = step
    mid_end = n - step
    result[mid_start:mid_end] = smoothed_values[:mid_end - mid_start]

    return result
