import sqlite3

# Funktion zum Abrufen des neuesten Eintrags aus der Datenbank – unabhängig vom Gerät
def get_latest_device():
    # Verbindung zur SQLite-Datenbank herstellen
    con = sqlite3.connect('sensordata.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # SQL-Abfrage: Holt die zuletzt empfangenen Sensordaten zusammen mit Geräteinformationen
    cur.execute("""
        SELECT
            d.device_id,
            d.application_id,
            p.temperature,
            p.humidity,
            p.motion,
            p.light,
            p.vdd,
            p.received_at
        FROM
            payloads p
        JOIN
            devices d ON d.id = p.device_id
        ORDER BY
            p.received_at DESC
        LIMIT 1;
    """)

    row = cur.fetchone()
    con.close()

    # Verpacke die Informationen in ein Dictionary
    if row:
        result = {
            "device_id": row["device_id"],
            "application_id": row["application_id"],
            "temperature": row["temperature"],
            "humidity": row["humidity"],
            "motion": row["motion"],
            "light": row["light"],
            "vdd": row["vdd"],
            "received_at": row["received_at"]
        }
        return result
    else:
        return {"message": "No data found"}

# Funktion zum Abrufen des neuesten Eintrags für ein bestimmtes Gerät (per ID)
def get_latest_data_by_device_id(device_id: str):
    # Verbindung zur SQLite-Datenbank
    con = sqlite3.connect('sensordata.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # SQL-Abfrage: Holt die neuesten Sensordaten für das angegebene Gerät
    cur.execute("""
        SELECT
            d.device_id,
            d.application_id,
            p.temperature,
            p.humidity,
            p.motion,
            p.light,
            p.vdd,
            p.received_at
        FROM
            payloads p
        JOIN
            devices d ON d.id = p.device_id
        WHERE
            d.device_id = ?
        ORDER BY
            p.received_at DESC
        LIMIT 1;
    """, (device_id,))

    row = cur.fetchone()
    con.close()

    # Verpacke die Informationen in ein Dictionary
    if row:
        result = {
            "device_id": row["device_id"],
            "application_id": row["application_id"],
            "temperature": row["temperature"],
            "humidity": row["humidity"],
            "motion": row["motion"],
            "light": row["light"],
            "vdd": row["vdd"],
            "received_at": row["received_at"]
        }
    else:
        result = {"error": f"No data found for device_id '{device_id}'"}

    return result
