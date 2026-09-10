"""
Module 8 — NFC Handler
========================
Handles NFC tap-in/tap-out events for parking entry/exit.
Integrates with the QR system for combined NFC+QR workflows.

Note: This module provides the integration layer for NFC readers
connected via serial/USB or MQTT. Hardware-specific drivers
(libnfc, ACR122U) are loaded via optional imports.

Dependencies:
    pip install pyserial  (for serial NFC readers)

Usage:
    from module8_qr_system.nfc_handler import NFCHandler
    handler = NFCHandler()
    handler.start_listening(on_tap=my_callback)
"""

import time
import json
import logging
import threading
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger(__name__)

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    logger.warning("pyserial not installed. Serial NFC reader mode disabled.")
    SERIAL_AVAILABLE = False


# ──────────────────────────────────────────────
# NFC Event
# ──────────────────────────────────────────────

class NFCEvent:
    """Represents a single NFC tap event."""

    def __init__(
        self,
        uid: str,
        direction: str = "entry",
        reader_id: str = "default",
        raw_data: str = "",
    ):
        self.uid       = uid
        self.direction = direction   # "entry" | "exit"
        self.reader_id = reader_id
        self.raw_data  = raw_data
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "uid"      : self.uid,
            "direction": self.direction,
            "reader_id": self.reader_id,
            "raw_data" : self.raw_data,
            "timestamp": self.timestamp,
        }

    def __repr__(self):
        return f"NFCEvent(uid={self.uid}, dir={self.direction}, ts={self.timestamp})"


# ──────────────────────────────────────────────
# NFC Card Database (in-memory)
# ──────────────────────────────────────────────

class NFCCardRegistry:
    """
    Maps NFC UIDs to registered vehicles / monthly pass holders.
    In production, this should query the main database.
    """

    def __init__(self):
        self._registry: dict[str, dict] = {}

    def register(self, uid: str, plate_number: str, pass_type: str = "monthly"):
        """Register an NFC card UID to a vehicle."""
        self._registry[uid.upper()] = {
            "plate_number": plate_number,
            "pass_type"   : pass_type,
            "registered_at": datetime.now().isoformat(),
        }
        logger.info(f"NFC registered: UID={uid} → Plate={plate_number}")

    def lookup(self, uid: str) -> Optional[dict]:
        """Resolve an NFC UID to vehicle info."""
        return self._registry.get(uid.upper())

    def is_registered(self, uid: str) -> bool:
        return uid.upper() in self._registry

    def deregister(self, uid: str):
        self._registry.pop(uid.upper(), None)

    def all_cards(self) -> list[dict]:
        return [{"uid": uid, **info} for uid, info in self._registry.items()]


# ──────────────────────────────────────────────
# NFC Handler
# ──────────────────────────────────────────────

class NFCHandler:
    """
    Handles NFC tap events from hardware readers or simulated input.

    Architecture:
        1. Start listening (serial reader or simulator)
        2. Each tap calls on_tap(NFCEvent) callback
        3. NFCCardRegistry resolves UID → vehicle
        4. Upstream system handles entry/exit logic
    """

    def __init__(
        self,
        reader_id: str = "ENTRY_READER_01",
        direction: str = "entry",
        baud_rate: int = 9600,
    ):
        self.reader_id   = reader_id
        self.direction   = direction
        self.baud_rate   = baud_rate
        self.registry    = NFCCardRegistry()
        self._running    = False
        self._thread: Optional[threading.Thread] = None
        self._serial: Optional["serial.Serial"] = None
        self._event_log: list[NFCEvent] = []

    # ── Serial Reader Mode ────────────────────────────────────────────────

    def find_serial_port(self) -> Optional[str]:
        """Auto-detect USB NFC reader port."""
        if not SERIAL_AVAILABLE:
            return None
        for port in serial.tools.list_ports.comports():
            desc = port.description.lower()
            if any(kw in desc for kw in ["acr", "nfc", "rfid", "usb serial"]):
                logger.info(f"NFC reader found: {port.device} ({port.description})")
                return port.device
        return None

    def connect_serial(self, port: Optional[str] = None) -> bool:
        """Open serial connection to NFC reader."""
        if not SERIAL_AVAILABLE:
            logger.warning("pyserial not available.")
            return False

        port = port or self.find_serial_port()
        if not port:
            logger.warning("No NFC serial port found.")
            return False

        try:
            self._serial = serial.Serial(port, self.baud_rate, timeout=1.0)
            logger.info(f"Serial NFC reader connected: {port}")
            return True
        except Exception as e:
            logger.error(f"Serial connection failed: {e}")
            return False

    def _read_serial_loop(self, on_tap: Callable[[NFCEvent], None]):
        """Background loop that reads UID from serial reader."""
        while self._running:
            try:
                if self._serial and self._serial.in_waiting > 0:
                    line = self._serial.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        uid = self._parse_uid(line)
                        if uid:
                            event = NFCEvent(uid, self.direction, self.reader_id, line)
                            self._event_log.append(event)
                            on_tap(event)
            except Exception as e:
                logger.error(f"Serial read error: {e}")
            time.sleep(0.05)

    def _parse_uid(self, raw: str) -> Optional[str]:
        """Extract UID from raw serial data. Handles common reader formats."""
        raw = raw.strip().upper()
        # Format 1: plain hex like "04A3F2B1"
        if len(raw) in (8, 14, 20) and all(c in "0123456789ABCDEF" for c in raw):
            return raw
        # Format 2: "UID:04A3F2B1"
        if "UID:" in raw:
            return raw.split("UID:")[-1].strip()[:14]
        return None

    # ── Listening Entry Point ─────────────────────────────────────────────

    def start_listening(
        self,
        on_tap: Callable[[NFCEvent], None],
        port: Optional[str] = None,
        simulate: bool = False,
    ):
        """
        Start background NFC listening thread.

        Args:
            on_tap   : Callback called with each NFCEvent
            port     : Serial port (auto-detected if None)
            simulate : If True, sends simulated tap events (for testing)
        """
        self._running = True

        if simulate:
            target = lambda: self._simulate_taps(on_tap)
        elif self.connect_serial(port):
            target = lambda: self._read_serial_loop(on_tap)
        else:
            logger.warning("No serial reader — switching to simulation mode.")
            target = lambda: self._simulate_taps(on_tap)

        self._thread = threading.Thread(target=target, daemon=True)
        self._thread.start()
        logger.info(f"NFC handler started. Reader: {self.reader_id}")

    def stop_listening(self):
        """Stop the background NFC listening thread."""
        self._running = False
        if self._serial:
            self._serial.close()
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("NFC handler stopped.")

    # ── Simulation ────────────────────────────────────────────────────────

    def _simulate_taps(self, on_tap: Callable[[NFCEvent], None]):
        """Send simulated NFC tap events (for development/testing)."""
        import random
        sample_uids = ["04A3F2B1", "04C7D8E9", "0812FF3A", "0ABCDE12"]

        # Pre-register sample cards
        for i, uid in enumerate(sample_uids):
            self.registry.register(uid, f"MH0{i+1}AB{1000+i*100}")

        logger.info("Simulation mode: sending tap events every 5 seconds.")
        while self._running:
            uid = random.choice(sample_uids)
            direction = random.choice(["entry", "exit"])
            event = NFCEvent(uid, direction, self.reader_id, f"SIM:{uid}")
            self._event_log.append(event)
            on_tap(event)
            time.sleep(5)

    # ── Tap Processing ────────────────────────────────────────────────────

    def process_tap(self, event: NFCEvent) -> dict:
        """
        Resolve an NFC tap to a full action response.

        Returns:
            {
                "uid": str,
                "plate_number": str | None,
                "direction": str,
                "action": "grant_entry"|"grant_exit"|"unknown_card",
                "pass_type": str,
                "timestamp": str,
            }
        """
        card_info = self.registry.lookup(event.uid)
        if card_info:
            return {
                "uid"         : event.uid,
                "plate_number": card_info["plate_number"],
                "direction"   : event.direction,
                "action"      : f"grant_{event.direction}",
                "pass_type"   : card_info["pass_type"],
                "timestamp"   : event.timestamp,
            }
        else:
            logger.warning(f"Unknown NFC card: {event.uid}")
            return {
                "uid"         : event.uid,
                "plate_number": None,
                "direction"   : event.direction,
                "action"      : "unknown_card",
                "pass_type"   : None,
                "timestamp"   : event.timestamp,
            }

    # ── Event Log ─────────────────────────────────────────────────────────

    def get_event_log(self, limit: int = 100) -> list[dict]:
        """Return the most recent tap events."""
        return [e.to_dict() for e in self._event_log[-limit:]]

    def clear_log(self):
        self._event_log.clear()


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    handler = NFCHandler(reader_id="ENTRY_GATE_1", direction="entry")

    def on_nfc_tap(event: NFCEvent):
        result = handler.process_tap(event)
        status = "✅ GRANTED" if "grant" in result["action"] else "❌ UNKNOWN"
        print(f"  {status}  UID={event.uid}  Plate={result['plate_number']}  Dir={event.direction}")

    print("Starting NFC simulation (5 events)…")
    handler.registry.register("04A3F2B1", "MH01AB1234")
    handler.registry.register("04C7D8E9", "MH02CD5678")

    handler.start_listening(on_tap=on_nfc_tap, simulate=True)

    # Let it run for 30 seconds in demo
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        pass
    finally:
        handler.stop_listening()
        print(f"\nTotal tap events logged: {len(handler.get_event_log())}")
