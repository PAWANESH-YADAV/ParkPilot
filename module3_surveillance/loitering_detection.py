"""
ParkPilot — Module 3: Loitering Detection
Tracks persons across frames and flags when they remain in the same
zone beyond the configured time threshold.

Integrates with ActivityMonitor for combined surveillance.
"""

import cv2
import numpy as np
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger, log_event
from utils.config import settings

logger = get_logger("parkpilot.module3.loitering")


class Zone:
    """
    Represents a defined surveillance zone (e.g., Zone A, Gate B, Restricted Area).
    """
    def __init__(self, zone_id: str, polygon: list, is_restricted: bool = False):
        """
        Args:
            zone_id: Unique zone identifier (e.g., "GATE_A", "ZONE_B")
            polygon: List of (x, y) points defining the zone boundary
            is_restricted: If True, ANY person triggers unauthorized access alert
        """
        self.zone_id = zone_id
        self.polygon = np.array(polygon, dtype=np.int32)
        self.is_restricted = is_restricted
        self.current_occupants: dict[int, datetime] = {}  # obj_id → entry_time

    def contains_point(self, point: tuple) -> bool:
        """Check if a point (cx, cy) is inside this zone."""
        return cv2.pointPolygonTest(self.polygon, point, False) >= 0

    def draw(self, frame: np.ndarray):
        """Draw zone boundary on frame."""
        color = (0, 0, 180) if self.is_restricted else (255, 165, 0)
        cv2.polylines(frame, [self.polygon], True, color, 2)
        # Zone label at centroid
        cx = int(np.mean(self.polygon[:, 0]))
        cy = int(np.mean(self.polygon[:, 1]))
        label = f"[{'RESTRICTED' if self.is_restricted else self.zone_id}]"
        cv2.putText(frame, label, (cx - 40, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)


class LoiteringDetector:
    """
    Advanced loitering detector using time-in-zone tracking.

    Detection Logic:
        1. For each tracked object, determine which zone it is in
        2. Track time since first seen in that zone
        3. If time > threshold → flag as LOITERING
        4. If zone is RESTRICTED → flag as UNAUTHORIZED_ACCESS immediately
        5. Save clip and trigger alert

    Args:
        loitering_threshold_seconds: Time limit before loitering is flagged
        zones: List of Zone objects to monitor
        clip_save_path: Directory to save flagged video clips
    """

    def __init__(
        self,
        loitering_threshold_seconds: int = None,
        zones: list = None,
        clip_save_path: str = None
    ):
        self.threshold = loitering_threshold_seconds or settings.LOITERING_THRESHOLD_SECONDS
        self.zones = zones or []
        self.clip_save_path = clip_save_path or settings.CLIPS_SAVE_PATH
        import os
        os.makedirs(self.clip_save_path, exist_ok=True)

        # obj_id → {zone_id, entry_time, flagged}
        self.zone_tracking: dict[int, dict] = {}
        # Active alerts: set of obj_id that have been flagged (avoid repeat alerts)
        self.flagged_ids: set = set()
        # Clip recording buffers: zone_id → list of frames
        self.clip_buffers: dict[str, list] = defaultdict(list)

        logger.info(
            f"LoiteringDetector | Threshold: {self.threshold}s | "
            f"Zones: {len(self.zones)} | Clip dir: {self.clip_save_path}"
        )

    def add_zone(self, zone: "Zone"):
        """Add a surveillance zone."""
        self.zones.append(zone)

    def update(
        self,
        tracked_objects: dict,
        frame: np.ndarray,
        camera_id: str = "CAM01"
    ) -> list:
        """
        Process tracked objects and detect loitering/unauthorized access.

        Args:
            tracked_objects: Dict from PersonTracker.update()
            frame: Current frame (for clip recording)
            camera_id: Camera identifier

        Returns:
            List of flagged event dicts
        """
        events = []

        for obj_id, obj in tracked_objects.items():
            centroid = obj["centroid"]

            # Determine which zone the object is in
            current_zone = None
            for zone in self.zones:
                if zone.contains_point(centroid):
                    current_zone = zone
                    break

            if current_zone is None:
                # Not in any monitored zone
                if obj_id in self.zone_tracking:
                    del self.zone_tracking[obj_id]
                continue

            # ── Track time in zone ────────────────────────────────────────
            if obj_id not in self.zone_tracking:
                self.zone_tracking[obj_id] = {
                    "zone_id": current_zone.zone_id,
                    "entry_time": datetime.utcnow(),
                    "flagged": False
                }
            elif self.zone_tracking[obj_id]["zone_id"] != current_zone.zone_id:
                # Zone changed — reset timer
                self.zone_tracking[obj_id] = {
                    "zone_id": current_zone.zone_id,
                    "entry_time": datetime.utcnow(),
                    "flagged": False
                }

            track = self.zone_tracking[obj_id]
            time_in_zone = (datetime.utcnow() - track["entry_time"]).total_seconds()

            # ── Unauthorized Access ────────────────────────────────────────
            if current_zone.is_restricted and obj_id not in self.flagged_ids:
                event = {
                    "type": "unauthorized",
                    "object_id": obj_id,
                    "zone_id": current_zone.zone_id,
                    "time_in_zone": time_in_zone,
                    "centroid": centroid,
                    "camera_id": camera_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "severity": "HIGH"
                }
                events.append(event)
                self.flagged_ids.add(obj_id)
                self._save_snapshot(frame, event)
                log_event("SURVEILLANCE", "UNAUTHORIZED_ACCESS",
                          f"Person in restricted zone {current_zone.zone_id}", extra=event)

            # ── Loitering ─────────────────────────────────────────────────
            elif time_in_zone > self.threshold and not track["flagged"]:
                track["flagged"] = True
                event = {
                    "type": "loitering",
                    "object_id": obj_id,
                    "zone_id": current_zone.zone_id,
                    "time_in_zone": time_in_zone,
                    "centroid": centroid,
                    "camera_id": camera_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "severity": "MEDIUM"
                }
                events.append(event)
                self._save_snapshot(frame, event)
                log_event("SURVEILLANCE", "LOITERING",
                          f"Person loitering {time_in_zone:.0f}s in {current_zone.zone_id}",
                          extra=event)

            # ── Buffer frames for clip saving ──────────────────────────────
            zone_key = f"{camera_id}_{current_zone.zone_id}"
            self.clip_buffers[zone_key].append(frame.copy())
            # Keep last 150 frames (≈5 seconds @ 30fps)
            if len(self.clip_buffers[zone_key]) > 150:
                self.clip_buffers[zone_key].pop(0)

        # ── Annotate zones on frame ───────────────────────────────────────
        for zone in self.zones:
            zone.draw(frame)

        return events

    def _save_snapshot(self, frame: np.ndarray, event: dict):
        """Save a snapshot image for the flagged event."""
        import os
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        event_type = event.get("type", "event")
        path = os.path.join(self.clip_save_path, f"{event_type}_{ts}.jpg")
        cv2.imwrite(path, frame)
        event["snapshot_path"] = path
        logger.info(f"Snapshot saved: {path}")

    def save_event_clip(self, zone_key: str, event: dict, fps: float = 10.0) -> str:
        """
        Save buffered frames as a video clip for a flagged event.

        Args:
            zone_key: Buffer key (camera_id + zone_id)
            event: Event dict
            fps: Output video FPS

        Returns:
            Path to saved clip
        """
        import os
        frames = self.clip_buffers.get(zone_key, [])
        if not frames:
            return ""

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        clip_path = os.path.join(
            self.clip_save_path,
            f"clip_{event['type']}_{ts}.mp4"
        )

        h, w = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(clip_path, fourcc, fps, (w, h))
        for frm in frames:
            writer.write(frm)
        writer.release()

        event["clip_path"] = clip_path
        logger.info(f"Clip saved: {clip_path} ({len(frames)} frames)")
        return clip_path

    def get_summary(self) -> dict:
        """Return a summary of current tracking state."""
        return {
            "tracked_objects": len(self.zone_tracking),
            "flagged_ids": len(self.flagged_ids),
            "zones": [z.zone_id for z in self.zones],
            "threshold_seconds": self.threshold
        }


def create_default_zones(frame_width: int = 1280, frame_height: int = 720) -> list:
    """
    Create default zone definitions for a standard parking lot layout.
    Override this with actual zone coordinates from your parking lot blueprint.

    Returns:
        List of Zone objects
    """
    w, h = frame_width, frame_height
    return [
        Zone("ZONE_A", [(0, 0), (w//2, 0), (w//2, h//2), (0, h//2)], is_restricted=False),
        Zone("ZONE_B", [(w//2, 0), (w, 0), (w, h//2), (w//2, h//2)], is_restricted=False),
        Zone("RESTRICTED", [(w//4, h*3//4), (w*3//4, h*3//4), (w*3//4, h), (w//4, h)],
             is_restricted=True),
    ]
