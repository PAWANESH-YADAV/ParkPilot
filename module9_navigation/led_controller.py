"""
Module 9 — LED Panel Controller
=================================
Controls LED guidance panels that direct drivers to available parking
slots via colour-coded arrows and zone indicators.

Hardware communication options:
  1. Serial/USB (Modbus RTU) — for panel controllers
  2. MQTT — for IoT-connected LED panels
  3. REST API — for smart panel hubs
  4. Simulation — for development/testing

Dependencies (optional):
    pip install paho-mqtt pymodbus

Usage:
    from module9_navigation.led_controller import LEDController
    ctrl = LEDController(mode="mqtt", broker="192.168.1.100")
    ctrl.set_slot_available("A3")
    ctrl.show_path(["A5", "A4", "A3"])
"""

import json
import logging
import time
import threading
from typing import Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    logger.warning("paho-mqtt not installed. MQTT mode disabled.")
    MQTT_AVAILABLE = False


# ──────────────────────────────────────────────
# LED State Constants
# ──────────────────────────────────────────────

class LEDColor:
    OFF       = "OFF"
    GREEN     = "GREEN"    # Slot available
    RED       = "RED"      # Slot occupied
    AMBER     = "AMBER"    # Slot reserved
    BLUE      = "BLUE"     # Navigation arrow / guidance
    WHITE     = "WHITE"    # General purpose
    PURPLE    = "PURPLE"   # EV slot available

class LEDAnimation:
    SOLID     = "SOLID"
    BLINK     = "BLINK"
    PULSE     = "PULSE"
    ARROW_L   = "ARROW_LEFT"
    ARROW_R   = "ARROW_RIGHT"
    ARROW_U   = "ARROW_UP"
    ARROW_D   = "ARROW_DOWN"


# ──────────────────────────────────────────────
# LED Command
# ──────────────────────────────────────────────

class LEDCommand:
    """Represents a single command sent to an LED panel."""

    def __init__(
        self,
        panel_id: str,
        color: str = LEDColor.GREEN,
        animation: str = LEDAnimation.SOLID,
        brightness: int = 100,   # 0–100%
        message: str = "",
        duration_s: float = 0,   # 0 = indefinite
    ):
        self.panel_id   = panel_id
        self.color      = color
        self.animation  = animation
        self.brightness = min(100, max(0, brightness))
        self.message    = message
        self.duration_s = duration_s
        self.timestamp  = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "panel_id"  : self.panel_id,
            "color"     : self.color,
            "animation" : self.animation,
            "brightness": self.brightness,
            "message"   : self.message,
            "duration_s": self.duration_s,
            "timestamp" : self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def __repr__(self):
        return f"LEDCommand(panel={self.panel_id}, color={self.color}, anim={self.animation})"


# ──────────────────────────────────────────────
# Panel Registry
# ──────────────────────────────────────────────

class PanelRegistry:
    """Maps slot IDs and waypoints to their physical LED panel IDs."""

    def __init__(self):
        self._panel_map: dict[str, str] = {}  # node_id → panel_id
        self._panel_state: dict[str, dict] = {}  # panel_id → state

    def register(self, node_id: str, panel_id: str):
        self._panel_map[node_id] = panel_id
        self._panel_state[panel_id] = {"color": LEDColor.OFF, "animation": LEDAnimation.SOLID}

    def panel_for(self, node_id: str) -> Optional[str]:
        return self._panel_map.get(node_id)

    def update_state(self, panel_id: str, state: dict):
        self._panel_state[panel_id] = {**self._panel_state.get(panel_id, {}), **state}

    def all_states(self) -> dict:
        return dict(self._panel_state)

    def load_defaults(self):
        """Register default lot LED panels."""
        # Zone A panels
        for i in range(1, 11):
            self.register(f"A{i}", f"LED-A{i:02d}")
        # Zone B panels
        for i in range(1, 11):
            self.register(f"B{i}", f"LED-B{i:02d}")
        # Zone C (EV) panels
        for i in range(1, 6):
            self.register(f"C{i}", f"LED-C{i:02d}")
        # Waypoint displays
        for wp in ["EXIT_NORTH", "EXIT_SOUTH", "ELEVATOR_1", "ELEVATOR_2"]:
            self.register(wp, f"LED-WP-{wp}")


# ──────────────────────────────────────────────
# LED Controller
# ──────────────────────────────────────────────

class LEDController:
    """
    Controls LED panels via MQTT, serial (Modbus), or simulation.

    Modes:
        "mqtt"       — publish commands to MQTT broker
        "modbus"     — send Modbus RTU frames (requires pymodbus)
        "simulation" — log commands, no hardware required
    """

    MQTT_BASE_TOPIC = "parkpilot/led"

    def __init__(
        self,
        mode: str = "simulation",
        broker: str = "localhost",
        broker_port: int = 1883,
        on_command_sent: Optional[Callable[[LEDCommand], None]] = None,
    ):
        self.mode       = mode
        self.broker     = broker
        self.port       = broker_port
        self.registry   = PanelRegistry()
        self.registry.load_defaults()
        self._on_command_sent = on_command_sent
        self._cmd_log: list[LEDCommand] = []
        self._mqtt_client: Optional["mqtt.Client"] = None

        if mode == "mqtt":
            self._connect_mqtt()

    # ── MQTT Connection ───────────────────────────────────────────────────

    def _connect_mqtt(self):
        if not MQTT_AVAILABLE:
            logger.warning("paho-mqtt not installed — falling back to simulation.")
            self.mode = "simulation"
            return
        try:
            self._mqtt_client = mqtt.Client(client_id="parkpilot-led-ctrl")
            self._mqtt_client.connect(self.broker, self.port, keepalive=60)
            self._mqtt_client.loop_start()
            logger.info(f"MQTT connected: {self.broker}:{self.port}")
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}. Falling back to simulation.")
            self.mode = "simulation"

    def disconnect(self):
        if self._mqtt_client:
            self._mqtt_client.loop_stop()
            self._mqtt_client.disconnect()

    # ── Core Send ─────────────────────────────────────────────────────────

    def _send(self, cmd: LEDCommand):
        """Dispatch an LED command via the configured transport."""
        self._cmd_log.append(cmd)
        self.registry.update_state(cmd.panel_id, cmd.to_dict())

        if self.mode == "mqtt" and self._mqtt_client:
            topic = f"{self.MQTT_BASE_TOPIC}/{cmd.panel_id}/set"
            self._mqtt_client.publish(topic, cmd.to_json(), qos=1)
            logger.debug(f"MQTT → {topic} : {cmd}")
        elif self.mode == "simulation":
            logger.info(f"[SIM] LED cmd: {cmd}")
        else:
            logger.debug(f"LED cmd (mode={self.mode}): {cmd}")

        if self._on_command_sent:
            self._on_command_sent(cmd)

    def _send_to_node(self, node_id: str, color: str, animation: str,
                      message: str = "", brightness: int = 100, duration_s: float = 0):
        panel_id = self.registry.panel_for(node_id)
        if not panel_id:
            logger.warning(f"No LED panel registered for node: {node_id}")
            return
        cmd = LEDCommand(panel_id, color, animation, brightness, message, duration_s)
        self._send(cmd)

    # ── Slot Status Commands ──────────────────────────────────────────────

    def set_slot_available(self, slot_id: str, is_ev: bool = False):
        """Turn a slot's LED green (or purple for EV)."""
        color = LEDColor.PURPLE if is_ev else LEDColor.GREEN
        self._send_to_node(slot_id, color, LEDAnimation.SOLID)

    def set_slot_occupied(self, slot_id: str):
        """Turn a slot's LED red."""
        self._send_to_node(slot_id, LEDColor.RED, LEDAnimation.SOLID)

    def set_slot_reserved(self, slot_id: str):
        """Turn a slot's LED amber (blinking)."""
        self._send_to_node(slot_id, LEDColor.AMBER, LEDAnimation.BLINK)

    def set_slot_maintenance(self, slot_id: str):
        """Turn off slot LED (maintenance mode)."""
        self._send_to_node(slot_id, LEDColor.OFF, LEDAnimation.SOLID)

    # ── Batch Status Update ───────────────────────────────────────────────

    def sync_occupancy(self, slot_statuses: list[dict]):
        """
        Update all LED panels from a list of slot status dicts.

        Args:
            slot_statuses: [{slot_id, status, is_ev}]
        """
        for slot in slot_statuses:
            sid    = slot.get("slot_id", "")
            status = slot.get("status", "available")
            is_ev  = slot.get("is_ev", False)

            if status == "available":
                self.set_slot_available(sid, is_ev=is_ev)
            elif status == "occupied":
                self.set_slot_occupied(sid)
            elif status == "reserved":
                self.set_slot_reserved(sid)
            elif status == "maintenance":
                self.set_slot_maintenance(sid)

    # ── Navigation Guidance ───────────────────────────────────────────────

    def show_path(self, path: list[str], blink_target: bool = True):
        """
        Illuminate a navigation path in blue.

        Args:
            path         : Ordered list of node IDs (source → target)
            blink_target : If True, blink the destination slot LED.
        """
        if not path:
            return
        for i, node_id in enumerate(path[:-1]):
            self._send_to_node(node_id, LEDColor.BLUE, LEDAnimation.ARROW_U, duration_s=30)

        # Target slot
        target = path[-1]
        anim = LEDAnimation.BLINK if blink_target else LEDAnimation.SOLID
        self._send_to_node(target, LEDColor.BLUE, anim, message="YOUR SLOT", duration_s=60)
        logger.info(f"Navigation path lit: {' → '.join(path)}")

    def clear_path(self, path: list[str]):
        """Reset a path's LED panels back to normal status."""
        for node_id in path:
            self.set_slot_available(node_id)

    # ── Zone Announcements ────────────────────────────────────────────────

    def announce_zone_full(self, zone: str):
        """Flash all panels in a zone red to signal zone is full."""
        zone_nodes = [k for k in self.registry._panel_map if k.startswith(zone.upper())]
        for node in zone_nodes:
            self._send_to_node(node, LEDColor.RED, LEDAnimation.BLINK, message="FULL")
        logger.info(f"Zone {zone} announced as FULL ({len(zone_nodes)} panels)")

    def announce_lot_available(self, lot_message: str = "PARKING AVAILABLE"):
        """Send a green announcement to entry waypoint panels."""
        for wp in ["EXIT_NORTH", "EXIT_SOUTH"]:
            self._send_to_node(wp, LEDColor.GREEN, LEDAnimation.PULSE, message=lot_message)

    # ── Command Log ───────────────────────────────────────────────────────

    def get_command_log(self, limit: int = 100) -> list[dict]:
        return [c.to_dict() for c in self._cmd_log[-limit:]]

    def get_panel_states(self) -> dict:
        return self.registry.all_states()

    def clear_all(self):
        """Turn off all LED panels."""
        for node_id in self.registry._panel_map:
            self._send_to_node(node_id, LEDColor.OFF, LEDAnimation.SOLID)
        logger.info("All LED panels cleared.")


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    ctrl = LEDController(mode="simulation")

    print("=== Setting Slot Statuses ===")
    for i in range(1, 6):
        ctrl.set_slot_available(f"A{i}")
    for i in range(6, 11):
        ctrl.set_slot_occupied(f"A{i}")
    ctrl.set_slot_reserved("B5")
    ctrl.set_slot_available("C1", is_ev=True)

    print("\n=== Showing Navigation Path ===")
    ctrl.show_path(["A7", "A6", "A5", "ELEVATOR_1", "C2"])

    print("\n=== Announcing Zone B Full ===")
    ctrl.announce_zone_full("B")

    print(f"\nTotal LED commands sent: {len(ctrl.get_command_log())}")
    for cmd in ctrl.get_command_log()[-5:]:
        print(f"  Panel={cmd['panel_id']:12s}  Color={cmd['color']:8s}  Anim={cmd['animation']}")
