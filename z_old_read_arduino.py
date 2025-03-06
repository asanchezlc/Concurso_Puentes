
import serial
import time


arduino_port = "COM7"
baud_rate = 9600

# Iniciar conexión serial
try:
    ser = serial.Serial(arduino_port, baud_rate, timeout=1)
    print(f"Conectado a {arduino_port}")
    time.sleep(2)
except serial.SerialException:
    print(f"Error: No se pudo abrir el puerto {arduino_port}")
    exit()

# Leer datos en tiempo real
try:
    while True:
        if ser.in_waiting > 0:  # Verify if available data
            data = ser.readline().decode('utf-8').strip()
            if data:
                try:
                    hx711_value, voltage = data.split()  # arduino saves thems separated
                    hx711_value = int(hx711_value)
                    voltage = float(voltage)
                    
                    # Mostrar en pantalla
                    print(f"Peso (HX711): {hx711_value} | Voltaje (Potenciómetro): {voltage:.2f} V")
                except ValueError:
                    print("Error de formato en la línea recibida:", data)

except KeyboardInterrupt:
    print("\nDeteniendo la lectura...")
    ser.close()
    print("Conexión serial cerrada.")
