# Standardbibliotheken und externe Module importieren
import random
import os
import json
import sqlite3

from dotenv import load_dotenv
from paho.mqtt import client as mqtt_client
from sql_utils import insert_payload_data

# Umgebungsvariablen laden (mqtt_password)
load_dotenv()

# MQTT-Verbindungsinformationen definieren
mqtt_broker = "eu2.cloud.thethings.industries"   # Adresse des MQTT-Brokers
mqtt_port = 1883                                 # Standardport für unverschlüsseltes MQTT
mqtt_topic = "v3/haus@vebl-network/devices/eui-a81758fffe07a941/up"  # Topic für Nachrichten
mqtt_id = f'subscribe{random.randint(0, 100)}'   # Zufällige Client-ID zur Vermeidung von Konflikten
mqtt_username = "haus@vebl-network"              # Benutzername für Authentifizierung
mqtt_password = os.getenv('MQTT_PW')             # Passwort aus Umgebungsvariable

# Funktion zur Verbindung mit dem MQTT-Broker
def connect_mqtt() -> mqtt_client:
    # Rückmeldung ob Verbindung aufgebaut werden konnte
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}\n")

    # MQTT-Client-Objekt erstellen und konfigurieren
    client = mqtt_client.Client(mqtt_id)
    client.username_pw_set(mqtt_username, mqtt_password) 
    client.on_connect = on_connect 
    client.connect(mqtt_broker, mqtt_port)
    return client

# Funktion zum Abonnieren eines MQTT-Themas und Behandeln eingehender Nachrichten
def subscribe(client: mqtt_client):
    # Funktion beim Empfang von MQTT Nachrichten
    def on_message(client, userdata, msg):
        print(f"Received '{msg.payload.decode()}' from '{msg.topic}' topic")
        # Empfangene JSON Nachricht wird in Datenbank gespeichert
        insert_payload_data(json.loads(msg.payload.decode()))
    
    client.subscribe(mqtt_topic)
    client.on_message = on_message

# Funktion zum Starten des MQTT-Clients und der Nachrichtenverarbeitung
def loop_mqtt():
    client = connect_mqtt()
    subscribe(client)
    client.loop_start()
