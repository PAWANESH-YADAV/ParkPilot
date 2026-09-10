"""
ParkPilot — Module 3: Activity Monitor
Real-time surveillance using OpenCV MOG2 background subtraction to
detect moving objects in the parking lot. Foundation for loitering
and vandalism detection.

Usage:
    python module3_surveillance/activity_monitor.py --source 0
"""

import cv2
import numpy as np
import time
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger, log_event
from utils.camera_stream import CameraStream, draw_status_overlay
from utils.config import settings

logger = get_logger("parkpilot.module3.activity_monitor")


class PersonTracker:
    """
    Tracks individual people/objects across frames using bounding boxes.
    Assigns unique IDs and tracks time-in-zone for loitering detection.
    """

    def __init__(self, max_disappeared: int = 30):
        self.objects: dict[int, dict] = {}    # id → track data
        self.disappeared: dict[int, int] = {} # id → frame count since last seen
        self.next_id = 0
        self.max_disappeared = max_disappeared

    def register(self, centroid: tuple, bbox: tuple) -> int:
        """Register a new tracked object."""
        obj_id = self.next_id
        self.objects[obj_id] = {
            "centroid": centroid,
            "bbox": bbox,
            "first_seen": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "zone": None,
            "frames_in_zone": 0,
            "total_frames": 0
        }
        self.disappeared[obj_id] = 0
        self.next_id += 1
        logger.debug(f"Registered new object ID: {obj_id}")
        return obj_id

    def deregister(self, obj_id: int):
        """Remove a tracked object."""
        del self.objects[obj_id]
        del self.disappeared[obj_id]

    def update(self, detections: list) -> dict:
        """
        Update tracker with new detections.

        Args:
            detections: List of (bbox, centroid) tuples

        Returns:
            Updated objects dict
        """
        if not detections:
            # Mark all as disappeared
            for obj_id in list(self.disappeared.keys()):
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] > self.max_disappeared:
                    self.deregister(obj_id)
            return self.objects

        centroids = [det[1] for det in detections]
        bboxes = [det[0] for det in detections]

        if not self.objects:
            for c, b in zip(centroids, bboxes):
                self.register(c, b)
        else:
            object_ids = list(self.objects.keys())
            object_centroids = [self.objects[oid]["centroid"] for oid in object_ids]

            # Calculate pairwise distances
            D = np.zeros((len(object_centroids), len(centroids)))
            for i, oc in enumerate(object_centroids):
                for j, nc in enumerate(centroids):
                    D[i, j] = np.sqrt((oc[0] - nc[0])**2 + (oc[1] - nc[1])**2)

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows, used_cols = set(), set()
            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                if D[row, col] > 100:  # Max distance to match
                    continue

                obj_id = object_ids[row]
                self.objects[obj_id]["centroid"] = centroids[col]
                self.objects[obj_id]["bbox"] = bboxes[col]
                self.objects[obj_id]["last_seen"] = datetime.utcnow()
                self.objects[obj_id]["total_frames"] += 1
                self.disappeared[obj_id] = 0
                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(D.shape[0])) - used_rows
            for row in unused_rows:
                obj_id = object_ids[row]
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] > self.max_disappeared:
                    self.deregister(obj_id)

            unused_cols = set(range(D.shape[1])) - used_cols
            for col in unused_cols:
                self.register(centroids[col], bboxes[col])

        return self.objects

    def get_time_in_zone(self, obj_id: int) -> float:
        """Get seconds an object has been tracked."""
        obj = self.objects.get(obj_id)
        if not obj:
            return 0.0
        return (datetime.utcnow() - obj["first_seen"]).total_seconds()


class ActivityMonitor:
    """
    Main surveillance monitor using MOG2 background subtraction.
    Detects people/objects, tracks them, and classifies activity.

    Algorithm:
        1. MOG2 background subtraction → foreground mask
        2. Morphological operations → clean mask
        3. Find contours → filter by area
        4. Track objects with PersonTracker
        5. Check loitering threshold (time in zone)
        6. Flag suspicious activity → trigger alert
    """

    def __init__(
        self,
        loitering_threshold: int = None,
        min_object_area: int = 800,
        min_object_area_vandalism: int = 200
    ):
        self.loitering_threshold = loitering_threshold or settings.LOITERING_THRESHOLD_SECONDS
        self.min_area = min_object_area
        self.min_area_vandalism = min_object_area_vandalism

        # MOG2 background subtractor
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True
        )

        # Morphological kernel
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        self.tracker = PersonTracker()
        self.flagged_events: list[dict] = []
        self.frame_count = 0

        logger.info(
            f"ActivityMonitor initialized | "
            f"Loitering threshold: {self.loitering_threshold}s"
        )

    def process_frame(self, frame: np.ndarray, camera_id: str = "CAM01") -> dict:
        """
        Process a single frame for activity detection.

        Args:
            frame: BGR camera frame
            camera_id: Identifier for this camera

        Returns:
            dict with:
                - detections: List of detected objects
                - events: List of flagged events this frame
                - annotated_frame: Frame with drawn bounding boxes
        """
        self.frame_count += 1
        events = []
        annotated = frame.copy()

        # ── Background Subtraction ─────────────────────────────────────────
        fg_mask = self.bg_subtractor.apply(frame)

        # Remove shadows (grey pixels, value=127)
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)

        # Morphological cleanup
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, self.kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, self.kernel)
        fg_mask = cv2.dilate(fg_mask, self.kernel, iterations=2)

        # ── Find Contours ─────────────────────────────────────────────────
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self.min_area:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            cx, cy = x + w // 2, y + h // 2
            detections.append(((x, y, w, h), (cx, cy)))

        # ── Update Tracker ────────────────────────────────────────────────
        tracked = self.tracker.update(detections)

        # ── Draw Tracked Objects & Check Loitering ────────────────────────
        for obj_id, obj in tracked.items():
            x, y, w, h = obj["bbox"]
            cx, cy = obj["centroid"]
            time_in_zone = self.tracker.get_time_in_zone(obj_id)

            # Color based on loitering status
            if time_in_zone > self.loitering_threshold:
                color = (0, 0, 255)   # Red — loitering
                label = f"ID:{obj_id} LOITERING {time_in_zone:.0f}s"
                events.append({
                    "type": "loitering",
                    "object_id": obj_id,
                    "duration_seconds": time_in_zone,
                    "location": (cx, cy),
                    "camera_id": camera_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif time_in_zone > self.loitering_threshold * 0.5:
                color = (0, 165, 255)  # Orange — warning
                label = f"ID:{obj_id} {time_in_zone:.0f}s"
            else:
                color = (0, 255, 0)   # Green — normal
                label = f"ID:{obj_id}"

            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            cv2.putText(annotated, label, (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
            cv2.circle(annotated, (cx, cy), 4, color, -1)

        # ── Check Rapid Motion (Vandalism Detection) ──────────────────────
        vandalism = self._check_rapid_motion(fg_mask, frame, camera_id)
        if vandalism:
            events.append(vandalism)
            cv2.putText(annotated, "⚠ VANDALISM DETECTED", (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        # ── Alert Banner ──────────────────────────────────────────────────
        if events:
            self._draw_alert_banner(annotated, events[0])
            # Store flagged events
            for ev in events:
                if not any(e["type"] == ev["type"] for e in self.flagged_events[-5:]):
                    self.flagged_events.append(ev)
                    log_event("SURVEILLANCE", ev["type"].upper(),
                              f"Camera {camera_id}", extra=ev)

        # ── FG mask overlay (bottom-right minimap) ────────────────────────
        mask_display = cv2.cvtColor(fg_mask, cv2.COLOR_GRAY2BGR)
        mask_small = cv2.resize(mask_display, (160, 90))
        h_f, w_f = annotated.shape[:2]
        annotated[h_f-100:h_f-10, w_f-170:w_f-10] = mask_small

        return {
            "detections": len(detections),
            "tracked_objects": len(tracked),
            "events": events,
            "annotated_frame": annotated,
            "fg_mask": fg_mask
        }

    def _check_rapid_motion(self, fg_mask: np.ndarray, frame: np.ndarray, camera_id: str):
        """
        Detect vandalism by checking for rapid large-area motion.
        Returns event dict if vandalism detected, else None.
        """
        # Only check every 15 frames
        if self.frame_count % 15 != 0:
            return None

        non_zero = cv2.countNonZero(fg_mask)
        total_pixels = fg_mask.shape[0] * fg_mask.shape[1]
        motion_ratio = non_zero / total_pixels

        if motion_ratio > 0.15:  # >15% of frame in motion = suspicious
            return {
                "type": "vandalism",
                "motion_ratio": motion_ratio,
                "camera_id": camera_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        return None

    def _draw_alert_banner(self, frame: np.ndarray, event: dict):
        """Draw a red alert banner at the top of the frame."""
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 50), (0, 0, 200), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        event_type = event.get("type", "ALERT").upper()
        ts = event.get("timestamp", "")[:19]
        text = f"🚨 {event_type} DETECTED — {event.get('camera_id', '')} | {ts}"
        cv2.putText(frame, text, (10, 33),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)


# ═══════════════════════════════════════════════════════════════════════════
#  Main Loop
# ═══════════════════════════════════════════════════════════════════════════

def run_monitor(source=0, camera_id: str = "CAM01", headless: bool = False):
    """
    Run the activity monitor on a camera feed.

    Args:
        source: Camera source (int or RTSP URL)
        camera_id: Camera identifier
        headless: Skip display
    """
    monitor = ActivityMonitor()
    stream = CameraStream(source=source)
    stream.start()

    fps_timer = time.time()
    frame_count = 0
    fps = 0.0

    logger.info(f"Activity monitor started | Camera: {camera_id} | Source: {source}")

    try:
        while True:
            frame = stream.read()
            if frame is None:
                time.sleep(0.05)
                continue

            frame_count += 1
            if frame_count % 30 == 0:
                fps = 30.0 / max(time.time() - fps_timer, 0.001)
                fps_timer = time.time()

            result = monitor.process_frame(frame, camera_id=camera_id)
            annotated = result["annotated_frame"]

            stats = {
                "total": result["tracked_objects"],
                "vacant": 0,
                "occupied": result["detections"],
                "fps": fps
            }
            annotated = draw_status_overlay(annotated, stats)

            if not headless:
                cv2.imshow(f"ParkPilot Surveillance — {camera_id}", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    except KeyboardInterrupt:
        logger.info("Monitor stopped")
    finally:
        stream.stop()
        if not headless:
            cv2.destroyAllWindows()
        logger.info(f"Session complete | Total events: {len(monitor.flagged_events)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ParkPilot — Activity Monitor")
    parser.add_argument("--source", default="0", help="Camera source")
    parser.add_argument("--camera-id", default="CAM01", help="Camera ID")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source
    run_monitor(source=source, camera_id=args.camera_id, headless=args.headless)
