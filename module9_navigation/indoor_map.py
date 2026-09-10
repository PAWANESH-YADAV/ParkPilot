"""
Module 9 — Indoor Map Manager
================================
Manages the SVG-based indoor parking map, exports to JSON for the
frontend, and tracks real-time slot status on the map.

Usage:
    from module9_navigation.indoor_map import IndoorMapManager
    mgr = IndoorMapManager()
    mgr.load_default_map()
    svg_str = mgr.render_svg(highlighted_slots=["A3", "B7"])
"""

import os
import json
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

MAPS_DIR = os.path.join(os.path.dirname(__file__), "maps")


# ──────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────

class SlotMapEntry:
    """Represents a single slot's visual position and current status."""

    STATUS_COLORS = {
        "available"  : "#22c55e",  # Green
        "occupied"   : "#ef4444",  # Red
        "reserved"   : "#f59e0b",  # Amber
        "maintenance": "#6b7280",  # Grey
        "highlighted": "#3b82f6",  # Blue
        "ev"         : "#8b5cf6",  # Purple
    }

    def __init__(
        self,
        slot_id: str,
        x: float, y: float,
        width: float = 40, height: float = 20,
        zone: str = "A",
        level: int = 1,
        status: str = "available",
        is_ev: bool = False,
    ):
        self.slot_id = slot_id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.zone = zone
        self.level = level
        self.status = status
        self.is_ev = is_ev

    @property
    def fill_color(self) -> str:
        if self.is_ev and self.status == "available":
            return self.STATUS_COLORS["ev"]
        return self.STATUS_COLORS.get(self.status, "#22c55e")

    def to_dict(self) -> dict:
        return {
            "slot_id"   : self.slot_id,
            "x"         : self.x,
            "y"         : self.y,
            "width"     : self.width,
            "height"    : self.height,
            "zone"      : self.zone,
            "level"     : self.level,
            "status"    : self.status,
            "is_ev"     : self.is_ev,
            "fill_color": self.fill_color,
        }

    def to_svg_rect(self, highlighted: bool = False) -> str:
        fill = self.STATUS_COLORS["highlighted"] if highlighted else self.fill_color
        label = self.slot_id
        return (
            f'<g id="slot-{self.slot_id}">\n'
            f'  <rect x="{self.x}" y="{self.y}" width="{self.width}" height="{self.height}" '
            f'rx="3" fill="{fill}" stroke="#1e293b" stroke-width="1.5" '
            f'class="parking-slot" data-slot="{self.slot_id}" data-status="{self.status}"/>\n'
            f'  <text x="{self.x + self.width/2}" y="{self.y + self.height/2 + 4}" '
            f'text-anchor="middle" fill="white" font-size="8" font-family="Arial">{label}</text>\n'
            f'</g>\n'
        )


class MapWaypoint:
    """Exit, elevator, staircase, reception, or EV charger on the map."""

    ICONS = {
        "exit"     : "EXIT",
        "elevator" : "LIFT",
        "staircase": "STAIR",
        "reception": "REC",
        "charger"  : "EV⚡",
    }

    def __init__(self, wp_id: str, label: str, x: float, y: float, wp_type: str = "exit"):
        self.wp_id   = wp_id
        self.label   = label
        self.x       = x
        self.y       = y
        self.wp_type = wp_type

    def to_svg(self) -> str:
        icon = self.ICONS.get(self.wp_type, "?")
        return (
            f'<g id="wp-{self.wp_id}">\n'
            f'  <rect x="{self.x}" y="{self.y}" width="50" height="20" rx="4" '
            f'fill="#0f172a" stroke="#64748b" stroke-width="1"/>\n'
            f'  <text x="{self.x + 25}" y="{self.y + 13}" text-anchor="middle" '
            f'fill="#94a3b8" font-size="7" font-family="Arial">{icon}: {self.label}</text>\n'
            f'</g>\n'
        )

    def to_dict(self) -> dict:
        return {"wp_id": self.wp_id, "label": self.label,
                "x": self.x, "y": self.y, "type": self.wp_type}


# ──────────────────────────────────────────────
# Indoor Map Manager
# ──────────────────────────────────────────────

class IndoorMapManager:
    """
    Manages the indoor parking SVG map.
    Supports loading from JSON config, updating slot statuses,
    and rendering to SVG or exporting to dict for the REST API.
    """

    def __init__(self, map_width: int = 600, map_height: int = 400):
        self.width     = map_width
        self.height    = map_height
        self.slots: dict[str, SlotMapEntry]   = {}
        self.waypoints: dict[str, MapWaypoint] = {}
        self._paths: list[dict]               = []  # Navigation path overlays
        os.makedirs(MAPS_DIR, exist_ok=True)

    # ── Loading ───────────────────────────────────────────────────────────

    def load_default_map(self):
        """Load a 2-level, 3-zone default parking layout."""
        # Level 1 — Zone A (10 slots in a row)
        for i in range(1, 11):
            slot_id = f"A{i}"
            self.slots[slot_id] = SlotMapEntry(
                slot_id=slot_id,
                x=20 + (i - 1) * 50,
                y=40,
                zone="A", level=1,
                status="available",
            )

        # Level 1 — Zone B (10 slots, second row)
        for i in range(1, 11):
            slot_id = f"B{i}"
            self.slots[slot_id] = SlotMapEntry(
                slot_id=slot_id,
                x=20 + (i - 1) * 50,
                y=100,
                zone="B", level=1,
                status="available",
            )

        # Level 2 — Zone C (EV slots)
        for i in range(1, 6):
            slot_id = f"C{i}"
            self.slots[slot_id] = SlotMapEntry(
                slot_id=slot_id,
                x=20 + (i - 1) * 60,
                y=200,
                zone="C", level=2,
                status="available",
                is_ev=True,
                width=50, height=22,
            )

        # Waypoints
        self.waypoints["EXIT_NORTH"]  = MapWaypoint("EXIT_NORTH",  "North Exit", 20,  10, "exit")
        self.waypoints["EXIT_SOUTH"]  = MapWaypoint("EXIT_SOUTH",  "South Exit", 450, 160, "exit")
        self.waypoints["ELEVATOR_1"]  = MapWaypoint("ELEVATOR_1",  "Lift L1",   300, 10, "elevator")
        self.waypoints["ELEVATOR_2"]  = MapWaypoint("ELEVATOR_2",  "Lift L2",   300, 190, "elevator")
        self.waypoints["RECEPTION"]   = MapWaypoint("RECEPTION",   "Reception", 20, 170, "reception")
        self.waypoints["EV_CHARGER1"] = MapWaypoint("EV_CHARGER1", "EV Bay 1",  350, 200, "charger")

        logger.info(
            f"Default map loaded: {len(self.slots)} slots, {len(self.waypoints)} waypoints."
        )

    def load_from_json(self, filepath: str):
        """Load map configuration from a JSON file."""
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        for s in data.get("slots", []):
            entry = SlotMapEntry(**s)
            self.slots[entry.slot_id] = entry
        for w in data.get("waypoints", []):
            wp = MapWaypoint(**w)
            self.waypoints[wp.wp_id] = wp
        logger.info(f"Map loaded from {filepath}: {len(self.slots)} slots.")

    # ── Status Updates ────────────────────────────────────────────────────

    def update_slot_status(self, slot_id: str, status: str):
        """Update the occupancy status of a slot."""
        if slot_id in self.slots:
            self.slots[slot_id].status = status
            logger.debug(f"Slot {slot_id} → {status}")

    def batch_update(self, updates: list[dict]):
        """Apply multiple status updates from a list of {slot_id, status} dicts."""
        for u in updates:
            self.update_slot_status(u["slot_id"], u["status"])

    def set_path_overlay(self, path: list[str]):
        """Set a navigation path to highlight on the map."""
        self._paths = path

    # ── Rendering ─────────────────────────────────────────────────────────

    def render_svg(self, highlighted_slots: Optional[list[str]] = None) -> str:
        """
        Render the map as an SVG string.

        Args:
            highlighted_slots: Slot IDs to show in blue (navigation path)

        Returns:
            SVG XML string.
        """
        hl = set(highlighted_slots or [])
        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}">',
            '<rect width="100%" height="100%" fill="#0f172a" rx="8"/>',
            # Level labels
            '<text x="10" y="35" fill="#64748b" font-size="10" font-family="Arial">LEVEL 1</text>',
            '<text x="10" y="195" fill="#64748b" font-size="10" font-family="Arial">LEVEL 2</text>',
            # Level divider
            '<line x1="0" y1="170" x2="600" y2="170" stroke="#1e293b" stroke-width="1"/>',
        ]

        # Waypoints
        for wp in self.waypoints.values():
            lines.append(wp.to_svg())

        # Slots
        for slot in self.slots.values():
            lines.append(slot.to_svg_rect(highlighted=slot.slot_id in hl))

        # Navigation path arrows
        if self._paths:
            path_str = self._build_path_polyline()
            if path_str:
                lines.append(path_str)

        # Legend
        lines += self._render_legend()
        lines.append("</svg>")
        return "\n".join(lines)

    def _build_path_polyline(self) -> str:
        """Build an SVG polyline connecting path slot centers."""
        points = []
        for slot_id in self._paths:
            if slot_id in self.slots:
                s = self.slots[slot_id]
                points.append(f"{s.x + s.width/2},{s.y + s.height/2}")
        if len(points) < 2:
            return ""
        return (
            f'<polyline points="{" ".join(points)}" '
            f'fill="none" stroke="#3b82f6" stroke-width="2" '
            f'stroke-dasharray="4 2" marker-end="url(#arrow)"/>'
        )

    def _render_legend(self) -> list[str]:
        """Return SVG elements for the map legend."""
        items = [
            ("#22c55e", "Available"),
            ("#ef4444", "Occupied"),
            ("#f59e0b", "Reserved"),
            ("#8b5cf6", "EV Slot"),
            ("#3b82f6", "Your Path"),
        ]
        lines = []
        x_start, y_start = 10, self.height - 30
        for i, (color, label) in enumerate(items):
            x = x_start + i * 110
            lines.append(
                f'<rect x="{x}" y="{y_start}" width="12" height="12" rx="2" fill="{color}"/>'
                f'<text x="{x+16}" y="{y_start+10}" fill="#94a3b8" font-size="9" '
                f'font-family="Arial">{label}</text>'
            )
        return lines

    # ── Export ────────────────────────────────────────────────────────────

    def to_api_dict(self) -> dict:
        """Export map state as a dict for the REST API."""
        total   = len(self.slots)
        occupied = sum(1 for s in self.slots.values() if s.status == "occupied")
        return {
            "total_slots"     : total,
            "occupied_slots"  : occupied,
            "available_slots" : total - occupied,
            "occupancy_pct"   : round(occupied / max(1, total), 4),
            "slots"           : [s.to_dict() for s in self.slots.values()],
            "waypoints"       : [w.to_dict() for w in self.waypoints.values()],
            "updated_at"      : datetime.now().isoformat(),
        }

    def save_map_json(self, filepath: Optional[str] = None):
        """Persist map configuration to JSON."""
        filepath = filepath or os.path.join(MAPS_DIR, "default_map.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_api_dict(), f, indent=2)
        logger.info(f"Map config saved: {filepath}")


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    mgr = IndoorMapManager()
    mgr.load_default_map()

    # Simulate some occupancy
    mgr.update_slot_status("A1", "occupied")
    mgr.update_slot_status("A2", "occupied")
    mgr.update_slot_status("B5", "reserved")
    mgr.set_path_overlay(["A7", "A6", "A5", "B5"])

    svg = mgr.render_svg(highlighted_slots=["A7"])
    svg_path = os.path.join(MAPS_DIR, "sample_map.svg")
    os.makedirs(MAPS_DIR, exist_ok=True)
    with open(svg_path, "w") as f:
        f.write(svg)
    print(f"SVG map saved: {svg_path}")

    api_data = mgr.to_api_dict()
    print(f"Total: {api_data['total_slots']} | Occupied: {api_data['occupied_slots']}")
