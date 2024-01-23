import sqlite3
from datetime import datetime

conn = sqlite3.connect('arduino_data.db')
cursor = conn.cursor()

# Récupérer les enregistrements sans timestamp
cursor.execute('SELECT id FROM sensor_data WHERE timestamp IS NULL')
records_without_timestamp = cursor.fetchall()

# Mettre à jour chaque enregistrement sans timestamp
for record in records_without_timestamp:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('UPDATE sensor_data SET timestamp=? WHERE id=?', (timestamp, record[0]))

conn.commit()
conn.close()

