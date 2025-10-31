

# GPS_tracker_nmea (NMEA Serial Reader)

A simple, lightweight Python module for reading GPS data from NMEA-compatible serial devices.  
It parses NMEA sentences in real-time, provides callbacks for new positions, saves history, and supports basic geofencing.

---

## 🚀 Features

- Read NMEA data from any serial GPS module  
- Parse latitude, longitude, altitude, and timestamps  
- Optional callback function for new GPS fixes  
- Thread-based reading loop (non-blocking)  
- Position history storage (configurable size)  
- Save data to CSV  
- Simple circular geofence check  

---

## 🧠 Intended Users

This module is ideal for:

- 🧰 **Makers and hobbyists** working with GPS modules on Raspberry Pi, Arduino, or similar hardware.  
- 🧑‍🔬 **Researchers and developers** needing to log or process real-time GPS data.  
- 🎓 **Students and educators** learning about serial communication, threading, and GPS parsing.  
- 🚗 **Prototype builders** developing location-aware applications.  

---

## ⚙️ Installation

Install dependencies first:

_bash 
pip install pyserial pynmea2_

Then clone this repository:

_git clone https://github.com/<your-username>/gps-tracker.git
cd gps-tracker_


---

🧩 Basic Usage

from gps_tracker import GPSTracker, Position

def callback(position: Position):
    print("New position:", position)

tracker = GPSTracker(serial_port="/dev/ttyUSB0", baudrate=9600)
tracker.set_callback(callback)
tracker.start()

# Run until stopped manually
try:
    while True:
        pass
except KeyboardInterrupt:
    tracker.stop()


---

📊 Saving History

You can save all recorded GPS positions to a CSV file:

tracker.save_history_csv("gps_data.csv")

The CSV contains columns:

lat, lon, alt, timestamp


---

📍 Geofencing Example

Check whether the last known position is inside a circular area:

inside = tracker.geofence_check_circle(center=(-23.5505, -46.6333), radius_m=100)
if inside:
    print("Inside the geofence!")
else:
    print("Outside the geofence.")


---

🧪 Command-Line Demo

You can also run the module directly for testing:

python gps_tracker.py --port /dev/ttyUSB0 --baud 9600

Press Ctrl+C to stop.


---

🧱 Project Structure

gps_tracker.py    # Main module
README.md          # This file


---

🧑‍💻 License

This project is released under the MIT License — feel free to use, modify, and distribute.


---

🤝 Contributing

Pull requests are welcome!
If you have ideas for improvements — such as visualization, logging, or error handling — feel free to open an issue or submit a PR.


---

💬 Contact

Created by Pedrocode-master.
If you use this module in your project, feel free to share your experience or improvements!

---
