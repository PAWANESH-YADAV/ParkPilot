"""
Module 12 — Price Display
===========================
Pushes real-time price updates to display boards, mobile apps,
and external systems via WebSocket, MQTT, or REST callbacks.

Usage:
    from module12_dynamic_pricing.price_display import PriceDisplayManager
    mgr = PriceDisplayManager()
    mgr.push_price_update(lot_id=1, rate=45.0, surge_mult=1.5)
"""

import json
import logging
import time
import threading
from datetime import datetime
from typing import Optional, Callable

logger = logging.getLogger(__name__)

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

try:
    import websockets
    import asyncio
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False


# ──────────────────────────────────────────────
# Price Update Message
# ──────────────────────────────────────────────

class PriceUpdate:
    """Represents a single price update event."""

    DEMAND_COLORS = {
        "low"      : "#22c55e",  # Green
        "medium"   : "#f59e0b",  # Amber
        "high"     : "#ef4444",  # Red
        "very_high": "#dc2626",  # Dark Red
    }

    def __init__(
        self,
        lot_id: int,
        rate: float,
        surge_multiplier: float = 1.0,
        demand_level: str = "medium",
        valid_until: Optional[str] = None,
        breakdown: Optional[dict] = None,
    ):
        self.lot_id          = lot_id
        self.rate            = round(rate, 2)
        self.surge_multiplier = round(surge_multiplier, 3)
        self.demand_level    = demand_level
        self.display_color   = self.DEMAND_COLORS.get(demand_level, "#f59e0b")
        self.valid_until     = valid_until or (
            datetime.now().strftime("%Y-%m-%dT%H:%M:00")
        )
        self.breakdown       = breakdown
        self.timestamp       = datetime.now().isoformat()

    @property
    def display_text(self) -> str:
        if self.surge_multiplier > 1.2:
            return f"₹{self.rate}/hr ⚡ SURGE"
        if self.surge_multiplier < 0.9:
            return f"₹{self.rate}/hr 🟢 DISCOUNT"
        return f"₹{self.rate}/hr"

    def to_dict(self) -> dict:
        return {
            "lot_id"          : self.lot_id,
            "rate"            : self.rate,
            "surge_multiplier": self.surge_multiplier,
            "demand_level"    : self.demand_level,
            "display_color"   : self.display_color,
            "display_text"    : self.display_text,
            "valid_until"     : self.valid_until,
            "timestamp"       : self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def __repr__(self):
        return f"PriceUpdate(lot={self.lot_id}, rate=₹{self.rate}, surge=×{self.surge_multiplier})"


# ──────────────────────────────────────────────
# Price Display Manager
# ──────────────────────────────────────────────

class PriceDisplayManager:
    """
    Distributes price updates to all registered display endpoints.
    Supports: MQTT, REST callback, WebSocket, and in-process subscribers.
    """

    MQTT_TOPIC_TEMPLATE = "parkpilot/pricing/{lot_id}/rate"

    def __init__(
        self,
        mode: str = "simulation",  # "mqtt" | "rest" | "simulation"
        mqtt_broker: str = "localhost",
        mqtt_port: int = 1883,
        rest_webhook_url: Optional[str] = None,
    ):
        self.mode             = mode
        self.mqtt_broker      = mqtt_broker
        self.mqtt_port        = mqtt_port
        self.rest_webhook_url = rest_webhook_url
        self._mqtt_client: Optional["mqtt.Client"] = None
        self._subscribers: list[Callable[[PriceUpdate], None]] = []
        self._history: list[PriceUpdate] = []

        if mode == "mqtt":
            self._init_mqtt()

    # ── MQTT ──────────────────────────────────────────────────────────────

    def _init_mqtt(self):
        if not MQTT_AVAILABLE:
            logger.warning("paho-mqtt not installed. MQTT mode disabled.")
            self.mode = "simulation"
            return
        try:
            self._mqtt_client = mqtt.Client("parkpilot-price-display")
            self._mqtt_client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
            self._mqtt_client.loop_start()
            logger.info(f"Price display MQTT connected: {self.mqtt_broker}:{self.mqtt_port}")
        except Exception as e:
            logger.error(f"MQTT price display connection failed: {e}")
            self.mode = "simulation"

    # ── Core Push ─────────────────────────────────────────────────────────

    def push_price_update(
        self,
        lot_id: int,
        rate: float,
        surge_multiplier: float = 1.0,
        demand_level: str = "medium",
        valid_until: Optional[str] = None,
        breakdown: Optional[dict] = None,
    ) -> PriceUpdate:
        """
        Push a new price to all connected display channels.

        Returns:
            The PriceUpdate object that was sent.
        """
        update = PriceUpdate(
            lot_id=lot_id,
            rate=rate,
            surge_multiplier=surge_multiplier,
            demand_level=demand_level,
            valid_until=valid_until,
            breakdown=breakdown,
        )

        # Store history
        self._history.append(update)

        # Dispatch to all channels
        self._dispatch(update)

        logger.info(f"Price pushed: {update}")
        return update

    def _dispatch(self, update: PriceUpdate):
        """Send price update to all configured channels."""

        # 1. MQTT
        if self.mode == "mqtt" and self._mqtt_client:
            topic = self.MQTT_TOPIC_TEMPLATE.format(lot_id=update.lot_id)
            self._mqtt_client.publish(topic, update.to_json(), qos=1, retain=True)
            logger.debug(f"MQTT price → {topic}: ₹{update.rate}")

        # 2. REST webhook
        if self.rest_webhook_url:
            self._rest_push(update)

        # 3. In-process subscribers
        for cb in self._subscribers:
            try:
                cb(update)
            except Exception as e:
                logger.warning(f"Subscriber callback error: {e}")

        # 4. Simulation log
        if self.mode == "simulation":
            logger.info(
                f"[SIM] Price display: {update.display_text} | "
                f"Demand={update.demand_level} | "
                f"Color={update.display_color}"
            )

    def _rest_push(self, update: PriceUpdate):
        """POST price update to REST webhook."""
        try:
            import requests
            resp = requests.post(
                self.rest_webhook_url,
                json=update.to_dict(),
                timeout=3,
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code not in (200, 201, 202, 204):
                logger.warning(f"Webhook returned {resp.status_code}")
        except Exception as e:
            logger.warning(f"REST webhook push failed: {e}")

    # ── Subscriptions ─────────────────────────────────────────────────────

    def subscribe(self, callback: Callable[[PriceUpdate], None]):
        """Register an in-process callback to receive price updates."""
        self._subscribers.append(callback)
        logger.debug(f"Price display subscriber added: {callback.__name__}")

    def unsubscribe(self, callback: Callable[[PriceUpdate], None]):
        """Remove a subscriber callback."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    # ── Auto-Refresh ──────────────────────────────────────────────────────

    def start_auto_refresh(
        self,
        pricing_fn: Callable[[], dict],
        lot_id: int,
        interval_seconds: float = 300.0,  # Every 5 minutes
    ):
        """
        Start a background thread that periodically re-computes and pushes prices.

        Args:
            pricing_fn      : Callable returning {rate, surge_multiplier, demand_level}
            lot_id          : Lot to push prices for
            interval_seconds: Refresh interval (default 5 minutes)
        """
        def _refresh_loop():
            while True:
                try:
                    price_data = pricing_fn()
                    self.push_price_update(
                        lot_id=lot_id,
                        rate=price_data.get("final_rate", 30.0),
                        surge_multiplier=price_data.get("surge_multiplier", 1.0),
                        demand_level=price_data.get("demand_level", "medium"),
                    )
                except Exception as e:
                    logger.error(f"Auto-refresh error: {e}")
                time.sleep(interval_seconds)

        t = threading.Thread(target=_refresh_loop, daemon=True)
        t.start()
        logger.info(f"Price auto-refresh started for lot {lot_id} every {interval_seconds}s")

    # ── History & Analytics ───────────────────────────────────────────────

    def get_price_history(self, lot_id: Optional[int] = None, limit: int = 100) -> list[dict]:
        """Return recent price update history."""
        history = self._history
        if lot_id is not None:
            history = [h for h in history if h.lot_id == lot_id]
        return [h.to_dict() for h in history[-limit:]]

    def avg_surge_today(self, lot_id: int) -> float:
        """Compute average surge multiplier pushed today."""
        today = datetime.now().date().isoformat()
        relevant = [
            h.surge_multiplier for h in self._history
            if h.lot_id == lot_id and h.timestamp.startswith(today)
        ]
        if not relevant:
            return 1.0
        return round(sum(relevant) / len(relevant), 3)

    def get_current_price(self, lot_id: int) -> Optional[dict]:
        """Return the most recent price for a lot."""
        for update in reversed(self._history):
            if update.lot_id == lot_id:
                return update.to_dict()
        return None

    def disconnect(self):
        if self._mqtt_client:
            self._mqtt_client.loop_stop()
            self._mqtt_client.disconnect()


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    mgr = PriceDisplayManager(mode="simulation")

    # Subscribe to print updates
    def print_update(update: PriceUpdate):
        print(f"  📟 Display: {update.display_text:25s} | {update.demand_level:9s} | {update.display_color}")

    mgr.subscribe(print_update)

    print("=== Price Display Demo ===\n")
    scenarios = [
        (30.0, 1.0,  "low",       "Low occupancy — normal rate"),
        (39.0, 1.3,  "high",      "Peak demand — surge active"),
        (48.0, 1.6,  "very_high", "Very high demand — max surge"),
        (24.0, 0.8,  "low",       "Late night — discount rate"),
    ]

    for rate, surge, demand, label in scenarios:
        print(f"  [{label}]")
        mgr.push_price_update(lot_id=1, rate=rate, surge_multiplier=surge, demand_level=demand)

    print(f"\nHistory: {len(mgr.get_price_history())} updates pushed")
    print(f"Avg surge today: ×{mgr.avg_surge_today(lot_id=1)}")
