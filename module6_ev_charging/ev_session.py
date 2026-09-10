"""
ParkPilot — Module 6: EV Charging Session Manager
Manages electric vehicle charging sessions: start, stop, billing, and status.

Charger Types:
    Type 1 (AC Slow)  : 3.3 kW  — Rs.8/kWh
    Type 2 (AC Fast)  : 22 kW   — Rs.12/kWh
    CCS2  (DC Fast)   : 60 kW   — Rs.18/kWh

Usage:
    from module6_ev_charging.ev_session import EVSessionManager
    mgr = EVSessionManager()
    session = mgr.start_session("KA05AB1234", "EV-CHARGER-01", "type2")
    mgr.stop_session(session["id"], kwh_consumed=15.5)
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger, log_event
from utils.config import settings

logger = get_logger("parkpilot.module6.ev_session")

DB_PATH = "database/parkpilot.db"

# ── Charger Type Rates ────────────────────────────────────────────────────────
CHARGER_RATES = {
    "type1": {"name": "AC Slow (3.3 kW)", "kw": 3.3, "rate": settings.EV_TYPE1_RATE},
    "type2": {"name": "AC Fast (22 kW)",  "kw": 22.0, "rate": settings.EV_TYPE2_RATE},
    "ccs2":  {"name": "DC Fast (60 kW)",  "kw": 60.0, "rate": settings.EV_CCS2_RATE},
}


class EVSessionManager:
    """
    Manages the full lifecycle of EV charging sessions.

    Operations:
        start_session()  — Create new charging session, mark charger OCCUPIED
        update_kwh()     — Real-time kWh update from power meter
        stop_session()   — End session, calculate bill, mark charger FREE
        get_status()     — Get current session and charger status
        get_all_active() — List all active sessions
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else ".", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ev_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT,
                charger_id TEXT NOT NULL,
                charger_type TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                kwh_consumed REAL DEFAULT 0.0,
                fee_amount REAL DEFAULT 0.0,
                rate_per_kwh REAL,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ev_chargers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                charger_id TEXT UNIQUE NOT NULL,
                charger_type TEXT,
                location TEXT,
                status TEXT DEFAULT 'available',
                current_session_id INTEGER,
                power_kw REAL,
                last_updated TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ev_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT,
                user_id INTEGER,
                charger_type TEXT,
                joined_at TEXT DEFAULT (datetime('now')),
                notified INTEGER DEFAULT 0,
                position INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── Session Operations ────────────────────────────────────────────────────

    def start_session(
        self,
        plate_number: str,
        charger_id: str,
        charger_type: str = "type2"
    ) -> dict:
        """
        Start a new EV charging session.

        Args:
            plate_number: Vehicle license plate
            charger_id: Charger unit ID (e.g., "EV-CHARGER-01")
            charger_type: 'type1', 'type2', or 'ccs2'

        Returns:
            Session dict or error dict
        """
        if charger_type not in CHARGER_RATES:
            return {"error": f"Unknown charger type: {charger_type}"}

        conn = self._get_conn()

        # Check if charger is available
        charger = conn.execute(
            "SELECT * FROM ev_chargers WHERE charger_id=?", (charger_id,)
        ).fetchone()

        if charger and charger["status"] == "occupied":
            conn.close()
            return {"error": f"Charger {charger_id} is already occupied"}

        if charger and charger["status"] == "fault":
            conn.close()
            return {"error": f"Charger {charger_id} is out of service (fault)"}

        rate = CHARGER_RATES[charger_type]["rate"]
        start_time = datetime.utcnow().isoformat()

        cur = conn.execute("""
            INSERT INTO ev_sessions (plate_number, charger_id, charger_type, start_time, rate_per_kwh, status)
            VALUES (?, ?, ?, ?, ?, 'active')
        """, (plate_number, charger_id, charger_type, start_time, rate))
        session_id = cur.lastrowid

        # Mark charger as occupied
        conn.execute("""
            INSERT OR REPLACE INTO ev_chargers
                (charger_id, charger_type, status, current_session_id, last_updated)
            VALUES (?, ?, 'occupied', ?, datetime('now'))
        """, (charger_id, charger_type, session_id))

        conn.commit()
        conn.close()

        session = {
            "id": session_id,
            "plate_number": plate_number,
            "charger_id": charger_id,
            "charger_type": charger_type,
            "charger_name": CHARGER_RATES[charger_type]["name"],
            "rate_per_kwh": rate,
            "start_time": start_time,
            "status": "active"
        }

        log_event("EV_CHARGING", "SESSION_START",
                  f"EV charging started | Plate: {plate_number} | Charger: {charger_id}",
                  extra=session)
        logger.info(f"EV session {session_id} started | {plate_number} @ {charger_id}")
        return session

    def update_kwh(self, session_id: int, kwh_consumed: float):
        """Real-time kWh update from power meter (called periodically by charger IoT)."""
        conn = self._get_conn()
        session = conn.execute(
            "SELECT * FROM ev_sessions WHERE id=?", (session_id,)
        ).fetchone()

        if not session or session["status"] != "active":
            conn.close()
            return {"error": "Session not found or inactive"}

        rate = session["rate_per_kwh"] or 0
        estimated_fee = round(kwh_consumed * rate, 2)

        conn.execute("""
            UPDATE ev_sessions SET kwh_consumed=?, fee_amount=? WHERE id=?
        """, (kwh_consumed, estimated_fee, session_id))
        conn.commit()
        conn.close()

        return {
            "session_id": session_id,
            "kwh_consumed": kwh_consumed,
            "estimated_fee": estimated_fee
        }

    def stop_session(
        self,
        session_id: int,
        kwh_consumed: float = None
    ) -> dict:
        """
        End a charging session and calculate final bill.

        Args:
            session_id: Session ID to stop
            kwh_consumed: Final kWh reading (if None, uses last recorded value)

        Returns:
            Completed session dict with final billing
        """
        conn = self._get_conn()
        session = conn.execute(
            "SELECT * FROM ev_sessions WHERE id=?", (session_id,)
        ).fetchone()

        if not session:
            conn.close()
            return {"error": f"Session {session_id} not found"}

        if session["status"] != "active":
            conn.close()
            return {"error": f"Session {session_id} is not active"}

        end_time = datetime.utcnow()
        kwh = kwh_consumed if kwh_consumed is not None else session["kwh_consumed"]
        rate = session["rate_per_kwh"] or CHARGER_RATES["type2"]["rate"]
        fee = round(kwh * rate, 2)

        start_dt = datetime.fromisoformat(session["start_time"])
        duration_min = (end_time - start_dt).total_seconds() / 60

        conn.execute("""
            UPDATE ev_sessions
            SET end_time=?, kwh_consumed=?, fee_amount=?, status='completed'
            WHERE id=?
        """, (end_time.isoformat(), kwh, fee, session_id))

        # Free up charger
        charger_id = session["charger_id"]
        conn.execute("""
            UPDATE ev_chargers
            SET status='available', current_session_id=NULL, last_updated=datetime('now')
            WHERE charger_id=?
        """, (charger_id,))

        conn.commit()
        conn.close()

        result = {
            "session_id": session_id,
            "plate_number": session["plate_number"],
            "charger_id": charger_id,
            "charger_type": session["charger_type"],
            "start_time": session["start_time"],
            "end_time": end_time.isoformat(),
            "duration_minutes": round(duration_min, 1),
            "kwh_consumed": kwh,
            "rate_per_kwh": rate,
            "fee_amount": fee,
            "status": "completed"
        }

        log_event("EV_CHARGING", "SESSION_END",
                  f"EV session completed | {session['plate_number']} | "
                  f"{kwh} kWh | ₹{fee}",
                  extra=result)
        logger.info(f"EV session {session_id} completed | {kwh} kWh | ₹{fee}")

        # Notify next in queue
        self._notify_queue(session["charger_type"])

        return result

    def get_session(self, session_id: int) -> dict:
        """Get session details by ID."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM ev_sessions WHERE id=?", (session_id,)
        ).fetchone()
        conn.close()
        return dict(row) if row else {}

    def get_active_sessions(self) -> list:
        """Get all currently active charging sessions."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM ev_sessions WHERE status='active'"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_charger_status(self, charger_id: str = None) -> list:
        """Get status of all chargers, or a specific one."""
        conn = self._get_conn()
        if charger_id:
            rows = conn.execute(
                "SELECT * FROM ev_chargers WHERE charger_id=?", (charger_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM ev_chargers").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def report_fault(self, charger_id: str, fault_description: str = ""):
        """Mark a charger as faulty (maintenance required)."""
        conn = self._get_conn()
        conn.execute("""
            UPDATE ev_chargers
            SET status='fault', last_updated=datetime('now')
            WHERE charger_id=?
        """, (charger_id,))
        conn.commit()
        conn.close()

        log_event("EV_CHARGING", "CHARGER_FAULT",
                  f"Charger {charger_id} reported fault: {fault_description}")
        logger.warning(f"Charger fault reported: {charger_id}")

    # ── Queue Management ──────────────────────────────────────────────────────

    def join_queue(self, plate_number: str, charger_type: str, user_id: int = None) -> dict:
        """Add a vehicle to the EV charging queue."""
        conn = self._get_conn()
        pos = conn.execute(
            "SELECT COUNT(*)+1 as pos FROM ev_queue WHERE charger_type=? AND notified=0",
            (charger_type,)
        ).fetchone()["pos"]

        conn.execute("""
            INSERT INTO ev_queue (plate_number, user_id, charger_type, position)
            VALUES (?, ?, ?, ?)
        """, (plate_number, user_id, charger_type, pos))
        conn.commit()
        conn.close()

        logger.info(f"Vehicle {plate_number} joined EV queue | Type: {charger_type} | Position: {pos}")
        return {"plate_number": plate_number, "charger_type": charger_type, "position": pos}

    def _notify_queue(self, charger_type: str):
        """Notify the next vehicle in queue when a charger becomes free."""
        conn = self._get_conn()
        next_in_queue = conn.execute("""
            SELECT * FROM ev_queue
            WHERE charger_type=? AND notified=0
            ORDER BY joined_at ASC LIMIT 1
        """, (charger_type,)).fetchone()

        if next_in_queue:
            conn.execute(
                "UPDATE ev_queue SET notified=1 WHERE id=?",
                (next_in_queue["id"],)
            )
            conn.commit()
            logger.info(
                f"Notified next in EV queue: {next_in_queue['plate_number']} | "
                f"Charger type: {charger_type}"
            )
        conn.close()


if __name__ == "__main__":
    mgr = EVSessionManager()

    # Demo
    print("Starting EV session demo...")
    session = mgr.start_session("KA05AB1234", "EV-CHARGER-01", "type2")
    print(f"Session started: {session}")

    # Simulate charging update
    mgr.update_kwh(session["id"], kwh_consumed=5.0)

    # Stop session
    result = mgr.stop_session(session["id"], kwh_consumed=15.5)
    print(f"\nSession completed: {result}")
    print(f"Total bill: ₹{result['fee_amount']:.2f}")
