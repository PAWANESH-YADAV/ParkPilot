"""
ParkPilot — Camera Stream Utility
Thread-safe camera stream manager for all modules.
Supports USB webcams (index) and RTSP/IP camera URLs.
"""

import cv2
import threading
import time
import numpy as np
from utils.logger import get_logger

logger = get_logger("parkpilot.camera_stream")


class CameraStream:
    """
    Thread-safe camera stream reader.
    Continuously reads frames in background thread to avoid lag.

    Usage:
        stream = CameraStream(source=0)
        stream.start()
        while True:
            frame = stream.read()
            if frame is not None:
                cv2.imshow("Feed", frame)
        stream.stop()
    """

    def __init__(self, source=0, width: int = 1280, height: int = 720, fps: int = 30):
        """
        Args:
            source: Camera index (int) or RTSP URL (str)
            width: Frame width
            height: Frame height
            fps: Target FPS
        """
        self.source = source
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None
        self.frame = None
        self.lock = threading.Lock()
        self.running = False
        self._thread = None

    def start(self) -> "CameraStream":
        """Start the background capture thread."""
        logger.info(f"Opening camera source: {self.source}")
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            logger.error(f"Failed to open camera: {self.source}")
            raise RuntimeError(f"Cannot open camera source: {self.source}")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        self.running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info(f"Camera stream started: {self.source} @ {self.width}x{self.height}")
        return self

    def _capture_loop(self):
        """Background loop — continuously reads and stores latest frame."""
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
            else:
                logger.warning(f"Frame capture failed from: {self.source}. Retrying...")
                time.sleep(0.1)

    def read(self) -> np.ndarray | None:
        """Return the latest captured frame (thread-safe)."""
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy()

    def stop(self):
        """Stop the capture thread and release camera."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()
        logger.info(f"Camera stream stopped: {self.source}")

    def __enter__(self):
        return self.start()

    def __exit__(self, *args):
        self.stop()

    @property
    def is_open(self) -> bool:
        return self.running and self.cap is not None and self.cap.isOpened()


class MultiCameraManager:
    """
    Manages multiple simultaneous camera streams.
    Useful for systems with entry, exit, and surveillance cameras.

    Usage:
        mgr = MultiCameraManager()
        mgr.add_camera("entry", source=0)
        mgr.add_camera("exit", source=1)
        mgr.add_camera("surveillance", source="rtsp://...")
        mgr.start_all()
        frame = mgr.read("entry")
        mgr.stop_all()
    """

    def __init__(self):
        self.cameras: dict[str, CameraStream] = {}

    def add_camera(self, name: str, source, **kwargs) -> "MultiCameraManager":
        """Register a named camera stream."""
        self.cameras[name] = CameraStream(source=source, **kwargs)
        return self

    def start_all(self):
        """Start all registered cameras."""
        for name, cam in self.cameras.items():
            try:
                cam.start()
            except RuntimeError as e:
                logger.error(f"Failed to start camera '{name}': {e}")

    def stop_all(self):
        """Stop all registered cameras."""
        for cam in self.cameras.values():
            cam.stop()

    def read(self, name: str) -> np.ndarray | None:
        """Read latest frame from named camera."""
        cam = self.cameras.get(name)
        if cam:
            return cam.read()
        logger.warning(f"Camera '{name}' not registered")
        return None

    def read_all(self) -> dict[str, np.ndarray | None]:
        """Read latest frames from all cameras."""
        return {name: cam.read() for name, cam in self.cameras.items()}


def capture_single_frame(source=0, warm_up_frames: int = 5) -> np.ndarray | None:
    """
    Capture a single still frame from a camera.
    Discards warm-up frames to avoid dark/blurry first frames.

    Args:
        source: Camera index or URL
        warm_up_frames: Number of frames to discard before capturing

    Returns:
        Captured frame as numpy array, or None on failure
    """
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        logger.error(f"Cannot open camera: {source}")
        return None

    for _ in range(warm_up_frames):
        cap.read()  # Discard warm-up frames

    ret, frame = cap.read()
    cap.release()

    if not ret:
        logger.error("Frame capture failed")
        return None

    logger.debug(f"Single frame captured: {frame.shape}")
    return frame


def draw_status_overlay(frame: np.ndarray, stats: dict) -> np.ndarray:
    """
    Draw an informational overlay on a frame.

    Args:
        frame: Input frame
        stats: Dict with keys like 'total', 'vacant', 'occupied', 'fps'

    Returns:
        Frame with overlay
    """
    overlay = frame.copy()
    h, w = frame.shape[:2]

    # Semi-transparent background
    cv2.rectangle(overlay, (0, 0), (w, 60), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    # Stats text
    y = 35
    text_parts = [
        (f"TOTAL: {stats.get('total', 0)}", (255, 255, 255)),
        (f"  VACANT: {stats.get('vacant', 0)}", (0, 255, 0)),
        (f"  OCCUPIED: {stats.get('occupied', 0)}", (0, 0, 255)),
        (f"  FPS: {stats.get('fps', 0):.1f}", (255, 200, 0)),
    ]

    x = 10
    for text, color in text_parts:
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        text_w, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        x += text_w

    # Timestamp
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, ts, (w - 220, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

    return frame
