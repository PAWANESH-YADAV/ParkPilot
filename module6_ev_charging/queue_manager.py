"""
ParkPilot — Module 6: EV Smart Queue Manager
Manages the waiting queue when all EV slots are occupied.
Provides estimated wait times and notifies users when a slot is free.
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger, log_event
from utils.notification import send_sms, send_push_notification
from utils.config import settings

logger = get_logger("parkpilot.module6.queue_manager")
DB_PATH = "database/parkpilot.db"

# Average charging duration estimates by charger type (minutes)
AVG_CHARGING_DURATION = {
    "type1": 180,   # AC Slow ~3 hours
    "type2": 60,    # AC Fast ~1 hour
    "ccs2":  30,    # DC Fast ~30 min
}


class EVQueueManager:
    """
    Smart queue manager for EV charging slots.

    Features:
        - Join/leave queue for specific charger type
        - Estimated wait time calculation
        - Auto-notification via SMS + push when slot available
        - Fair FIFO ordering with position tracking
        - Auto-expiry of stale queue entries
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else ".", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ev_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT NOT NULL,
                user_id INTEGER,
                phone TEXT,
                fcm_token TEXT,
                charger_type TEXT NOT NULL,
                joined_at TEXT DEFAULT (datetime('now')),
                notified INTEGER DEFAULT 0,
                notified_at TEXT,
                expired INTEGER DEFAULT 0,
                position INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── Queue Operations ──────────────────────────────────────────────────────

    def join(
        self,
        plate_number: str,
        charger_type: str,
        user_id: int = None,
        phone: str = None,
        fcm_token: str = None
    ) -> dict:
        """
        Add a vehicle to the charging queue.

        Args:
            plate_number: Vehicle license plate
            charger_type: 'type1', 'type2', or 'ccs2'
            user_id: User account ID (optional)
            phone: Phone for SMS notification
            fcm_token: Firebase push token

        Returns:
            Queue entry dict with position and wait estimate
        """
        # Check if already in queue
        conn = self._get_conn()
        existing = conn.execute(
            "SELECT * FROM ev_queue WHERE plate_number=? AND charger_type=? AND notified=0 AND expired=0",
            (plate_number, charger_type)
        ).fetchone()

        if existing:
            conn.close()
            pos = existing["position"]
            wait = self._estimate_wait(charger_type, pos)
            return {
                "already_queued": True,
                "position": pos,
                "estimated_wait_minutes": wait,
                "plate_number": plate_number
            }

        # Get current queue length
        pos = conn.execute(
            "SELECT COUNT(*)+1 as cnt FROM ev_queue WHERE charger_type=? AND notified=0 AND expired=0",
            (charger_type,)
        ).fetchone()["cnt"]

        conn.execute("""
            INSERT INTO ev_queue (plate_number, user_id, phone, fcm_token, charger_type, position)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (plate_number, user_id, phone, fcm_token, charger_type, pos))
        conn.commit()
        conn.close()

        wait = self._estimate_wait(charger_type, pos)

        log_event("EV_QUEUE", "JOIN",
                  f"{plate_number} joined {charger_type} queue at position {pos}")
        logger.info(f"Queue join: {plate_number} | Type: {charger_type} | Position: {pos} | ETA: {wait}min")

        return {
            "plate_number": plate_number,
            "charger_type": charger_type,
            "position": pos,
            "estimated_wait_minutes": wait,
            "message": f"You are #{pos} in queue. Estimated wait: {wait} minutes."
        }

    def leave(self, plate_number: str, charger_type: str) -> bool:
        """Remove a vehicle from the queue."""
        conn = self._get_conn()
        conn.execute(
            "UPDATE ev_queue SET expired=1 WHERE plate_number=? AND charger_type=? AND expired=0",
            (plate_number, charger_type)
        )
        conn.commit()
        self._reorder_positions(conn, charger_type)
        conn.commit()
        conn.close()
        logger.info(f"Queue leave: {plate_number} | Type: {charger_type}")
        return True

    def notify_next(self, charger_type: str) -> dict | None:
        """
        Notify the next person in queue that a charger is available.
        Called automatically when a charging session ends.

        Returns:
            Next queue entry dict if someone was notified, else None
        """
        conn = self._get_conn()
        next_entry = conn.execute("""
            SELECT * FROM ev_queue
            WHERE charger_type=? AND notified=0 AND expired=0
            ORDER BY joined_at ASC LIMIT 1
        """, (charger_type,)).fetchone()

        if not next_entry:
            conn.close()
            logger.info(f"EV queue empty for charger type: {charger_type}")
            return None

        entry = dict(next_entry)

        # Mark as notified
        conn.execute(
            "UPDATE ev_queue SET notified=1, notified_at=datetime('now') WHERE id=?",
            (entry["id"],)
        )
        conn.commit()
        conn.close()

        # Send notifications
        msg = (
            f"✅ ParkPilot EV: A {charger_type.upper()} charger is now available! "
            f"You are next in queue. Please proceed to the charging station within 10 minutes."
        )

        if entry.get("phone"):
            send_sms(entry["phone"], msg)

        if entry.get("fcm_token"):
            send_push_notification(
                entry["fcm_token"],
                title="⚡ EV Charger Available!",
                body=f"A {charger_type} charger is ready for you.",
                data={"charger_type": charger_type, "action": "proceed_to_charger"}
            )

        log_event("EV_QUEUE", "NOTIFIED",
                  f"Notified {entry['plate_number']} for {charger_type} charger")
        logger.info(f"Queue notified: {entry['plate_number']} for {charger_type}")
        return entry

    def get_queue(self, charger_type: str = None) -> list:
        """Get current queue entries."""
        conn = self._get_conn()
        if charger_type:
            rows = conn.execute("""
                SELECT * FROM ev_queue
                WHERE charger_type=? AND notified=0 AND expired=0
                ORDER BY joined_at ASC
            """, (charger_type,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM ev_queue
                WHERE notified=0 AND expired=0
                ORDER BY charger_type, joined_at ASC
            """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_position(self, plate_number: str, charger_type: str) -> dict:
        """Get current queue position for a vehicle."""
        conn = self._get_conn()
        entry = conn.execute("""
            SELECT * FROM ev_queue
            WHERE plate_number=? AND charger_type=? AND notified=0 AND expired=0
        """, (plate_number, charger_type)).fetchone()
        conn.close()

        if not entry:
            return {"in_queue": False}

        pos = entry["position"]
        wait = self._estimate_wait(charger_type, pos)
        return {
            "in_queue": True,
            "position": pos,
            "estimated_wait_minutes": wait,
            "joined_at": entry["joined_at"]
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _estimate_wait(self, charger_type: str, position: int) -> int:
        """
        Estimate wait time in minutes.
        Based on average session duration × position in queue.
        """
        avg_duration = AVG_CHARGING_DURATION.get(charger_type, 60)
        # Assume there might be multiple chargers of same type
        chargers_of_type = self._count_available_chargers(charger_type)
        if chargers_of_type == 0:
            chargers_of_type = 1
        wait = int((position / chargers_of_type) * avg_duration)
        return max(wait, 5)  # Minimum 5 min estimate

    def _count_available_chargers(self, charger_type: str) -> int:
        """Count chargers of given type (including occupied ones being waited for)."""
        try:
            conn = sqlite3.connect(self.db_path)
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM ev_chargers WHERE charger_type=?",
                (charger_type,)
            ).fetchone()
            conn.close()
            return row[0] if row else 1
        except Exception:
            return 1

    def _reorder_positions(self, conn: sqlite3.Connection, charger_type: str):
        """Re-number queue positions after a removal."""
        rows = conn.execute("""
            SELECT id FROM ev_queue
            WHERE charger_type=? AND notified=0 AND expired=0
            ORDER BY joined_at ASC
        """, (charger_type,)).fetchall()
        for idx, row in enumerate(rows, start=1):
            conn.execute("UPDATE ev_queue SET position=? WHERE id=?", (idx, row[0]))


if __name__ == "__main__":
    qmgr = EVQueueManager()

    # Demo
    print("EV Queue Manager Demo")
    result1 = qmgr.join("KA05AB1234", "ccs2", phone="+919876543210")
    result2 = qmgr.join("MH01CD5678", "ccs2", phone="+919876543211")
    result3 = qmgr.join("DL4CAF9876", "type2")

    print(f"Queue status:")
    for entry in qmgr.get_queue():
        print(f"  {entry['plate_number']} | Type: {entry['charger_type']} | Pos: {entry['position']}")

    print(f"\nNotifying next in ccs2 queue...")
    notified = qmgr.notify_next("ccs2")
    if notified:
        print(f"Notified: {notified['plate_number']}")
