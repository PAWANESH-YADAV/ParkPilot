"""
Module 8 — QR Code Generator
==============================
Generates QR code tickets for parking sessions and visitor passes.
Stores the QR hash in the database for later validation.

Dependencies:
    pip install qrcode[pil] pillow

Usage:
    from module8_qr_system.qr_generator import QRGenerator
    gen = QRGenerator()
    result = gen.generate_session_ticket("MH01AB1234", slot_id=5)
"""

import os
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import qrcode
    from PIL import Image, ImageDraw, ImageFont
    QRCODE_AVAILABLE = True
except ImportError:
    logger.warning("qrcode / Pillow not installed. QR images will be skipped.")
    QRCODE_AVAILABLE = False


# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────

QR_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "tickets")
SECRET_SALT   = os.environ.get("QR_SECRET_SALT", "PARKPILOT_QR_SECRET_2024")
QR_VERSION    = 2          # QR code version (1–40, higher = more data)
QR_BOX_SIZE   = 10         # Pixels per QR module
QR_BORDER     = 4          # Quiet zone border modules


# ──────────────────────────────────────────────
# Hash Utility
# ──────────────────────────────────────────────

def _generate_hash(payload: dict) -> str:
    """Generate a SHA-256 hash of the payload + secret salt."""
    raw = json.dumps(payload, sort_keys=True) + SECRET_SALT
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


# ──────────────────────────────────────────────
# QR Generator
# ──────────────────────────────────────────────

class QRGenerator:
    """
    Generates QR code tickets as PNG images and returns metadata.

    Ticket payload (encoded as JSON in QR):
        {
            "type": "session" | "visitor" | "prepaid" | "monthly",
            "plate": "MH01AB1234",
            "slot_id": 5,
            "entry_time": "2024-01-15T10:30:00",
            "expiry_time": "2024-01-15T22:30:00",
            "hash": "<sha256[:32]>"
        }
    """

    def __init__(self, output_dir: str = QR_OUTPUT_DIR):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # ── Public Methods ────────────────────────────────────────────────────

    def generate_session_ticket(
        self,
        plate_number: str,
        slot_id: int,
        entry_time: Optional[datetime] = None,
        duration_hours: float = 12.0,
        save_image: bool = True,
    ) -> dict:
        """
        Generate a parking session QR ticket.

        Returns:
            {
                "qr_code_hash": str,
                "payload": dict,
                "image_path": str | None,
                "expiry_time": str,
            }
        """
        entry = entry_time or datetime.now()
        expiry = entry + timedelta(hours=duration_hours)

        payload = {
            "type": "session",
            "plate": plate_number.upper().strip(),
            "slot_id": slot_id,
            "entry_time": entry.isoformat(),
            "expiry_time": expiry.isoformat(),
        }
        payload["hash"] = _generate_hash(payload)

        image_path = None
        if save_image and QRCODE_AVAILABLE:
            image_path = self._save_qr_image(payload, ticket_type="session")

        logger.info(f"Generated session QR for plate={plate_number} slot={slot_id} hash={payload['hash'][:8]}…")
        return {
            "qr_code_hash": payload["hash"],
            "payload": payload,
            "image_path": image_path,
            "expiry_time": expiry.isoformat(),
        }

    def generate_visitor_pass(
        self,
        visitor_name: str,
        host_plate: str,
        valid_hours: float = 4.0,
        save_image: bool = True,
    ) -> dict:
        """Generate a time-limited visitor QR pass."""
        now = datetime.now()
        expiry = now + timedelta(hours=valid_hours)

        payload = {
            "type": "visitor",
            "visitor_name": visitor_name.strip(),
            "host_plate": host_plate.upper().strip(),
            "issued_at": now.isoformat(),
            "expiry_time": expiry.isoformat(),
            "valid_hours": valid_hours,
        }
        payload["hash"] = _generate_hash(payload)

        image_path = None
        if save_image and QRCODE_AVAILABLE:
            image_path = self._save_qr_image(payload, ticket_type="visitor")

        logger.info(f"Generated visitor pass for {visitor_name} valid until {expiry.isoformat()}")
        return {
            "qr_code_hash": payload["hash"],
            "payload": payload,
            "image_path": image_path,
            "expiry_time": expiry.isoformat(),
        }

    def generate_monthly_pass(
        self,
        plate_number: str,
        lot_id: int,
        start_date: Optional[datetime] = None,
    ) -> dict:
        """Generate a monthly parking pass QR code."""
        start = start_date or datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        expiry = start + timedelta(days=30)

        payload = {
            "type": "monthly",
            "plate": plate_number.upper().strip(),
            "lot_id": lot_id,
            "start_date": start.isoformat(),
            "expiry_time": expiry.isoformat(),
        }
        payload["hash"] = _generate_hash(payload)

        image_path = None
        if QRCODE_AVAILABLE:
            image_path = self._save_qr_image(payload, ticket_type="monthly")

        return {
            "qr_code_hash": payload["hash"],
            "payload": payload,
            "image_path": image_path,
            "expiry_time": expiry.isoformat(),
        }

    def validate_hash(self, payload: dict) -> bool:
        """Re-compute hash from payload and verify it matches."""
        provided_hash = payload.pop("hash", None)
        if not provided_hash:
            return False
        expected = _generate_hash(payload)
        payload["hash"] = provided_hash  # Restore
        return provided_hash == expected

    def is_expired(self, payload: dict) -> bool:
        """Check if the ticket has passed its expiry time."""
        expiry_str = payload.get("expiry_time")
        if not expiry_str:
            return True
        expiry = datetime.fromisoformat(expiry_str)
        return datetime.now() > expiry

    # ── Private Helpers ───────────────────────────────────────────────────

    def _save_qr_image(self, payload: dict, ticket_type: str) -> str:
        """Generate and save QR image, returning file path."""
        qr = qrcode.QRCode(
            version=QR_VERSION,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=QR_BOX_SIZE,
            border=QR_BORDER,
        )
        qr.add_data(json.dumps(payload))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        # Add label banner
        banner_height = 40
        final_img = Image.new("RGB", (img.width, img.height + banner_height), color="#1e293b")
        final_img.paste(img, (0, 0))

        draw = ImageDraw.Draw(final_img)
        label = f"ParkPilot — {ticket_type.upper()} TICKET"
        draw.text((10, img.height + 8), label, fill="white")

        # Save
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{ticket_type}_{ts}.png"
        filepath = os.path.join(self.output_dir, filename)
        final_img.save(filepath, "PNG")
        logger.info(f"QR image saved: {filepath}")
        return filepath


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    gen = QRGenerator()

    print("=== Generating Session Ticket ===")
    result = gen.generate_session_ticket("MH01AB1234", slot_id=5, duration_hours=4)
    print(f"Hash     : {result['qr_code_hash']}")
    print(f"Expires  : {result['expiry_time']}")
    print(f"Image    : {result['image_path']}")
    print(f"Valid?   : {gen.validate_hash(dict(result['payload']))}")

    print("\n=== Generating Visitor Pass ===")
    vp = gen.generate_visitor_pass("Rahul Sharma", "MH01AB1234", valid_hours=3)
    print(f"Hash     : {vp['qr_code_hash']}")
    print(f"Expires  : {vp['expiry_time']}")
