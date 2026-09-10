"""
ParkPilot — Module 3: Alert System
Handles all security alert delivery — on-screen display, sound,
push notification, SMS, and video clip saving.

Called by both activity_monitor.py and loitering_detection.py.
"""

import os
import sys
import cv2
import threading
import sqlite3
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger, log_event
from utils.notification import send_security_alert, send_push_notification
from utils.config import settings

logger = get_logger("parkpilot.module3.alert_system")

CLIPS_DIR = settings.CLIPS_SAVE_PATH
os.makedirs(CLIPS_DIR, exist_ok=True)

# ── Alert severity colors (BGR) ───────────────────────────────────────────────
SEVERITY_COLORS = {
    "HIGH":   (0, 0, 220),      # Dark red
    "MEDIUM": (0, 100, 255),    # Orange
    "LOW":    (0, 165, 255),    # Yellow-orange
    "INFO":   (200, 200, 0),    # Cyan
}

# ── Event type → human-readable label ────────────────────────────────────────
EVENT_LABELS = {
    "loitering":    "🚶 Loitering Detected",
    "vandalism":    "🔨 Vandalism Alert",
    "unauthorized": "🚫 Unauthorized Access",
    "accident":     "💥 Vehicle Accident",
    "other":        "⚠ Suspicious Activity",
}


class AlertSystem:
    """
    Centralized alert management system.

    Features:
        - On-screen color-coded alert overlay with countdown
        - Sound alarm (beep / external audio)
        - Push notification via FCM
        - SMS to security guard
        - Event stored in SQLite database
        - Video clip saved for review

    Usage:
        alert = AlertSystem(db_path="database/parkpilot.db")
        alert.trigger(event_type="loitering", camera_id="CAM01",
                      location="Zone B", clip_frames=[...])
    """

    def __init__(
        self,
        db_path: str = "database/parkpilot.db",
        security_phone: str = None,
        security_email: str = None,
        security_fcm_token: str = None
    ):
        self.db_path = db_path
        self.security_phone = security_phone or os.getenv("SECURITY_PHONE", "")
        self.security_email = security_email or os.getenv("SECURITY_EMAIL", "")
        self.security_fcm_token = security_fcm_token or os.getenv("SECURITY_FCM_TOKEN", "")

        # Active on-screen alerts
        self.active_alerts: list[dict] = []
        self.alert_lock = threading.Lock()

        # Rate limiting — avoid spamming same alert type
        self.last_alert_time: dict[str, datetime] = {}
        self.alert_cooldown_seconds = 30

        self._init_db()
        logger.info("AlertSystem initialized")

    def _init_db(self):
        """Initialize SQLite security_events table if not exists."""
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else ".", exist_ok=True)
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    timestamp TEXT,
                    camera_id TEXT,
                    location_zone TEXT,
                    clip_path TEXT,
                    snapshot_path TEXT,
                    resolved INTEGER DEFAULT 0,
                    notified INTEGER DEFAULT 0,
                    notes TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"DB init failed: {e}")

    # ── Main Trigger ──────────────────────────────────────────────────────────

    def trigger(
        self,
        event_type: str,
        camera_id: str,
        location: str = "Unknown",
        severity: str = "MEDIUM",
        clip_frames: list = None,
        snapshot: "np.ndarray" = None,
        extra: dict = None
    ) -> dict:
        """
        Trigger a security alert.

        Args:
            event_type: 'loitering', 'vandalism', 'unauthorized', 'accident'
            camera_id: Camera identifier
            location: Zone/location description
            severity: 'HIGH', 'MEDIUM', 'LOW'
            clip_frames: List of frames to save as video clip
            snapshot: Single frame snapshot
            extra: Extra data dict

        Returns:
            Event record dict
        """
        # ── Rate limiting ──────────────────────────────────────────────────
        key = f"{event_type}_{camera_id}"
        now = datetime.utcnow()
        last = self.last_alert_time.get(key)
        if last and (now - last).total_seconds() < self.alert_cooldown_seconds:
            logger.debug(f"Alert rate-limited: {key}")
            return {}

        self.last_alert_time[key] = now
        ts = now.isoformat()

        logger.warning(
            f"🚨 SECURITY ALERT | Type: {event_type.upper()} | "
            f"Camera: {camera_id} | Location: {location} | Severity: {severity}"
        )

        event = {
            "event_type": event_type,
            "timestamp": ts,
            "camera_id": camera_id,
            "location": location,
            "severity": severity,
            "clip_path": "",
            "snapshot_path": "",
        }
        if extra:
            event.update(extra)

        # ── Save snapshot ──────────────────────────────────────────────────
        if snapshot is not None:
            snap_path = self._save_snapshot(snapshot, event_type, ts)
            event["snapshot_path"] = snap_path

        # ── Save clip ─────────────────────────────────────────────────────
        if clip_frames:
            clip_path = self._save_clip(clip_frames, event_type, ts)
            event["clip_path"] = clip_path

        # ── Store in database ─────────────────────────────────────────────
        event_id = self._store_event(event)
        event["id"] = event_id

        # ── Add to on-screen alert queue ──────────────────────────────────
        display_alert = {
            **event,
            "display_until": time.time() + 10,  # Show for 10 seconds
            "label": EVENT_LABELS.get(event_type, "⚠ Alert"),
            "color": SEVERITY_COLORS.get(severity, SEVERITY_COLORS["MEDIUM"])
        }
        with self.alert_lock:
            self.active_alerts.append(display_alert)
            # Keep max 5 active alerts on screen
            self.active_alerts = self.active_alerts[-5:]

        # ── Send notifications in background thread ────────────────────────
        threading.Thread(
            target=self._send_notifications,
            args=(event,),
            daemon=True
        ).start()

        log_event("ALERT_SYSTEM", event_type.upper(), f"{severity} alert triggered at {location}")
        return event

    # ── On-Screen Overlay ─────────────────────────────────────────────────────

    def draw_alerts(self, frame: "np.ndarray") -> "np.ndarray":
        """
        Draw all active on-screen alerts on a frame.
        Alerts auto-expire after their display duration.

        Args:
            frame: Input frame to annotate

        Returns:
            Annotated frame
        """
        import numpy as np
        now = time.time()
        with self.alert_lock:
            # Remove expired alerts
            self.active_alerts = [a for a in self.active_alerts if a["display_until"] > now]

            if not self.active_alerts:
                return frame

            # Draw alert panel
            h, w = frame.shape[:2]
            panel_h = min(40 + len(self.active_alerts) * 35, 200)
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, panel_h), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

            # Blinking border for HIGH severity
            high_alerts = [a for a in self.active_alerts if a.get("severity") == "HIGH"]
            if high_alerts and int(now * 2) % 2 == 0:
                cv2.rectangle(frame, (0, 0), (w, panel_h), (0, 0, 255), 3)

            y = 28
            for alert in self.active_alerts:
                color = alert.get("color", (0, 100, 255))
                label = alert.get("label", "ALERT")
                cam = alert.get("camera_id", "")
                loc = alert.get("location", "")
                ts = alert.get("timestamp", "")[:19]
                remaining = int(alert["display_until"] - now)

                text = f"  {label} | {cam} | {loc} | {ts} [{remaining}s]"
                cv2.putText(frame, text, (5, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1, cv2.LINE_AA)
                y += 30

        return frame

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save_snapshot(self, frame: "np.ndarray", event_type: str, ts: str) -> str:
        clean_ts = ts.replace(":", "").replace(".", "")[:15]
        path = os.path.join(CLIPS_DIR, f"snap_{event_type}_{clean_ts}.jpg")
        cv2.imwrite(path, frame)
        return path

    def _save_clip(self, frames: list, event_type: str, ts: str, fps: float = 10.0) -> str:
        if not frames:
            return ""
        clean_ts = ts.replace(":", "").replace(".", "")[:15]
        path = os.path.join(CLIPS_DIR, f"clip_{event_type}_{clean_ts}.mp4")
        h, w = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(path, fourcc, fps, (w, h))
        for f in frames:
            writer.write(f)
        writer.release()
        logger.info(f"Clip saved: {path}")
        return path

    def _store_event(self, event: dict) -> int:
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.execute("""
                INSERT INTO security_events
                    (event_type, timestamp, camera_id, location_zone, clip_path, snapshot_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event.get("event_type"),
                event.get("timestamp"),
                event.get("camera_id"),
                event.get("location"),
                event.get("clip_path"),
                event.get("snapshot_path")
            ))
            conn.commit()
            event_id = cur.lastrowid
            conn.close()
            return event_id
        except Exception as e:
            logger.error(f"Failed to store security event: {e}")
            return -1

    # ── Notifications ─────────────────────────────────────────────────────────

    def _send_notifications(self, event: dict):
        """Send notifications via all configured channels (runs in background thread)."""
        event_type = event.get("event_type", "alert")
        location = event.get("location", "Unknown")
        ts = datetime.fromisoformat(event.get("timestamp", datetime.utcnow().isoformat()))
        camera_id = event.get("camera_id", "")

        send_security_alert(
            event_type=event_type.upper(),
            location=location,
            timestamp=ts,
            camera_id=camera_id,
            security_phone=self.security_phone or None,
            security_email=self.security_email or None,
            security_fcm_token=self.security_fcm_token or None
        )

    def resolve_event(self, event_id: int, notes: str = ""):
        """Mark an event as resolved in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "UPDATE security_events SET resolved=1, notes=? WHERE id=?",
                (notes, event_id)
            )
            conn.commit()
            conn.close()
            logger.info(f"Event {event_id} resolved")
        except Exception as e:
            logger.error(f"Failed to resolve event: {e}")

    def get_recent_events(self, limit: int = 20) -> list:
        """Fetch recent security events from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM security_events ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Failed to fetch events: {e}")
            return []


# ─── Module-level convenience singleton ──────────────────────────────────────
_alert_system = None

def get_alert_system() -> AlertSystem:
    """Get or create the global AlertSystem singleton."""
    global _alert_system
    if _alert_system is None:
        _alert_system = AlertSystem()
    return _alert_system


def trigger_alert(event_type: str, camera_id: str, **kwargs) -> dict:
    """Convenience wrapper — trigger an alert via the global AlertSystem."""
    return get_alert_system().trigger(event_type, camera_id, **kwargs)
