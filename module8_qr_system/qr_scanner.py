"""
Module 8 — QR Scanner
======================
Scans QR codes from camera frames or image files using OpenCV + pyzbar.
Validates the embedded payload and returns ticket info.

Dependencies:
    pip install opencv-python pyzbar

Usage:
    from module8_qr_system.qr_scanner import QRScanner
    scanner = QRScanner()
    result = scanner.scan_from_image("ticket.png")
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    logger.warning("opencv-python not installed. Camera scanning disabled.")
    CV2_AVAILABLE = False

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    PYZBAR_AVAILABLE = True
except ImportError:
    logger.warning("pyzbar not installed. QR decoding from images disabled.")
    PYZBAR_AVAILABLE = False

from module8_qr_system.qr_generator import QRGenerator


# ──────────────────────────────────────────────
# Scan Result
# ──────────────────────────────────────────────

class ScanResult:
    """Structured result from a QR scan operation."""

    def __init__(
        self,
        success: bool,
        raw_data: str = "",
        payload: Optional[dict] = None,
        error: str = "",
        is_valid: bool = False,
        is_expired: bool = False,
    ):
        self.success    = success
        self.raw_data   = raw_data
        self.payload    = payload or {}
        self.error      = error
        self.is_valid   = is_valid
        self.is_expired = is_expired
        self.scanned_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "success"    : self.success,
            "raw_data"   : self.raw_data,
            "payload"    : self.payload,
            "error"      : self.error,
            "is_valid"   : self.is_valid,
            "is_expired" : self.is_expired,
            "scanned_at" : self.scanned_at,
        }

    def __repr__(self):
        return (
            f"ScanResult(success={self.success}, valid={self.is_valid}, "
            f"expired={self.is_expired}, type={self.payload.get('type','?')})"
        )


# ──────────────────────────────────────────────
# QR Scanner
# ──────────────────────────────────────────────

class QRScanner:
    """
    Scans QR codes from images or live camera feed.
    Validates ticket authenticity using the generator's hash check.
    """

    def __init__(self):
        self._generator = QRGenerator(output_dir=os.path.join(
            os.path.dirname(__file__), "tickets"
        ))

    # ── Image Scanning ────────────────────────────────────────────────────

    def scan_from_image(self, image_path: str) -> ScanResult:
        """
        Decode and validate a QR code from an image file.

        Args:
            image_path: Path to PNG/JPG ticket image.

        Returns:
            ScanResult
        """
        if not (CV2_AVAILABLE and PYZBAR_AVAILABLE):
            return ScanResult(False, error="cv2 or pyzbar not installed.")

        if not os.path.exists(image_path):
            return ScanResult(False, error=f"File not found: {image_path}")

        img = cv2.imread(image_path)
        if img is None:
            return ScanResult(False, error="Failed to read image.")

        return self._decode_frame(img)

    def scan_from_frame(self, frame: "cv2.Mat") -> ScanResult:
        """Decode a QR code from an OpenCV frame."""
        if not (CV2_AVAILABLE and PYZBAR_AVAILABLE):
            return ScanResult(False, error="cv2 or pyzbar not installed.")
        return self._decode_frame(frame)

    # ── Camera Scanning ───────────────────────────────────────────────────

    def scan_from_camera(
        self,
        camera_index: int = 0,
        timeout_seconds: float = 30.0,
        show_preview: bool = False,
    ) -> ScanResult:
        """
        Open a camera and continuously scan until a QR code is found.

        Args:
            camera_index   : CV camera index (0 = default webcam)
            timeout_seconds: Maximum scan time before giving up
            show_preview   : Whether to open a CV window preview

        Returns:
            First valid ScanResult found.
        """
        if not (CV2_AVAILABLE and PYZBAR_AVAILABLE):
            return ScanResult(False, error="Camera scanning requires cv2 + pyzbar.")

        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return ScanResult(False, error=f"Cannot open camera index {camera_index}.")

        start = datetime.now()
        result = ScanResult(False, error="Timeout — no QR code found.")

        try:
            while (datetime.now() - start).total_seconds() < timeout_seconds:
                ret, frame = cap.read()
                if not ret:
                    continue

                scan = self._decode_frame(frame)
                if scan.success:
                    result = scan
                    break

                if show_preview:
                    cv2.imshow("ParkPilot — QR Scanner", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
        finally:
            cap.release()
            if show_preview:
                cv2.destroyAllWindows()

        return result

    # ── Validation ────────────────────────────────────────────────────────

    def validate_ticket(self, payload: dict) -> tuple[bool, str]:
        """
        Validate a scanned QR payload.

        Returns:
            (is_valid, reason_string)
        """
        # Check required fields
        required = ["type", "hash"]
        for field in required:
            if field not in payload:
                return False, f"Missing field: {field}"

        # Verify cryptographic hash
        if not self._generator.validate_hash(dict(payload)):
            return False, "Invalid hash — ticket may be forged."

        # Check expiry
        if self._generator.is_expired(payload):
            return False, "Ticket has expired."

        return True, "OK"

    # ── Private ───────────────────────────────────────────────────────────

    def _decode_frame(self, frame) -> ScanResult:
        """Decode all QR codes in a single frame and return the first valid one."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        decoded_objects = pyzbar_decode(gray)

        for obj in decoded_objects:
            raw = obj.data.decode("utf-8", errors="ignore")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning(f"Non-JSON QR data: {raw[:60]}")
                return ScanResult(True, raw_data=raw, payload={}, is_valid=False,
                                  error="QR data is not valid JSON.")

            is_valid, reason = self.validate_ticket(payload)
            is_expired = reason == "Ticket has expired."

            logger.info(
                f"QR scanned: type={payload.get('type','?')} "
                f"valid={is_valid} reason={reason}"
            )
            return ScanResult(
                success=True,
                raw_data=raw,
                payload=payload,
                is_valid=is_valid,
                is_expired=is_expired,
                error="" if is_valid else reason,
            )

        return ScanResult(False, error="No QR code detected in frame.")


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    scanner = QRScanner()
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        result = scanner.scan_from_image(image_path)
        print("\n=== Scan Result ===")
        for k, v in result.to_dict().items():
            print(f"  {k:15s}: {v}")
    else:
        print("Usage: python qr_scanner.py <image_path.png>")
        print("       OR running camera scan…")
        if CV2_AVAILABLE and PYZBAR_AVAILABLE:
            result = scanner.scan_from_camera(timeout_seconds=10, show_preview=True)
            print(result)
