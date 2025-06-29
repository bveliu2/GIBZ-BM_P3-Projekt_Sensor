import sqlite3

def create_tables():
    # Sqlite3 connection
    con = sqlite3.connect('sensordata.db')
    cur = con.cursor()
    # Erstellt Tabelle für Devices
    cur.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE,
            application_id TEXT,
            dev_eui TEXT,
            join_eui TEXT,
            dev_addr TEXT
        );
    """)

    # Erstellt Tabelle für Payloads
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            temperature REAL,
            humidity INTEGER,
            motion INTEGER,
            light INTEGER,
            vdd INTEGER,
            received_at TEXT,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        );
    """)

def insert_payload_data(data):
    # Sqlite3 connection
    con = sqlite3.connect('sensordata.db')
    cur = con.cursor()

    # 1. Device-Daten extrahieren und einfügen
    device_info = data["end_device_ids"]
    device_id_str = device_info["device_id"]
    application_id = device_info["application_ids"]["application_id"]
    dev_eui = device_info.get("dev_eui")
    join_eui = device_info.get("join_eui")
    dev_addr = device_info.get("dev_addr")

    cur.execute("""
        INSERT OR IGNORE INTO devices (device_id, application_id, dev_eui, join_eui, dev_addr)
        VALUES (?, ?, ?, ?, ?)
    """, (device_id_str, application_id, dev_eui, join_eui, dev_addr))
    con.commit()

    # Device-ID aus DB holen
    cur.execute("SELECT id FROM devices WHERE device_id = ?", (device_id_str,))
    device_row = cur.fetchone()
    if not device_row:
        print("Fehler: Gerät nicht gefunden.")
        return
    device_id = device_row[0]

    # 2. Payload-Daten extrahieren
    uplink = data["uplink_message"]
    decoded = uplink.get("decoded_payload", {})

    temperature = decoded.get("temperature")
    humidity = decoded.get("humidity")
    motion = decoded.get("motion")
    light = decoded.get("light")
    vdd = decoded.get("vdd")
    received_at = data.get("received_at")

    # 3. Payload einfügen
    cur.execute("""
        INSERT INTO payloads (
            device_id, temperature, humidity, motion, light, vdd, received_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (device_id, temperature, humidity, motion, light, vdd, received_at))
    con.commit()
