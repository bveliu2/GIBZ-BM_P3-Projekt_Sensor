import random
import sys
import os
import asyncio
import uvicorn
import threading
import mqtt_utils as mqtt_utils # Importiert mqtt_utils.py
import api_utils as api_utils # Importiert api_utils.py
import gui_utils as gui_utils # Importiert gui_utils.py

from sql_utils import create_tables 
from fastapi import FastAPI
from PyQt6.QtWidgets import QApplication
from contextlib import asynccontextmanager

# Startet den MQTT-Loop beim Starten der FastAPI-Anwendung
@asynccontextmanager
async def lifespan(app: FastAPI):
    mqtt_utils.loop_mqtt()
    print("MQTT client started")
    yield

app = FastAPI(lifespan=lifespan)

# Erstellt die Datenbanktabellen, falls sie nicht existieren
create_tables()

# Verbindet den MQTT-Client und abonniert relevante Topics
mqtt_client_instance = mqtt_utils.connect_mqtt()
mqtt_utils.subscribe(mqtt_client_instance)

# Root-Endpoint für die API
@app.get("/")
async def read_root():
    return {"message": "This is the root endpoint of the sensor API."}

# Gibt den Status des letzten Geräts zurück
@app.get("/api/status")
async def read_state():
    return api_utils.get_latest_device()

# Gibt neuste Sensordaten für ein bestimmtes Gerät zurück
@app.get("/api/status/{sensor}")
async def read_sensor(sensor):
    return api_utils.get_latest_data_by_device_id(sensor)

# Startet Uvicorn-Server für die FastAPI-Anwendung
def run_server():
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=80,
        reload=False
    )

# Startet das GUI
def start_gui():
    gui = QApplication(sys.argv)
    dashboard = gui_utils.Dashboard()
    dashboard.show()
    sys.exit(gui.exec())

# Startpunkt des Programms
if __name__ == "__main__":
    # Starte den FastAPI-Server in einem Hintergrund-Thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Starte das GUI im Haupt-Thread
    start_gui()
