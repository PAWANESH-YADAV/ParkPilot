"""
Module 8 — Visitor Pass Generator
====================================
Generates time-limited visitor QR passes with configurable validity
windows, optional host approval, and automatic expiration.

Usage:
    from module8_qr_system.visitor_pass import VisitorPassManager
    mgr = VisitorPassManager()
    pass_info = mgr.issue_pass(
        visitor_name="Rahul Sharma",
        host_plate="MH01AB1234",
        valid_hours=4,
        lot_id=1,
    )
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

from module8_qr_system.qr_generator import QRGenerator

PASSES_DIR = os.path.join(os.path.dirname(__file__), "visitor_passes")


# ──────────────────────────────────────────────
# Visitor Pass Record
# ──────────────────────────────────────────────

class VisitorPass:
    """Represents a single visitor parking pass."""

    STATUS_ACTIVE  = "active"
    STATUS_USED    = "used"
    STATUS_EXPIRED = "expired"
    STATUS_REVOKED = "revoked"

    def __init__(
        self,
        pass_id: str,
        visitor_name: str,
        host_plate: str,
        lot_id: int,
        valid_hours: float,
        slot_number: Optional[str] = None,
    ):
        self.pass_id      = pass_id
        self.visitor_name = visitor_name
        self.host_plate   = host_plate
        self.lot_id       = lot_id
        self.valid_hours  = valid_hours
        self.slot_number  = slot_number
        self.issued_at    = datetime.now()
        self.expiry_time  = self.issued_at + timedelta(hours=valid_hours)
        self.status       = self.STATUS_ACTIVE
        self.qr_hash      = ""
        self.qr_image_path: Optional[str] = None
        self.used_at: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expiry_time

    @property
    def is_valid(self) -> bool:
        return self.status == self.STATUS_ACTIVE and not self.is_expired

    @property
    def minutes_remaining(self) -> float:
        if self.is_expired:
            return 0.0
        return (self.expiry_time - datetime.now()).total_seconds() / 60

    def to_dict(self) -> dict:
        return {
            "pass_id"       : self.pass_id,
            "visitor_name"  : self.visitor_name,
            "host_plate"    : self.host_plate,
            "lot_id"        : self.lot_id,
            "valid_hours"   : self.valid_hours,
            "slot_number"   : self.slot_number,
            "issued_at"     : self.issued_at.isoformat(),
            "expiry_time"   : self.expiry_time.isoformat(),
            "status"        : self.status,
            "qr_hash"       : self.qr_hash,
            "qr_image_path" : self.qr_image_path,
            "used_at"       : self.used_at,
            "is_valid"      : self.is_valid,
            "minutes_remaining": round(self.minutes_remaining, 1),
        }


# ──────────────────────────────────────────────
# Visitor Pass Manager
# ──────────────────────────────────────────────

class VisitorPassManager:
    """
    Issues, validates, and revokes visitor parking passes.
    Maintains an in-memory registry (persist to DB in production).
    """

    MAX_PASSES_PER_HOST   = 3     # Max concurrent passes per host vehicle
    MAX_VALID_HOURS       = 24.0  # Passes cannot exceed 24 hours
    DEFAULT_VALID_HOURS   = 4.0

    def __init__(self):
        self._generator = QRGenerator(output_dir=os.path.join(PASSES_DIR, "qr_images"))
        self._registry: dict[str, VisitorPass] = {}  # pass_id → VisitorPass
        os.makedirs(PASSES_DIR, exist_ok=True)

    # ── Issue ─────────────────────────────────────────────────────────────

    def issue_pass(
        self,
        visitor_name: str,
        host_plate: str,
        lot_id: int = 1,
        valid_hours: float = DEFAULT_VALID_HOURS,
        slot_number: Optional[str] = None,
        save_image: bool = True,
    ) -> dict:
        """
        Issue a new visitor parking pass with a QR code.

        Args:
            visitor_name: Full name of visitor
            host_plate  : License plate of the hosting vehicle/person
            lot_id      : Target parking lot ID
            valid_hours : How long the pass is valid (max 24h)
            slot_number : Optionally pre-assign a specific slot
            save_image  : Whether to save QR image to disk

        Returns:
            Full pass dict including QR hash and image path.

        Raises:
            ValueError: If host has too many active passes.
        """
        # Validate inputs
        valid_hours = min(valid_hours, self.MAX_VALID_HOURS)
        host_plate = host_plate.upper().strip()

        # Check host pass limit
        host_active = self._active_passes_for_host(host_plate)
        if len(host_active) >= self.MAX_PASSES_PER_HOST:
            raise ValueError(
                f"Host {host_plate} already has {len(host_active)} active passes "
                f"(max {self.MAX_PASSES_PER_HOST})."
            )

        # Generate unique pass ID
        pass_id = self._generate_pass_id(visitor_name, host_plate)

        vp = VisitorPass(
            pass_id=pass_id,
            visitor_name=visitor_name.strip(),
            host_plate=host_plate,
            lot_id=lot_id,
            valid_hours=valid_hours,
            slot_number=slot_number,
        )

        # Generate QR code
        qr_result = self._generator.generate_visitor_pass(
            visitor_name=visitor_name,
            host_plate=host_plate,
            valid_hours=valid_hours,
            save_image=save_image,
        )
        vp.qr_hash = qr_result["qr_code_hash"]
        vp.qr_image_path = qr_result.get("image_path")

        self._registry[pass_id] = vp

        logger.info(
            f"Visitor pass issued: {pass_id} | "
            f"Visitor={visitor_name} | Host={host_plate} | "
            f"Valid until {vp.expiry_time.strftime('%H:%M')}"
        )

        return vp.to_dict()

    # ── Validate ──────────────────────────────────────────────────────────

    def validate_pass(self, pass_id: str) -> tuple[bool, str]:
        """
        Validate a visitor pass at the gate.

        Returns:
            (is_valid, reason_string)
        """
        vp = self._registry.get(pass_id)
        if not vp:
            return False, "Pass not found in registry."
        if vp.status == VisitorPass.STATUS_REVOKED:
            return False, "Pass has been revoked."
        if vp.status == VisitorPass.STATUS_USED:
            return False, "Pass has already been used."
        if vp.is_expired:
            vp.status = VisitorPass.STATUS_EXPIRED
            return False, f"Pass expired at {vp.expiry_time.strftime('%H:%M')}."
        return True, f"Valid for {vp.minutes_remaining:.0f} more minutes."

    def mark_used(self, pass_id: str) -> bool:
        """Mark a pass as used (e.g., after gate entry scan)."""
        vp = self._registry.get(pass_id)
        if vp and vp.is_valid:
            vp.status = VisitorPass.STATUS_USED
            vp.used_at = datetime.now().isoformat()
            logger.info(f"Pass marked as used: {pass_id}")
            return True
        return False

    # ── Revoke ────────────────────────────────────────────────────────────

    def revoke_pass(self, pass_id: str, reason: str = "manual revocation") -> bool:
        """Revoke (cancel) a visitor pass."""
        vp = self._registry.get(pass_id)
        if vp:
            vp.status = VisitorPass.STATUS_REVOKED
            logger.info(f"Pass revoked: {pass_id} | Reason: {reason}")
            return True
        return False

    def revoke_all_for_host(self, host_plate: str) -> int:
        """Revoke all active passes for a specific host plate."""
        count = 0
        for vp in self._registry.values():
            if vp.host_plate == host_plate.upper() and vp.is_valid:
                vp.status = VisitorPass.STATUS_REVOKED
                count += 1
        logger.info(f"Revoked {count} passes for host {host_plate}")
        return count

    # ── Query ─────────────────────────────────────────────────────────────

    def get_pass(self, pass_id: str) -> Optional[dict]:
        """Retrieve pass details by ID."""
        vp = self._registry.get(pass_id)
        return vp.to_dict() if vp else None

    def list_active_passes(self) -> list[dict]:
        """Return all currently valid (non-expired, non-revoked) passes."""
        self._expire_old_passes()
        return [vp.to_dict() for vp in self._registry.values() if vp.is_valid]

    def list_all_passes(self) -> list[dict]:
        """Return all passes (all statuses)."""
        return [vp.to_dict() for vp in self._registry.values()]

    # ── Internal ──────────────────────────────────────────────────────────

    def _active_passes_for_host(self, host_plate: str) -> list[VisitorPass]:
        return [
            vp for vp in self._registry.values()
            if vp.host_plate == host_plate and vp.is_valid
        ]

    def _expire_old_passes(self):
        """Update status for any passes that have naturally expired."""
        for vp in self._registry.values():
            if vp.status == VisitorPass.STATUS_ACTIVE and vp.is_expired:
                vp.status = VisitorPass.STATUS_EXPIRED

    def _generate_pass_id(self, visitor_name: str, host_plate: str) -> str:
        import hashlib
        raw = f"{visitor_name}{host_plate}{datetime.now().timestamp()}"
        return "VP" + hashlib.md5(raw.encode()).hexdigest()[:10].upper()

    def stats(self) -> dict:
        """Return summary statistics."""
        self._expire_old_passes()
        all_passes = list(self._registry.values())
        return {
            "total_issued" : len(all_passes),
            "active"       : sum(1 for p in all_passes if p.status == VisitorPass.STATUS_ACTIVE),
            "used"         : sum(1 for p in all_passes if p.status == VisitorPass.STATUS_USED),
            "expired"      : sum(1 for p in all_passes if p.status == VisitorPass.STATUS_EXPIRED),
            "revoked"      : sum(1 for p in all_passes if p.status == VisitorPass.STATUS_REVOKED),
        }


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    mgr = VisitorPassManager()

    print("=== Issuing Visitor Passes ===")
    pass1 = mgr.issue_pass("Rahul Sharma", "MH01AB1234", valid_hours=4)
    print(f"  Pass ID  : {pass1['pass_id']}")
    print(f"  QR Hash  : {pass1['qr_hash']}")
    print(f"  Valid for: {pass1['minutes_remaining']:.0f} min")

    pass2 = mgr.issue_pass("Anjali Kumar", "MH01AB1234", valid_hours=2)

    print("\n=== Validating Pass ===")
    is_valid, reason = mgr.validate_pass(pass1["pass_id"])
    print(f"  Valid: {is_valid} | {reason}")

    print("\n=== Stats ===")
    print(f"  {mgr.stats()}")

    print("\n=== Active Passes ===")
    for p in mgr.list_active_passes():
        print(f"  {p['visitor_name']:20s}  Host: {p['host_plate']}  Expires: {p['expiry_time'][11:16]}")
