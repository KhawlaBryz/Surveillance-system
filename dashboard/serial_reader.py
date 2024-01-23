import serial
import re
import sqlite3

conn = sqlite3.connect('arduino_data.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        light_intensity INTEGER,
        temperature REAL
    )
''')

port = 'COM10'  # Remplacez 'COM10' par le port série de votre Arduino
baudrate = 9600  # Assurez-vous que la vitesse de transmission correspond à celle configurée dans votre code Arduino

try:
    ser = serial.Serial(port, baudrate)
    if ser.isOpen():
        print(f"Port série {port} ouvert.")
        
        while True:
            if ser.in_waiting > 0:
                data = ser.readline().decode().strip()
                print(f"Donnée reçue: {data}")
                
                light_intensity_match = re.search(r'lightIntensity:\s*(\d+)', data)
                temperature_match = re.search(r'Temperature:\s*([\d.]+)\s*C', data)
                
                if light_intensity_match and temperature_match:
                    light_intensity = int(light_intensity_match.group(1))
                    temperature = float(temperature_match.group(1))
                    
                    cursor.execute('INSERT INTO sensor_data (light_intensity, temperature) VALUES (?, ?)', (light_intensity, temperature))
                    conn.commit()
                elif light_intensity_match:
                    light_intensity = int(light_intensity_match.group(1))
                    cursor.execute('INSERT INTO sensor_data (light_intensity) VALUES (?)', (light_intensity,))
                    conn.commit()
                elif temperature_match:
                    temperature = float(temperature_match.group(1))
                    cursor.execute('INSERT INTO sensor_data (temperature) VALUES (?)', (temperature,))
                    conn.commit()
                else:
                    print("Les données reçues ne contiennent ni intensité lumineuse ni température.")
                
except serial.SerialException as e:
    print(f"Erreur: {e}")
finally:
    ser.close() if 'ser' in locals() else None
    conn.close()
