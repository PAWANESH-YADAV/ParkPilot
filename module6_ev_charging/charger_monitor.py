"""
ParkPilot — Module 6: EV Charger Health Monitor
Monitors charger hardware status using IoT sensor data.
Detects faults, overheating, and power anomalies.
Triggers maintenance alerts automatically.

In production, replace the mock IoT reader with your actual
MQTT/Modbus/RS485 charger communication protocol.
"""

import sys
import os
import time
import random
import threading
import sqlite3
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger, log_event
from utils.notification import send_push_notification
from utils.config import settings

logger = get_logger("parkpilot.module6.charger_monitor")

DB_PATH = "database/parkpilot.db"

# ── Charger Health Thresholds ─────────────────────────────────────────────────
TEMP_WARNING_C = 55.0       # Warning above 55°C
TEMP_CRITICAL_C = 70.0      # Fault above 70°C
VOLTAGE_MIN = 195.0         # Min acceptable voltage (220V ±25V)
VOLTAGE_MAX = 245.0
CURRENT_MAX_A = {
    "type1": 16.0,
    "type2": 32.0,
    "ccs2": 125.0
}


class ChargerHealthMonitor:
    """
    Monitors EV charger hardware health in real-time.

    In production, integrate with:
        - OCPP (Open Charge Point Protocol) over WebSocket
        - Modbus TCP/RTU for industrial chargers
        - MQTT for IoT-enabled chargers
        - HTTP polling of charger management API

    For this demo, a mock data generator simulates sensor readings.

    Args:
        poll_interval_seconds: How often to poll charger status
        db_path: SQLite database path
    """

    def __init__(
        self,
        poll_interval_seconds: int = 30,
        db_path: str = DB_PATH
    ):
        self.poll_interval = poll_interval_seconds
        self.db_path = db_path
        self.running = False
        self._thread = None
        self.charger_states: dict[str, dict] = {}
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else ".", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS charger_health_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                charger_id TEXT,
                temperature_c REAL,
                voltage_v REAL,
                current_a REAL,
                power_kw REAL,
                status TEXT,
                fault_code TEXT,
                recorded_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        conn.close()

    def start(self):
        """Start background monitoring loop."""
        self.running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info(f"Charger monitor started | Poll interval: {self.poll_interval}s")

    def stop(self):
        """Stop monitoring loop."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Charger monitor stopped")

    def _monitor_loop(self):
        """Background loop — polls all chargers periodically."""
        while self.running:
            chargers = self._get_all_chargers()
            for charger in chargers:
                self._poll_charger(charger)
            time.sleep(self.poll_interval)

    def _get_all_chargers(self) -> list:
        """Get all charger records from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM ev_chargers").fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def _poll_charger(self, charger: dict):
        """
        Poll a single charger for health metrics.

        In production, replace this with actual OCPP/MQTT/Modbus calls.
        """
        charger_id = charger["charger_id"]
        charger_type = charger.get("charger_type", "type2")

        # ── Mock IoT sensor reading ────────────────────────────────────────
        # In production: call OCPP.sendRequest() or read Modbus registers
        reading = self._mock_sensor_reading(charger_id, charger_type,
                                             charger.get("status", "available"))

        # ── Update in-memory state ─────────────────────────────────────────
        self.charger_states[charger_id] = {**charger, **reading}

        # ── Check thresholds ───────────────────────────────────────────────
        fault = self._check_faults(charger_id, charger_type, reading)

        # ── Log to database ────────────────────────────────────────────────
        self._log_reading(charger_id, reading, fault)

        if fault:
            self._handle_fault(charger_id, fault)

    def _mock_sensor_reading(self, charger_id: str, charger_type: str, status: str) -> dict:
        """Generate mock sensor data for demo purposes."""
        is_active = status == "occupied"

        # Simulate realistic values
        base_temp = 35.0 + (20.0 if is_active else 0.0)
        temperature = base_temp + random.gauss(0, 3)

        # Occasionally simulate a fault (1% chance)
        if random.random() < 0.01:
            temperature = TEMP_CRITICAL_C + random.uniform(0, 10)

        max_current = CURRENT_MAX_A.get(charger_type, 32.0)
        current = max_current * 0.85 if is_active else 0.0
        voltage = random.gauss(230.0, 5.0)
        power = round(voltage * current / 1000, 2) if is_active else 0.0

        return {
            "temperature_c": round(temperature, 1),
            "voltage_v": round(voltage, 1),
            "current_a": round(current, 1),
            "power_kw": power,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _check_faults(self, charger_id: str, charger_type: str, reading: dict) -> str | None:
        """
        Check sensor readings against safety thresholds.

        Returns:
            Fault code string, or None if healthy
        """
        temp = reading["temperature_c"]
        voltage = reading["voltage_v"]
        current = reading["current_a"]

        if temp >= TEMP_CRITICAL_C:
            return f"OVERHEATING (T={temp:.1f}°C)"

        if not (VOLTAGE_MIN <= voltage <= VOLTAGE_MAX):
            return f"VOLTAGE_ANOMALY (V={voltage:.1f}V)"

        max_current = CURRENT_MAX_A.get(charger_type, 32.0)
        if current > max_current * 1.1:  # 10% over max
            return f"OVERCURRENT (I={current:.1f}A)"

        if temp >= TEMP_WARNING_C:
            logger.warning(f"Charger {charger_id}: Temperature warning ({temp:.1f}°C)")

        return None

    def _handle_fault(self, charger_id: str, fault_code: str):
        """Handle a detected fault — mark charger out of service and alert."""
        logger.error(f"⚡ CHARGER FAULT | {charger_id} | {fault_code}")

        # Mark as fault in database
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE ev_chargers SET status='fault', last_updated=datetime('now') WHERE charger_id=?",
            (charger_id,)
        )
        conn.commit()
        conn.close()

        log_event("EV_CHARGING", "CHARGER_FAULT",
                  f"Charger {charger_id}: {fault_code}")

        # Send push notification to maintenance team
        maintenance_token = os.getenv("MAINTENANCE_FCM_TOKEN", "")
        if maintenance_token:
            send_push_notification(
                maintenance_token,
                title=f"⚡ Charger Fault — {charger_id}",
                body=fault_code,
                data={"charger_id": charger_id, "fault": fault_code}
            )

    def _log_reading(self, charger_id: str, reading: dict, fault: str = None):
        """Log health reading to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT INTO charger_health_log
                    (charger_id, temperature_c, voltage_v, current_a, power_kw, status, fault_code)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                charger_id,
                reading["temperature_c"],
                reading["voltage_v"],
                reading["current_a"],
                reading["power_kw"],
                "fault" if fault else "ok",
                fault or ""
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Health log DB error: {e}")

    def get_charger_state(self, charger_id: str) -> dict:
        """Get the latest state of a charger."""
        return self.charger_states.get(charger_id, {})

    def get_all_states(self) -> dict:
        """Get latest state of all monitored chargers."""
        return self.charger_states.copy()

    def get_health_history(self, charger_id: str, limit: int = 50) -> list:
        """Fetch health log history for a charger."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM charger_health_log
                WHERE charger_id=?
                ORDER BY recorded_at DESC LIMIT ?
            """, (charger_id, limit)).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Health history query error: {e}")
            return []


if __name__ == "__main__":
    monitor = ChargerHealthMonitor(poll_interval_seconds=10)
    monitor.start()

    print("EV Charger Monitor running (Ctrl+C to stop)...")
    try:
        while True:
            states = monitor.get_all_states()
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Charger States:")
            for cid, state in states.items():
                print(f"  {cid}: T={state.get('temperature_c', 'N/A')}°C "
                      f"V={state.get('voltage_v', 'N/A')}V "
                      f"P={state.get('power_kw', 'N/A')}kW")
            time.sleep(15)
    except KeyboardInterrupt:
        monitor.stop()
        print("Monitor stopped")
