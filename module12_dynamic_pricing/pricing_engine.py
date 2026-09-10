"""
Module 12 — Dynamic Pricing Engine
=====================================
Computes real-time parking prices based on occupancy, time-of-day,
weather, local events, and demand forecasts using a rule-based engine
with optional ML price prediction model overlay.

Usage:
    from module12_dynamic_pricing.pricing_engine import PricingEngine
    engine = PricingEngine(base_rate=30.0)
    result = engine.compute_price(occupancy_pct=0.82, hour=18, day_of_week=4)
"""

import os
import json
import logging
import pickle
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "pricing_model.pkl")

try:
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


# ──────────────────────────────────────────────
# Pricing Rules Config
# ──────────────────────────────────────────────

class PricingConfig:
    """Configurable parameters for the pricing engine."""

    def __init__(
        self,
        base_rate: float = 30.0,          # ₹ per hour base
        min_rate: float  = 15.0,          # Floor price
        max_rate: float  = 120.0,         # Ceiling price
        # Occupancy multiplier bands
        occ_low_threshold:  float = 0.40, # Below → discount
        occ_high_threshold: float = 0.70, # Above → surge
        occ_very_high:      float = 0.85, # High surge zone
        low_occ_discount:   float = 0.80, # 20% discount
        high_occ_surge:     float = 1.30, # 30% surge
        very_high_surge:    float = 1.60, # 60% surge
        # Time-of-day multipliers
        peak_morning_mult:  float = 1.20, # 8–10 AM
        peak_evening_mult:  float = 1.25, # 5–8 PM
        night_mult:         float = 0.75, # 10 PM – 6 AM
        weekend_mult:       float = 1.10, # Saturday & Sunday
        # EV / handicap discounts
        ev_discount:        float = 0.10, # 10% off for EVs
        handicap_discount:  float = 0.50, # 50% off for handicap
    ):
        self.base_rate            = base_rate
        self.min_rate             = min_rate
        self.max_rate             = max_rate
        self.occ_low_threshold    = occ_low_threshold
        self.occ_high_threshold   = occ_high_threshold
        self.occ_very_high        = occ_very_high
        self.low_occ_discount     = low_occ_discount
        self.high_occ_surge       = high_occ_surge
        self.very_high_surge      = very_high_surge
        self.peak_morning_mult    = peak_morning_mult
        self.peak_evening_mult    = peak_evening_mult
        self.night_mult           = night_mult
        self.weekend_mult         = weekend_mult
        self.ev_discount          = ev_discount
        self.handicap_discount    = handicap_discount


# ──────────────────────────────────────────────
# Price Breakdown
# ──────────────────────────────────────────────

class PriceBreakdown:
    """Detailed explanation of how a price was computed."""

    def __init__(self):
        self.base_rate: float = 0.0
        self.occupancy_multiplier: float = 1.0
        self.time_multiplier: float = 1.0
        self.weather_multiplier: float = 1.0
        self.event_multiplier: float = 1.0
        self.ev_discount: float = 0.0
        self.handicap_discount: float = 0.0
        self.ml_adjustment: float = 0.0
        self.final_rate: float = 0.0
        self.reasons: list[str] = []

    def effective_multiplier(self) -> float:
        return (
            self.occupancy_multiplier *
            self.time_multiplier *
            self.weather_multiplier *
            self.event_multiplier
        )

    def to_dict(self) -> dict:
        return {
            "base_rate"             : round(self.base_rate, 2),
            "occupancy_multiplier"  : round(self.occupancy_multiplier, 3),
            "time_multiplier"       : round(self.time_multiplier, 3),
            "weather_multiplier"    : round(self.weather_multiplier, 3),
            "event_multiplier"      : round(self.event_multiplier, 3),
            "effective_multiplier"  : round(self.effective_multiplier(), 3),
            "ev_discount"           : round(self.ev_discount, 2),
            "handicap_discount"     : round(self.handicap_discount, 2),
            "ml_adjustment"         : round(self.ml_adjustment, 2),
            "final_rate"            : round(self.final_rate, 2),
            "reasons"               : self.reasons,
        }


# ──────────────────────────────────────────────
# Pricing Engine
# ──────────────────────────────────────────────

class PricingEngine:
    """
    Computes real-time dynamic parking prices.

    Pipeline:
        1. Base rate (lot config)
        2. Occupancy multiplier (rule-based)
        3. Time-of-day multiplier
        4. Weather factor (from demand_signals)
        5. Event factor (from demand_signals)
        6. Vehicle discounts (EV / handicap)
        7. Optional ML fine-tuning
        8. Clamp to [min_rate, max_rate]
    """

    def __init__(
        self,
        base_rate: float = 30.0,
        config: Optional[PricingConfig] = None,
        load_ml_model: bool = True,
    ):
        self.config = config or PricingConfig(base_rate=base_rate)
        self._ml_model = None
        self._price_history: list[dict] = []

        if load_ml_model:
            self._load_model()

    # ── Core Computation ──────────────────────────────────────────────────

    def compute_price(
        self,
        occupancy_pct: float,             # 0.0 – 1.0
        hour: Optional[int] = None,
        day_of_week: Optional[int] = None,  # 0=Mon … 6=Sun
        weather_factor: float = 1.0,
        event_factor: float = 1.0,
        vehicle_type: str = "car",        # car, ev, handicap, bike, truck
        lot_id: int = 1,
        forecast_occupancy: Optional[float] = None,  # 1h-ahead prediction
    ) -> dict:
        """
        Compute the effective parking rate.

        Returns:
            {
                "final_rate": float,
                "surge_multiplier": float,
                "demand_level": str,
                "breakdown": dict,
                "valid_until": str,
                "computed_at": str,
            }
        """
        now = datetime.now()
        h   = hour if hour is not None else now.hour
        dow = day_of_week if day_of_week is not None else now.weekday()

        bd = PriceBreakdown()
        bd.base_rate = self.config.base_rate

        # 1. Occupancy multiplier
        bd.occupancy_multiplier, occ_reason = self._occupancy_mult(occupancy_pct)
        bd.reasons.append(occ_reason)

        # 2. Time-of-day multiplier
        bd.time_multiplier, time_reason = self._time_mult(h, dow)
        bd.reasons.append(time_reason)

        # 3. External factors
        if weather_factor != 1.0:
            bd.weather_multiplier = weather_factor
            bd.reasons.append(f"Weather factor: ×{weather_factor:.2f}")
        if event_factor != 1.0:
            bd.event_multiplier = event_factor
            bd.reasons.append(f"Event nearby: ×{event_factor:.2f}")

        # 4. Raw price before discounts
        raw_price = bd.base_rate * bd.effective_multiplier()

        # 5. Vehicle discounts
        vtype = vehicle_type.lower()
        if vtype == "ev":
            bd.ev_discount = raw_price * self.config.ev_discount
            bd.reasons.append(f"EV discount: −{self.config.ev_discount:.0%}")
        elif vtype == "handicap":
            bd.handicap_discount = raw_price * self.config.handicap_discount
            bd.reasons.append(f"Handicap discount: −{self.config.handicap_discount:.0%}")
        elif vtype == "bike":
            raw_price *= 0.50
            bd.reasons.append("Bike rate: ×0.50")
        elif vtype == "truck":
            raw_price *= 1.50
            bd.reasons.append("Truck rate: ×1.50")

        adjusted = raw_price - bd.ev_discount - bd.handicap_discount

        # 6. ML fine-tuning
        if self._ml_model and ML_AVAILABLE and forecast_occupancy is not None:
            try:
                features = [[occupancy_pct, h, dow, forecast_occupancy,
                             weather_factor, event_factor]]
                ml_pred = float(self._ml_model.predict(features)[0])
                bd.ml_adjustment = round(ml_pred - adjusted, 2)
                adjusted = ml_pred
                bd.reasons.append(f"ML tuning: adjustment {bd.ml_adjustment:+.2f}")
            except Exception as e:
                logger.warning(f"ML pricing inference failed: {e}")

        # 7. Clamp to bounds
        final = max(self.config.min_rate, min(self.config.max_rate, adjusted))
        bd.final_rate = round(final, 2)

        # Surge multiplier
        surge = round(final / self.config.base_rate, 3)
        demand = self._demand_level(occupancy_pct)

        result = {
            "final_rate"       : bd.final_rate,
            "surge_multiplier" : surge,
            "demand_level"     : demand,
            "breakdown"        : bd.to_dict(),
            "valid_until"      : (now + timedelta(minutes=15)).isoformat(),
            "computed_at"      : now.isoformat(),
            "lot_id"           : lot_id,
        }

        self._price_history.append(result)
        logger.info(
            f"Price computed: ₹{bd.final_rate} (surge ×{surge}) | "
            f"occ={occupancy_pct:.0%} | {demand}"
        )
        return result

    # ── Batch Computation ─────────────────────────────────────────────────

    def forecast_prices(
        self, occupancy_forecast: list[float], from_hour: Optional[int] = None
    ) -> list[dict]:
        """
        Compute prices for an occupancy forecast list.

        Args:
            occupancy_forecast: Hourly occupancy predictions (0–1)
            from_hour: Starting hour (defaults to current hour + 1)

        Returns:
            List of price dicts with timestamp.
        """
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        start_h = from_hour if from_hour is not None else now.hour

        results = []
        for i, occ in enumerate(occupancy_forecast):
            ts = now + timedelta(hours=i + 1)
            price = self.compute_price(
                occupancy_pct=occ,
                hour=ts.hour,
                day_of_week=ts.weekday(),
            )
            price["timestamp"] = ts.isoformat()
            results.append(price)
        return results

    # ── Rule Helpers ──────────────────────────────────────────────────────

    def _occupancy_mult(self, occ: float) -> tuple[float, str]:
        cfg = self.config
        if occ >= cfg.occ_very_high:
            return cfg.very_high_surge, f"High demand ({occ:.0%} occupied): ×{cfg.very_high_surge}"
        if occ >= cfg.occ_high_threshold:
            return cfg.high_occ_surge, f"Surge demand ({occ:.0%} occupied): ×{cfg.high_occ_surge}"
        if occ < cfg.occ_low_threshold:
            return cfg.low_occ_discount, f"Low demand ({occ:.0%} occupied): ×{cfg.low_occ_discount}"
        return 1.0, f"Normal demand ({occ:.0%} occupied): ×1.00"

    def _time_mult(self, hour: int, day_of_week: int) -> tuple[float, str]:
        cfg = self.config
        is_weekend = day_of_week >= 5
        mult = 1.0
        reason_parts = []

        if 8 <= hour <= 10:
            mult *= cfg.peak_morning_mult
            reason_parts.append(f"Morning peak ×{cfg.peak_morning_mult}")
        elif 17 <= hour <= 20:
            mult *= cfg.peak_evening_mult
            reason_parts.append(f"Evening peak ×{cfg.peak_evening_mult}")
        elif hour < 6 or hour >= 22:
            mult *= cfg.night_mult
            reason_parts.append(f"Night rate ×{cfg.night_mult}")

        if is_weekend:
            mult *= cfg.weekend_mult
            reason_parts.append(f"Weekend ×{cfg.weekend_mult}")

        return round(mult, 3), f"Time: {', '.join(reason_parts) or 'standard hours'}"

    def _demand_level(self, occ: float) -> str:
        if occ >= self.config.occ_very_high:
            return "very_high"
        if occ >= self.config.occ_high_threshold:
            return "high"
        if occ < self.config.occ_low_threshold:
            return "low"
        return "medium"

    # ── ML Model ──────────────────────────────────────────────────────────

    def _load_model(self):
        """Load pre-trained pricing ML model if available."""
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    self._ml_model = pickle.load(f)
                logger.info(f"Pricing ML model loaded: {MODEL_PATH}")
            except Exception as e:
                logger.warning(f"Could not load pricing model: {e}")

    def save_stub_model(self):
        """Save a LinearRegression stub model for testing."""
        if not ML_AVAILABLE:
            return
        from sklearn.linear_model import LinearRegression
        import numpy as np

        X = np.random.rand(500, 6)
        y = 30.0 + X[:, 0] * 50 + X[:, 1] * 5
        model = LinearRegression().fit(X, y)

        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model, f)
        logger.info(f"Stub pricing model saved: {MODEL_PATH}")
        return MODEL_PATH

    # ── History ───────────────────────────────────────────────────────────

    def price_history(self, limit: int = 50) -> list[dict]:
        return self._price_history[-limit:]

    def avg_price_today(self) -> float:
        if not self._price_history:
            return self.config.base_rate
        return round(
            sum(p["final_rate"] for p in self._price_history) / len(self._price_history), 2
        )


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    engine = PricingEngine(base_rate=30.0)

    scenarios = [
        {"occupancy_pct": 0.20, "hour": 14, "day_of_week": 1, "label": "Low occupancy, afternoon"},
        {"occupancy_pct": 0.75, "hour": 9,  "day_of_week": 2, "label": "High occ, morning peak"},
        {"occupancy_pct": 0.90, "hour": 18, "day_of_week": 4, "label": "Very high, evening peak"},
        {"occupancy_pct": 0.60, "hour": 23, "day_of_week": 5, "label": "Night weekend"},
        {"occupancy_pct": 0.80, "hour": 18, "day_of_week": 3,
         "vehicle_type": "ev", "label": "EV surge"},
    ]

    print("=== Dynamic Pricing Scenarios ===\n")
    print(f"{'Label':40s} {'Occ%':6s} {'Rate':8s} {'Surge':8s} {'Demand'}")
    print("─" * 80)
    for s in scenarios:
        label = s.pop("label")
        result = engine.compute_price(**s)
        print(
            f"{label:40s} "
            f"{s.get('occupancy_pct', 0):.0%}   "
            f"₹{result['final_rate']:6.1f}  "
            f"×{result['surge_multiplier']:4.2f}   "
            f"{result['demand_level']}"
        )
        for r in result["breakdown"]["reasons"]:
            print(f"  └ {r}")
