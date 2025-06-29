import sys
import sqlite3
from PyQt6.QtWidgets import (
   QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox, QDateEdit
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt, QTimer, QDate
import pyqtgraph as pg
from datetime import datetime, timedelta

# Pfad zur Datenbankdatei
DB_PATH = "sensordata.db"

# Wandelt Batteriespannung in Prozent um (2900–4200 mV entspricht 0–100 %)
def get_vdd_percentage(vdd_mv):
   if vdd_mv <= 2900:
       return 0
   elif vdd_mv >= 4200:
       return 100
   else:
       percent = (vdd_mv - 2900) / (4200 - 2900) * 100
       return round(percent)

# Gibt abhängig vom Sensorwert eine passende Farbe zurück
def get_color_for_value(sensor, value):
   if sensor == "temperature":
       if value < 10:
           return "#3498db"  # Blau
       elif value < 25:
           return "#2ecc71"  # Grün
       else:
           return "#e74c3c"  # Rot
   elif sensor == "humidity":
       if value < 30:
           return "#f1c40f"  # Gelb
       else:
           return "#2ecc71"  # Grün
   elif sensor == "vdd":
       if value < 2500:
           return "#e67e22"  # Orange
       else:
           return "#2ecc71"  # Grün
   return "white"

# Visuelle Komponente zur Darstellung eines einzelnen Sensors (z.B Temperaturkarte)
class SensorCard(QFrame):
   def __init__(self, title, icon_path):
       super().__init__()
       self.setMinimumSize(160, 140)
       self.setStyleSheet("""...""")
       
       layout = QVBoxLayout()
       
       # Titel
       self.label_title = QLabel(title)
       self.label_title.setFont(QFont("Arial", 10))
       self.label_title.setWordWrap(True)
       layout.addWidget(self.label_title, alignment=Qt.AlignmentFlag.AlignCenter)

       # Icon des Sensors
       self.value_icon = QLabel()
       self.value_icon.setFixedSize(60, 60)
       self.value_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
       self.value_icon.setScaledContents(True)
       self.value_icon.setStyleSheet("padding: 4px; background-color: transparent;")
       pixmap = QPixmap(icon_path)
       if not pixmap.isNull():
           pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
           self.value_icon.setPixmap(pixmap)
       layout.addWidget(self.value_icon, alignment=Qt.AlignmentFlag.AlignCenter)

       # Zahlenwert des Sensors
       self.label_value = QLabel("--")
       self.label_value.setFont(QFont("Arial", 14, weight=QFont.Weight.Bold))
       self.label_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
       self.label_value.setWordWrap(True)
       layout.addWidget(self.label_value)

       self.setLayout(layout)

   # Aktualisiert den angezeigten Sensorwert und Farbe
   def update_value(self, value, unit="", color="white"):
       self.label_value.setStyleSheet(f"color: {color};")
       self.label_value.setText(f"{value} {unit}")

# Hauptfenster mit GUI-Layout und Datenaktualisierung
class Dashboard(QWidget):
   def __init__(self):
       super().__init__()
       self.setWindowTitle("Fluxview")
       self.setMinimumSize(1000, 600)

       self.main_layout = QVBoxLayout()

       title_label = QLabel("Fluxview")
       title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
       title_label.setStyleSheet("color: white; padding: 10px;")
       self.main_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

       # Kartenlayout für Sensoren
       self.card_layout = QHBoxLayout()
       self.cards = {
           "temperature": SensorCard("Temperatur", "assets/icons/temperature.png"),
           "humidity": SensorCard("Luftfeuchtigkeit", "assets/icons/humidity.png"),
           "motion": SensorCard("Bewegung", "assets/icons/motion.png"),
           "light": SensorCard("Licht", "assets/icons/sun.png"),
           "vdd": SensorCard("Batterie", "assets/icons/battery.png"),
       }
       for card in self.cards.values():
           self.card_layout.addWidget(card)
       self.main_layout.addLayout(self.card_layout)

       # Zeitstempel der letzten Messung
       self.timestamp_label = QLabel("Letzte Messung: --")
       self.timestamp_label.setStyleSheet("color: white; padding: 10px;")
       self.timestamp_label.setFont(QFont("Arial", 12, QFont.Weight.DemiBold))
       self.main_layout.addWidget(self.timestamp_label, alignment=Qt.AlignmentFlag.AlignCenter)

       self.sensor_display_map = {
           "Temperatur": "temperature",
           "Luftfeuchtigkeit": "humidity",
           "Licht": "light",
           "Batterie": "vdd",
           "Bewegung": "motion"
       }
       self.sensor_internal_map = {v: k for k, v in self.sensor_display_map.items()}

       # Dropdown zur Auswahl des Sensors für das Diagramm
       self.sensor_selector = QComboBox()
       self.sensor_selector.addItems(self.sensor_display_map.keys())
       self.sensor_selector.setCurrentText("Temperatur")
       self.sensor_selector.currentTextChanged.connect(self.update_data)
       self.sensor_selector.setStyleSheet("""...""")
       self.main_layout.addWidget(self.sensor_selector, alignment=Qt.AlignmentFlag.AlignCenter)

       # Datumsbereich für die Diagrammfilterung
       self.date_layout = QHBoxLayout()
       self.date_from = QDateEdit(calendarPopup=True)
       self.date_to = QDateEdit(calendarPopup=True)
       today = QDate.currentDate()
       self.date_from.setDate(today.addDays(-7))  # Standard: letzte 7 Tage
       self.date_to.setDate(today)
       for date_edit in [self.date_from, self.date_to]:
           date_edit.setDisplayFormat("dd.MM.yyyy")
           date_edit.setStyleSheet("""...""")
           date_edit.dateChanged.connect(self.update_data)
           self.date_layout.addWidget(date_edit)
       self.main_layout.addLayout(self.date_layout)

       self.selected_sensor = "temperature"

       # Diagramm zur Anzeige des Sensorverlaufs
       self.graph_widget = pg.PlotWidget(title="Sensorverlauf")
       self.graph_widget.setBackground("#dce6f0")
       self.graph_widget.setLabel('left', 'Sensorwert')
       self.graph_widget.setLabel('bottom', 'Zeit')
       self.main_layout.addWidget(self.graph_widget)

       self.setLayout(self.main_layout)

       self.update_data()

       # Timer zur regelmäßigen Aktualisierung (alle 30 Sekunden)
       self.timer = QTimer(self)
       self.timer.timeout.connect(self.update_data)
       self.timer.start(30 * 1000)

   # Holt aktuelle Sensordaten aus der Datenbank und aktualisiert GUI
   def update_data(self):
       try:
           # Auswahl aktueller Sensor
           selected_label = self.sensor_selector.currentText()
           self.selected_sensor = self.sensor_display_map[selected_label]

           # Datumsbereich für Abfrage
           date_from_str = self.date_from.date().toString("yyyy-MM-dd")
           date_to_str = self.date_to.date().toString("yyyy-MM-dd")

           # Verbindung zur SQLite-Datenbank
           conn = sqlite3.connect(DB_PATH)
           cur = conn.cursor()

           # Letzte aktuelle Werte abfragen
           cur.execute("SELECT temperature, humidity, motion, light, vdd, received_at FROM payloads ORDER BY id DESC LIMIT 1")
           row = cur.fetchone()
           if row:
               temp, hum, motion, light, vdd, received_at = row
               # Karten aktualisieren
               self.cards["temperature"].update_value(temp, "°C", get_color_for_value("temperature", temp))
               self.cards["humidity"].update_value(hum, "%", get_color_for_value("humidity", hum))
               self.cards["motion"].update_value("Ja" if motion else "Nein")
               self.cards["light"].update_value(light, "lx")
               vdd_percent = get_vdd_percentage(vdd)
               self.cards["vdd"].update_value(f"{vdd_percent}%", "", get_color_for_value("vdd", vdd))
               # Zeitstempel anzeigen
               if received_at:
                   dt = datetime.fromisoformat(received_at.replace("Z", "")) + timedelta(hours=2)
                   self.timestamp_label.setText(f"Letzte Messung: {dt.strftime('%H:%M:%S')} - {dt.strftime('%d.%m.%Y')}")

           # Verlauf für den gewählten Sensor im angegebenen Zeitraum laden
           cur.execute(f"""
               SELECT {self.selected_sensor}, received_at
               FROM payloads
               WHERE DATE(received_at) BETWEEN ? AND ?
               ORDER BY received_at ASC
           """, (date_from_str, date_to_str))
           data = cur.fetchall()

           # Wenn keine Daten vorhanden sind, leeres Diagramm anzeigen
           if not data:
               self.graph_widget.clear()
               self.graph_widget.setTitle("Keine Daten im gewählten Zeitraum")
               return

           # Werte und Zeitlabels extrahieren
           values = [row[0] for row in data]
           labels = []
           last_date = ""
           for row in data:
               if row[1]:
                   dt = datetime.fromisoformat(row[1].replace("Z", "")) + timedelta(hours=2)
                   label = dt.strftime('%H:%M')
                   if dt.strftime('%d.%m.%Y') != last_date:
                       label += f"\n{dt.strftime('%d.%m.%Y')}"
                       last_date = dt.strftime('%d.%m.%Y')
                   labels.append(label)

           # Diagramm aktualisieren
           self.graph_widget.setLabel('left', selected_label)
           self.graph_widget.clear()
           self.graph_widget.plot(list(range(len(values))), values, pen=pg.mkPen(color='#e74c3c', width=2), symbol='o')
           ax = self.graph_widget.getAxis("bottom")
           ax.setTicks([list(enumerate(labels))])

           conn.close()
       except Exception as e:
           # Fehlerausgabe bei Problemen
           print(f"Fehler beim Laden der Daten: {e}")
