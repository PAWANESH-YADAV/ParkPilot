"""
Module 9 — BLE Indoor Positioning Tracker
==========================================
Tracks vehicle/user positions inside a multi-level parking garage
using Bluetooth Low Energy (BLE) beacon RSSI trilateration.

Note: BLE scanning requires bleak (cross-platform BLE library).
      On headless systems it falls back to simulated positions.

Dependencies:
    pip install bleak

Usage:
    from module9_navigation.ble_tracker import BLETracker
    tracker = BLETracker()
    await tracker.start()
    pos = tracker.get_position(device_mac="AA:BB:CC:DD:EE:FF")
"""

import asyncio
import math
import logging
import time
import random
from typing import Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from bleak import BleakScanner
    BLEAK_AVAILABLE = True
except ImportError:
    logger.warning("bleak not installed — BLE tracker will use simulation mode.")
    BLEAK_AVAILABLE = False


# ──────────────────────────────────────────────
# Beacon Configuration
# ──────────────────────────────────────────────

# BLE Beacons deployed in the parking lot
# {beacon_id: {x, y, level, tx_power}}
DEFAULT_BEACONS = {
    "BEACON_A1"  : {"x": 25,  "y": 50,  "level": 1, "tx_power": -59, "mac": "AA:00:00:00:00:01"},
    "BEACON_A5"  : {"x": 250, "y": 50,  "level": 1, "tx_power": -59, "mac": "AA:00:00:00:00:02"},
    "BEACON_A10" : {"x": 475, "y": 50,  "level": 1, "tx_power": -59, "mac": "AA:00:00:00:00:03"},
    "BEACON_B5"  : {"x": 250, "y": 120, "level": 1, "tx_power": -59, "mac": "AA:00:00:00:00:04"},
    "BEACON_B10" : {"x": 475, "y": 120, "level": 1, "tx_power": -59, "mac": "AA:00:00:00:00:05"},
    "BEACON_C1"  : {"x": 25,  "y": 250, "level": 2, "tx_power": -59, "mac": "AA:00:00:00:00:06"},
    "BEACON_C3"  : {"x": 150, "y": 250, "level": 2, "tx_power": -59, "mac": "AA:00:00:00:00:07"},
    "BEACON_C5"  : {"x": 275, "y": 250, "level": 2, "tx_power": -59, "mac": "AA:00:00:00:00:08"},
}


# ──────────────────────────────────────────────
# RSSI → Distance Conversion
# ──────────────────────────────────────────────

def rssi_to_distance(rssi: float, tx_power: float = -59, n: float = 2.5) -> float:
    """
    Estimate distance from RSSI using the log-distance path loss model.

    Args:
        rssi     : Received Signal Strength Indicator (dBm, negative)
        tx_power : Calibrated TX power at 1 metre (dBm)
        n        : Path loss exponent (2.0 = free space, 3.0 = indoors)

    Returns:
        Estimated distance in metres.
    """
    if rssi == 0:
        return -1.0
    ratio = rssi / tx_power
    if ratio < 1.0:
        return pow(ratio, 10)
    return (0.89976) * pow(ratio, 7.7095) + 0.111


# ──────────────────────────────────────────────
# Trilateration
# ──────────────────────────────────────────────

def trilaterate(
    beacons: list[dict],
    distances: list[float],
) -> Optional[tuple[float, float]]:
    """
    Estimate 2D position using weighted least-squares trilateration.

    Args:
        beacons  : List of {x, y} beacon positions
        distances: Corresponding distance estimates

    Returns:
        (x, y) estimated position, or None if insufficient data.
    """
    if len(beacons) < 3:
        logger.warning("Need at least 3 beacons for trilateration.")
        return None

    # Weighted centroid as a fast approximation
    weights = [1.0 / max(0.1, d) for d in distances]
    total_w = sum(weights)

    est_x = sum(w * b["x"] for w, b in zip(weights, beacons)) / total_w
    est_y = sum(w * b["y"] for w, b in zip(weights, beacons)) / total_w

    return round(est_x, 1), round(est_y, 1)


# ──────────────────────────────────────────────
# Position Record
# ──────────────────────────────────────────────

class Position:
    def __init__(self, x: float, y: float, level: int = 1,
                 accuracy_m: float = 2.0, source: str = "ble"):
        self.x          = x
        self.y          = y
        self.level      = level
        self.accuracy_m = accuracy_m
        self.source     = source
        self.timestamp  = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "x"         : self.x,
            "y"         : self.y,
            "level"     : self.level,
            "accuracy_m": self.accuracy_m,
            "source"    : self.source,
            "timestamp" : self.timestamp,
        }

    def __repr__(self):
        return f"Position(x={self.x}, y={self.y}, L{self.level}, ±{self.accuracy_m}m)"


# ──────────────────────────────────────────────
# BLE Tracker
# ──────────────────────────────────────────────

class BLETracker:
    """
    Tracks positions of BLE devices (mobile phones / BLE tags)
    by reading beacon RSSI and applying trilateration.
    """

    def __init__(self, beacons: Optional[dict] = None, scan_interval: float = 2.0):
        self.beacons = beacons or DEFAULT_BEACONS
        self.scan_interval = scan_interval
        self._positions: dict[str, Position] = {}   # mac → latest position
        self._rssi_cache: dict[str, dict] = {}      # device_mac → {beacon_mac: rssi}
        self._running = False

    # ── BLE Scanning ──────────────────────────────────────────────────────

    async def start(self):
        """Start continuous BLE scanning."""
        self._running = True
        if BLEAK_AVAILABLE:
            logger.info("Starting BLE scanner…")
            await self._scan_loop()
        else:
            logger.info("Simulation mode: generating synthetic BLE positions.")
            await self._simulate_loop()

    async def stop(self):
        self._running = False

    async def _scan_loop(self):
        """Real BLE scan using bleak."""
        beacon_macs = {info["mac"]: (bid, info) for bid, info in self.beacons.items()}

        while self._running:
            try:
                devices = await BleakScanner.discover(timeout=self.scan_interval)
                for device in devices:
                    if device.address in beacon_macs:
                        # This is one of our beacons — update cached RSSI
                        bid, binfo = beacon_macs[device.address]
                        # We're tracking other devices relative to beacons;
                        # for demonstration, log the beacon RSSI
                        logger.debug(f"Beacon {bid} RSSI: {device.rssi}")
            except Exception as e:
                logger.error(f"BLE scan error: {e}")
            await asyncio.sleep(self.scan_interval)

    async def _simulate_loop(self):
        """Simulate realistic BLE position data for testing."""
        # Start simulated devices at known positions
        simulated_devices = {
            "AA:BB:CC:11:22:33": {"x": 100, "y": 55,  "level": 1, "vx": 2, "vy": 0},
            "AA:BB:CC:44:55:66": {"x": 50,  "y": 120, "level": 1, "vx": 0, "vy": 1},
        }

        while self._running:
            for mac, state in simulated_devices.items():
                # Move simulated device
                state["x"] = (state["x"] + state["vx"] + random.uniform(-1, 1)) % 500
                state["y"] = (state["y"] + state["vy"] + random.uniform(-1, 1)) % 150

                noise_x = random.gauss(0, 2)
                noise_y = random.gauss(0, 2)

                pos = Position(
                    x=round(state["x"] + noise_x, 1),
                    y=round(state["y"] + noise_y, 1),
                    level=state["level"],
                    accuracy_m=round(random.uniform(1.5, 3.5), 1),
                    source="simulated",
                )
                self._positions[mac] = pos

            await asyncio.sleep(self.scan_interval)

    # ── Position Queries ──────────────────────────────────────────────────

    def get_position(self, device_mac: str) -> Optional[Position]:
        """Get the last known position of a device by MAC address."""
        return self._positions.get(device_mac)

    def update_position_from_rssi(
        self,
        device_mac: str,
        rssi_readings: dict[str, float],
    ) -> Optional[Position]:
        """
        Manually update position from RSSI readings.

        Args:
            device_mac   : MAC of the device to locate
            rssi_readings: {beacon_id: rssi_dBm}

        Returns:
            Estimated Position or None.
        """
        beacon_list, dist_list = [], []
        level_votes: dict[int, int] = {}

        for bid, rssi in rssi_readings.items():
            if bid in self.beacons:
                binfo = self.beacons[bid]
                dist = rssi_to_distance(rssi, binfo["tx_power"])
                beacon_list.append(binfo)
                dist_list.append(dist)
                level = binfo["level"]
                level_votes[level] = level_votes.get(level, 0) + 1

        if not beacon_list:
            return None

        coords = trilaterate(beacon_list, dist_list)
        if not coords:
            return None

        # Majority vote for level
        level = max(level_votes, key=level_votes.get)
        accuracy = round(sum(dist_list) / len(dist_list) * 0.3, 1)

        pos = Position(x=coords[0], y=coords[1], level=level,
                       accuracy_m=accuracy, source="ble_rssi")
        self._positions[device_mac] = pos
        return pos

    def all_positions(self) -> dict[str, dict]:
        """Return all tracked device positions."""
        return {mac: pos.to_dict() for mac, pos in self._positions.items()}

    def nearest_slot(self, device_mac: str, slots: list[dict]) -> Optional[str]:
        """
        Find the parking slot nearest to the device's current position.

        Args:
            device_mac: MAC of the tracked device
            slots     : List of {slot_id, x, y, status} dicts

        Returns:
            Nearest slot_id or None.
        """
        pos = self.get_position(device_mac)
        if not pos:
            return None

        nearest_id, nearest_dist = None, float("inf")
        for slot in slots:
            d = math.sqrt((slot["x"] - pos.x) ** 2 + (slot["y"] - pos.y) ** 2)
            if d < nearest_dist:
                nearest_dist = d
                nearest_id = slot["slot_id"]
        return nearest_id


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    async def demo():
        tracker = BLETracker(scan_interval=1.0)
        print("Starting BLE tracker (simulation mode, 8 seconds)…")

        task = asyncio.create_task(tracker.start())

        for _ in range(4):
            await asyncio.sleep(2)
            positions = tracker.all_positions()
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Tracked devices: {len(positions)}")
            for mac, pos in positions.items():
                print(f"  {mac}  →  x={pos['x']}, y={pos['y']}  L{pos['level']}  ±{pos['accuracy_m']}m")

        await tracker.stop()
        task.cancel()

    asyncio.run(demo())
