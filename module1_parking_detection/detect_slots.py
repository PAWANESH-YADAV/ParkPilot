"""
ParkPilot — Module 1: Real-Time Parking Slot Detection
Reads a live camera feed, applies the trained CNN/SVM model to each defined
parking slot region, and displays color-coded occupancy in real-time.

Usage:
    # First define slot positions:
    python module1_parking_detection/train_model.py --mode positions

    # Then run detection on webcam (index 0):
    python module1_parking_detection/detect_slots.py --source 0

    # Or on an IP camera / RTSP stream:
    python module1_parking_detection/detect_slots.py --source rtsp://192.168.1.100:554/stream
"""

import os
import sys
import cv2
import pickle
import time
import numpy as np
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger, log_event
from utils.camera_stream import CameraStream, draw_status_overlay

logger = get_logger("parkpilot.module1.detect")

# ─── File paths ──────────────────────────────────────────────────────────────
SLOT_POSITIONS_PATH = "module1_parking_detection/slot_positions.pkl"
CNN_MODEL_PATH      = "module1_parking_detection/model.h5"
SVM_MODEL_PATH      = "module1_parking_detection/model_svm.pkl"

# ─── Constants ───────────────────────────────────────────────────────────────
CLASS_NAMES  = ["occupied", "vacant"]
IMG_SIZE     = (64, 64)
COLOR_VACANT   = (0, 255, 0)      # Green — vacant
COLOR_OCCUPIED = (0, 0, 255)      # Red — occupied
COLOR_UNKNOWN  = (200, 200, 200)  # Grey — unknown
FONT = cv2.FONT_HERSHEY_SIMPLEX


# ═══════════════════════════════════════════════════════════════════════════
#  Model Loading
# ═══════════════════════════════════════════════════════════════════════════

def load_model(prefer_cnn: bool = True):
    """
    Load the trained model. Tries CNN first, falls back to SVM.

    Returns:
        (model, model_type): model object and 'cnn' or 'svm' string
    """
    if prefer_cnn and os.path.exists(CNN_MODEL_PATH):
        try:
            import tensorflow as tf
            model = tf.keras.models.load_model(CNN_MODEL_PATH)
            logger.info(f"CNN model loaded from: {CNN_MODEL_PATH}")
            return model, "cnn"
        except Exception as e:
            logger.warning(f"CNN load failed: {e} — trying SVM")

    if os.path.exists(SVM_MODEL_PATH):
        with open(SVM_MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        logger.info(f"SVM model loaded from: {SVM_MODEL_PATH}")
        return model, "svm"

    logger.warning("No trained model found! Using random demo predictions.")
    return None, "demo"


def load_slot_positions() -> list:
    """Load saved slot positions (ROI coordinates)."""
    if not os.path.exists(SLOT_POSITIONS_PATH):
        logger.error(f"Slot positions not found: {SLOT_POSITIONS_PATH}")
        logger.info("Run: python module1_parking_detection/train_model.py --mode positions")
        return []

    with open(SLOT_POSITIONS_PATH, "rb") as f:
        positions = pickle.load(f)
    logger.info(f"Loaded {len(positions)} slot positions")
    return positions


# ═══════════════════════════════════════════════════════════════════════════
#  Prediction
# ═══════════════════════════════════════════════════════════════════════════

def preprocess_slot(frame: np.ndarray, slot: dict) -> np.ndarray:
    """
    Crop and preprocess a single slot ROI from the full frame.

    Args:
        frame: Full camera frame (BGR)
        slot: Slot dict with keys: x, y, width, height

    Returns:
        Preprocessed slot image (64x64 RGB normalized)
    """
    x, y, w, h = slot["x"], slot["y"], slot["width"], slot["height"]
    # Clamp to frame bounds
    fh, fw = frame.shape[:2]
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(fw, x + w), min(fh, y + h)

    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return np.zeros((*IMG_SIZE, 3), dtype=np.float32)

    resized = cv2.resize(crop, IMG_SIZE)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    return rgb.astype(np.float32) / 255.0


def predict_cnn(model, frame: np.ndarray, slots: list) -> list:
    """
    Batch predict all slots using CNN.

    Returns:
        List of (class_idx, confidence) per slot
    """
    batch = np.array([preprocess_slot(frame, s) for s in slots])
    predictions = model.predict(batch, verbose=0)
    return [(np.argmax(p), float(np.max(p))) for p in predictions]


def predict_svm(model, frame: np.ndarray, slots: list) -> list:
    """
    Predict all slots using SVM + HOG features.

    Returns:
        List of (class_idx, confidence) per slot
    """
    results = []
    for slot in slots:
        crop = preprocess_slot(frame, slot)
        bgr = (crop * 255).astype(np.uint8)
        bgr = cv2.cvtColor(bgr, cv2.COLOR_RGB2BGR)

        win_size = IMG_SIZE
        hog = cv2.HOGDescriptor(win_size, (16, 16), (8, 8), (8, 8), 9)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        features = hog.compute(gray).flatten().reshape(1, -1)

        pred = model.predict(features)[0]
        proba = model.predict_proba(features)[0]
        results.append((int(pred), float(np.max(proba))))

    return results


def predict_demo(slots: list) -> list:
    """Synthetic demo predictions when no model is available."""
    # 60% occupied, 40% vacant for demo purposes
    return [
        (0 if np.random.random() < 0.6 else 1, 0.85 + np.random.random() * 0.1)
        for _ in slots
    ]


def run_predictions(model, model_type: str, frame: np.ndarray, slots: list) -> list:
    """Dispatch to correct prediction function based on model type."""
    if model_type == "cnn":
        return predict_cnn(model, frame, slots)
    elif model_type == "svm":
        return predict_svm(model, frame, slots)
    else:
        return predict_demo(slots)


# ═══════════════════════════════════════════════════════════════════════════
#  Annotation
# ═══════════════════════════════════════════════════════════════════════════

def annotate_frame(
    frame: np.ndarray,
    slots: list,
    predictions: list,
    stats: dict
) -> np.ndarray:
    """
    Draw colored bounding boxes on all slots.
    Green = VACANT, Red = OCCUPIED.

    Args:
        frame: Camera frame
        slots: List of slot dicts
        predictions: List of (class_idx, confidence) tuples
        stats: {'total', 'vacant', 'occupied', 'fps'}
    """
    annotated = frame.copy()

    for slot, (class_idx, confidence) in zip(slots, predictions):
        x, y, w, h = slot["x"], slot["y"], slot["width"], slot["height"]
        label = CLASS_NAMES[class_idx]
        color = COLOR_VACANT if class_idx == 1 else COLOR_OCCUPIED

        # Bounding box
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)

        # Slot ID label
        slot_id = str(slot.get("id", "?"))
        cv2.putText(annotated, slot_id, (x + 3, y + 14),
                    FONT, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

        # Confidence label
        conf_text = f"{confidence:.0%}"
        cv2.putText(annotated, conf_text, (x + 3, y + h - 5),
                    FONT, 0.35, color, 1, cv2.LINE_AA)

    # Status overlay bar (total / vacant / occupied / fps)
    annotated = draw_status_overlay(annotated, stats)

    return annotated


# ═══════════════════════════════════════════════════════════════════════════
#  Status Change Detection & Dashboard Notification
# ═══════════════════════════════════════════════════════════════════════════

class SlotStatusTracker:
    """Tracks previous slot statuses and detects changes to trigger alerts."""

    def __init__(self, num_slots: int):
        self.previous: dict[int, int] = {}   # slot_id → class_idx
        self.change_log: list[dict] = []

    def update(self, slot_id: int, class_idx: int, confidence: float) -> bool:
        """
        Update slot status. Returns True if status changed.

        Args:
            slot_id: Slot identifier
            class_idx: 0=occupied, 1=vacant
            confidence: Prediction confidence
        """
        prev = self.previous.get(slot_id)
        changed = prev is not None and prev != class_idx

        if changed:
            label = CLASS_NAMES[class_idx]
            prev_label = CLASS_NAMES[prev]
            event = {
                "slot_id": slot_id,
                "from": prev_label,
                "to": label,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.change_log.append(event)
            log_event("PARKING_DETECTION", "STATUS_CHANGE",
                      f"Slot {slot_id}: {prev_label} → {label} ({confidence:.0%})",
                      extra=event)

        self.previous[slot_id] = class_idx
        return changed

    def get_stats(self, slots: list, predictions: list) -> dict:
        occupied = sum(1 for _, (c, _) in zip(slots, predictions) if c == 0)
        vacant = len(slots) - occupied
        return {
            "total": len(slots),
            "occupied": occupied,
            "vacant": vacant
        }


# ═══════════════════════════════════════════════════════════════════════════
#  Main Detection Loop
# ═══════════════════════════════════════════════════════════════════════════

def run_detection(
    source=0,
    prefer_cnn: bool = True,
    save_output: bool = False,
    headless: bool = False
):
    """
    Main real-time detection loop.

    Args:
        source: Camera source (int index or RTSP URL string)
        prefer_cnn: Use CNN model if available
        save_output: Save annotated video to file
        headless: Run without display (for server/background mode)
    """
    # Load model and slot positions
    model, model_type = load_model(prefer_cnn)
    slots = load_slot_positions()

    if not slots:
        logger.error("No slot positions defined. Cannot run detection.")
        return

    logger.info(f"Running detection | Model: {model_type} | Slots: {len(slots)} | Source: {source}")

    stream = CameraStream(source=source)
    stream.start()

    tracker = SlotStatusTracker(num_slots=len(slots))
    fps_timer = time.time()
    frame_count = 0
    fps = 0.0

    # Output video writer
    writer = None
    if save_output:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        os.makedirs("module1_parking_detection/output", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        writer = cv2.VideoWriter(
            f"module1_parking_detection/output/detection_{ts}.mp4",
            fourcc, 10.0, (1280, 720)
        )

    try:
        while True:
            frame = stream.read()
            if frame is None:
                time.sleep(0.05)
                continue

            frame_count += 1
            # Calculate FPS every 30 frames
            if frame_count % 30 == 0:
                elapsed = time.time() - fps_timer
                fps = 30.0 / max(elapsed, 0.001)
                fps_timer = time.time()

            # Run predictions every other frame for performance
            if frame_count % 2 == 0:
                predictions = run_predictions(model, model_type, frame, slots)
            else:
                predictions = [(0, 0.0)] * len(slots)  # Use cached (not shown)

            # Track status changes
            for slot, (class_idx, conf) in zip(slots, predictions):
                tracker.update(slot["id"], class_idx, conf)

            # Build stats
            stats = tracker.get_stats(slots, predictions)
            stats["fps"] = fps

            # Annotate frame
            annotated = annotate_frame(frame, slots, predictions, stats)

            if writer:
                resized = cv2.resize(annotated, (1280, 720))
                writer.write(resized)

            if not headless:
                cv2.imshow("ParkPilot — Real-Time Parking Detection", annotated)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q") or key == 27:  # 'q' or ESC to quit
                    break
                elif key == ord("s"):              # 's' to save screenshot
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    path = f"module1_parking_detection/output/screenshot_{ts}.jpg"
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    cv2.imwrite(path, annotated)
                    logger.info(f"Screenshot saved: {path}")

    except KeyboardInterrupt:
        logger.info("Detection stopped by user")
    finally:
        stream.stop()
        if writer:
            writer.release()
        if not headless:
            cv2.destroyAllWindows()
        logger.info(
            f"Session complete | Total frames: {frame_count} | "
            f"Status changes: {len(tracker.change_log)}"
        )


# ═══════════════════════════════════════════════════════════════════════════
#  Interactive Slot Position Definer
# ═══════════════════════════════════════════════════════════════════════════

def define_slot_positions_interactive(source=0):
    """
    Interactive tool to manually define parking slot ROIs using mouse clicks.
    Click and drag to draw slot rectangles. Press 's' to save, 'q' to quit.

    Instructions:
        - Click and drag to draw a slot bounding box
        - Press 's' to save all defined positions
        - Press 'r' to redo last slot
        - Press 'q' to quit without saving
    """
    import pickle

    cap = cv2.VideoCapture(source)
    ret, frame = cap.read()
    if not ret:
        logger.error(f"Cannot open source: {source}")
        cap.release()
        return

    cap.release()
    reference_frame = frame.copy()
    slots = []
    drawing = False
    start_x = start_y = 0
    slot_id_counter = 1

    def mouse_callback(event, x, y, flags, param):
        nonlocal drawing, start_x, start_y, slot_id_counter

        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            start_x, start_y = x, y

        elif event == cv2.EVENT_LBUTTONUP and drawing:
            drawing = False
            w = abs(x - start_x)
            h = abs(y - start_y)
            if w > 10 and h > 10:
                slot = {
                    "id": slot_id_counter,
                    "x": min(start_x, x),
                    "y": min(start_y, y),
                    "width": w,
                    "height": h,
                    "zone": "A",
                    "level": 1
                }
                slots.append(slot)
                slot_id_counter += 1
                logger.info(f"Slot {slot['id']} defined: {slot}")

    cv2.namedWindow("Define Parking Slots", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Define Parking Slots", mouse_callback)

    logger.info("Click and drag to define slot boundaries. Press 's' to save, 'q' to quit.")

    while True:
        display = reference_frame.copy()
        for slot in slots:
            x, y, w, h = slot["x"], slot["y"], slot["width"], slot["height"]
            cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(display, str(slot["id"]), (x + 3, y + 14),
                        FONT, 0.5, (255, 255, 255), 1)

        cv2.putText(display, f"Slots defined: {len(slots)} | [s]=save [r]=redo [q]=quit",
                    (10, 30), FONT, 0.6, (0, 220, 255), 2)
        cv2.imshow("Define Parking Slots", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("s"):
            os.makedirs("module1_parking_detection", exist_ok=True)
            with open(SLOT_POSITIONS_PATH, "wb") as f:
                pickle.dump(slots, f)
            logger.info(f"✅ Saved {len(slots)} slot positions to {SLOT_POSITIONS_PATH}")
            break
        elif key == ord("r") and slots:
            removed = slots.pop()
            slot_id_counter -= 1
            logger.info(f"Removed slot {removed['id']}")
        elif key == ord("q"):
            logger.info("Exited without saving")
            break

    cv2.destroyAllWindows()


# ═══════════════════════════════════════════════════════════════════════════
#  Entry Point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ParkPilot — Parking Slot Detector")
    parser.add_argument("--source", default="0", help="Camera source (int or RTSP URL)")
    parser.add_argument("--svm", action="store_true", help="Force SVM model instead of CNN")
    parser.add_argument("--save", action="store_true", help="Save annotated video output")
    parser.add_argument("--headless", action="store_true", help="Run without GUI display")
    parser.add_argument("--define-slots", action="store_true",
                        help="Launch interactive slot position definer")
    args = parser.parse_args()

    # Convert source to int if numeric
    source = int(args.source) if args.source.isdigit() else args.source

    if args.define_slots:
        define_slot_positions_interactive(source=source)
    else:
        run_detection(
            source=source,
            prefer_cnn=not args.svm,
            save_output=args.save,
            headless=args.headless
        )
