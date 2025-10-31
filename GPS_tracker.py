"""
gps_tracker.py
Simple GPS tracking module using NMEA (serial).
Dependencies: pyserial, pynmea2

Basic usage:
from gps_tracker import GPSTracker
tracker = GPSTracker(serial_port="/dev/ttyUSB0", baudrate=9600)
tracker.start()

or use a callback:

def cb(pos): print("pos:", pos)
tracker.set_callback(cb)

later

tracker.stop()
"""

import threading
import time
import csv
from collections import deque
from typing import Callable, Optional, Dict, Any, Tuple, List

try:
    import serial
except Exception as e:
    raise ImportError("pyserial not found. Install with: pip install pyserial") from e

try:
    import pynmea2
except Exception as e:
    raise ImportError("pynmea2 not found. Install with: pip install pynmea2") from e


class Position:
    """Simple class to store GPS position."""

    def __init__(self, lat: float, lon: float, alt: Optional[float], timestamp: Optional[float]):
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.timestamp = timestamp  # epoch seconds when fix was read (or None)

    def to_dict(self) -> Dict[str, Any]:
        return {"lat": self.lat, "lon": self.lon, "alt": self.alt, "timestamp": self.timestamp}

    def __repr__(self):
        return f"Position(lat={self.lat:.6f}, lon={self.lon:.6f}, alt={self.alt}, time={self.timestamp})"


class GPSTracker:
    """
    GPSTracker: reads NMEA sentences from a serial port and provides:
    - start()/stop()
    - callback when a new valid position is obtained
    - get_last(), get_history()
    - simple geofence detection (circle)
    """

    def __init__(
        self,
        serial_port: str,
        baudrate: int = 9600,
        timeout: float = 1.0,
        history_size: int = 1000
    ):
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.timeout = timeout
        self._ser: Optional[serial.Serial] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._callback: Optional[Callable[[Position], None]] = None
        self._history: deque = deque(maxlen=history_size)
        self._lock = threading.Lock()
        self._last_position: Optional[Position] = None

    def set_callback(self, cb: Callable[[Position], None]):
        """Registers callback(pos: Position) called for each new valid position."""
        self._callback = cb

    def start(self):
        """Opens the serial port and starts the reading thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stops the reading thread and closes the serial port."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            except Exception:
                pass

    def _open_serial(self):
        if self._ser and self._ser.is_open:
            return
        self._ser = serial.Serial(self.serial_port, baudrate=self.baudrate, timeout=self.timeout)

    def _read_loop(self):
        try:
            self._open_serial()
        except Exception as e:
            print(f"[GPSTracker] error opening serial {self.serial_port}: {e}")
            return

        while not self._stop_event.is_set():
            try:
                line = self._ser.readline()
                if not line:
                    continue
                try:
                    # pyserial returns bytes; decode ignoring errors
                    line_str = line.decode(errors="ignore").strip()
                except Exception:
                    continue
                if not line_str:
                    continue

                # parse NMEA sentence
                try:
                    msg = pynmea2.parse(line_str)
                except pynmea2.nmea.ChecksumError:
                    continue  # invalid checksum
                except pynmea2.ParseError:
                    continue  # unknown sentence

                pos = None
                timestamp = None

                # Messages with fix: GGA (GPS Fix Data), RMC (Recommended Minimum)
                if isinstance(msg, pynmea2.types.talker.GGA):
                    if msg.lat and msg.lon:
                        lat = _nmea_to_decimal(msg.lat, msg.lat_dir)
                        lon = _nmea_to_decimal(msg.lon, msg.lon_dir)
                        alt = float(msg.alt) if msg.alt not in (None, '') else None
                        timestamp = _nmea_time_to_epoch(msg.timestamp)
                        pos = Position(lat, lon, alt, timestamp)
                elif isinstance(msg, pynmea2.types.talker.RMC):
                    if msg.lat and msg.lon and msg.status == 'A':  # 'A' = active (valid)
                        lat = _nmea_to_decimal(msg.lat, msg.lat_dir)
                        lon = _nmea_to_decimal(msg.lon, msg.lon_dir)
                        alt = None
                        timestamp = _nmea_datetime_to_epoch(msg.datestamp, msg.timestamp)
                        pos = Position(lat, lon, alt, timestamp)

                if pos:
                    with self._lock:
                        self._last_position = pos
                        self._history.append(pos)
                    if self._callback:
                        try:
                            self._callback(pos)
                        except Exception as cb_e:
                            print(f"[GPSTracker] callback error: {cb_e}")

            except Exception as e:
                print(f"[GPSTracker] read loop error: {e}")
                time.sleep(0.5)

    def get_last(self) -> Optional[Position]:
        with self._lock:
            return self._last_position

    def get_history(self) -> List[Position]:
        with self._lock:
            return list(self._history)

    def save_history_csv(self, path: str):
        """Saves position history to a CSV file (lat, lon, alt, timestamp)."""
        data = self.get_history()
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["lat", "lon", "alt", "timestamp"])
            for p in data:
                writer.writerow([p.lat, p.lon, p.alt, p.timestamp])

    def geofence_check_circle(self, center: Tuple[float, float], radius_m: float) -> Optional[bool]:
        """
        Checks if the last position is inside a circular geofence.
        center=(lat, lon), radius in meters.
        Returns True (inside), False (outside), or None (no position).
        """
        last = self.get_last()
        if last is None:
            return None
        d = haversine_distance_m((last.lat, last.lon), center)
        return d <= radius_m


# --- Utility functions below ---

def _nmea_to_decimal(coord_str: str, direction: str) -> float:
    """
    Converts NMEA coordinate (ddmm.mmmm or dddmm.mmmm) to decimal degrees.
    coord_str: string like "4916.45" (49 deg 16.45')
    direction: 'N', 'S', 'E', or 'W'
    """
    if not coord_str:
        raise ValueError("coord_str is empty")
    dot_pos = coord_str.find('.')
    if dot_pos == -1:
        deg_len = 2 if len(coord_str) <= 4 else len(coord_str) - 4
    else:
        deg_len = 2 if dot_pos <= 4 else dot_pos - 2

    degrees = float(coord_str[:deg_len])
    minutes = float(coord_str[deg_len:])
    dec = degrees + minutes / 60.0
    if direction in ('S', 'W'):
        dec = -dec
    return dec


def _nmea_time_to_epoch(nmea_time) -> Optional[float]:
    """
    Converts NMEA time (hh:mm:ss) to epoch seconds assuming today's date.
    Returns None if nmea_time is None.
    """
    if nmea_time is None:
        return None
    try:
        t = nmea_time
        now = time.localtime()
        epoch = time.mktime((now.tm_year, now.tm_mon, now.tm_mday,
                             t.hour, t.minute, t.second,
                             now.tm_wday, now.tm_yday, now.tm_isdst))
        return epoch
    except Exception:
        return None


def _nmea_datetime_to_epoch(datestamp, timestamp) -> Optional[float]:
    """
    Converts NMEA date (datetime.date) and time (datetime.time) from RMC to epoch.
    """
    if datestamp is None or timestamp is None:
        return _nmea_time_to_epoch(timestamp)
    try:
        dt = datestamp
        t = timestamp
        epoch = time.mktime((dt.year, dt.month, dt.day, t.hour, t.minute, t.second, 0, 0, -1))
        return epoch
    except Exception:
        return None


def haversine_distance_m(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """
    Haversine distance between two (lat, lon) points in meters.
    """
    import math
    lat1, lon1 = p1
    lat2, lon2 = p2
    R = 6371000.0  # Earth's mean radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * (math.sin(dlambda / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# Demo (not for production)
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GPSTracker demo - read NMEA from serial and print positions")
    parser.add_argument("--port", required=True, help="serial port (e.g. COM3 or /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=9600)
    args = parser.parse_args()

    
