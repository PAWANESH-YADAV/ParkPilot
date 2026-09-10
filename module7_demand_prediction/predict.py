"""
Module 7 — Demand Predictor (Inference)
=========================================
Loads a trained LSTM model and generates hourly occupancy predictions
for the next 1–24 hours for a given parking lot.

Dependencies:
    pip install tensorflow numpy pandas scikit-learn

Usage:
    from module7_demand_prediction.predict import DemandPredictor
    predictor = DemandPredictor(lot_id=1)
    forecast = predictor.predict_next_hours(hours=6)
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

try:
    import numpy as np
    import pandas as pd
    from sklearn.preprocessing import MinMaxScaler
    import tensorflow as tf
    ML_AVAILABLE = True
except ImportError:
    logger.warning("TensorFlow/numpy not available — predictions will use heuristic fallback.")
    ML_AVAILABLE = False


FEATURES = ["occupancy_pct", "hour", "day_of_week", "is_weekend",
            "is_morning_peak", "is_evening_peak", "occ_rolling_3h"]
LOOK_BACK = 24


# ──────────────────────────────────────────────
# Heuristic Fallback
# ──────────────────────────────────────────────

def heuristic_prediction(dt: datetime) -> float:
    """
    Rule-based occupancy estimate based on time-of-day patterns.
    Used when ML model is unavailable.
    """
    import math
    h   = dt.hour
    dow = dt.weekday()

    if dow < 5:  # Weekday
        if 7 <= h <= 9:
            return 0.55 + 0.35 * math.sin(math.pi * (h - 7) / 2)
        elif 9 <= h <= 17:
            return 0.75 + 0.10 * math.sin(math.pi * (h - 9) / 8)
        elif 17 <= h <= 20:
            return 0.80 - 0.40 * (h - 17) / 3
        return 0.12
    else:  # Weekend
        if 10 <= h <= 20:
            return 0.50 + 0.25 * math.sin(math.pi * (h - 10) / 10)
        return 0.10


# ──────────────────────────────────────────────
# Demand Predictor
# ──────────────────────────────────────────────

class DemandPredictor:
    """
    Loads a trained LSTM model and generates occupancy forecasts.
    Falls back to heuristic estimates if model is not available.
    """

    def __init__(self, lot_id: int = 1):
        self.lot_id   = lot_id
        self._model   = None
        self._scaler  = None
        self._metadata: dict = {}
        self._load()

    def _load(self):
        """Try to load model + scaler from disk."""
        model_path  = os.path.join(MODEL_DIR, f"lstm_lot{self.lot_id}.h5")
        scaler_path = os.path.join(MODEL_DIR, f"scaler_lot{self.lot_id}.pkl")
        meta_path   = os.path.join(MODEL_DIR, f"metadata_lot{self.lot_id}.json")

        if os.path.exists(meta_path):
            with open(meta_path) as f:
                self._metadata = json.load(f)

        if not ML_AVAILABLE:
            logger.info("ML not available — heuristic mode active.")
            return

        if os.path.exists(model_path):
            try:
                self._model = tf.keras.models.load_model(model_path)
                logger.info(f"LSTM model loaded: {model_path}")
            except Exception as e:
                logger.warning(f"Could not load model: {e}")

        if os.path.exists(scaler_path):
            import pickle
            with open(scaler_path, "rb") as f:
                self._scaler = pickle.load(f)
            logger.info("Scaler loaded.")

    # ── Prediction ────────────────────────────────────────────────────────

    def predict_next_hours(
        self,
        hours: int = 6,
        from_time: Optional[datetime] = None,
        recent_window: Optional[list[float]] = None,
    ) -> list[dict]:
        """
        Generate occupancy predictions for the next N hours.

        Args:
            hours        : Number of hours to forecast (1–24)
            from_time    : Start time for prediction (defaults to now)
            recent_window: Last 24 hours occupancy values (0–1).
                           If None, uses heuristic baseline.

        Returns:
            List of hourly forecast dicts:
            {
                "timestamp": ISO string,
                "predicted_occupancy": float (0–1),
                "confidence": float (0–1),
                "demand_level": "low"|"medium"|"high"|"very_high",
                "recommended_price_multiplier": float,
            }
        """
        start = (from_time or datetime.now()).replace(minute=0, second=0, microsecond=0)
        forecasts = []

        use_lstm = (
            ML_AVAILABLE
            and self._model is not None
            and self._scaler is not None
            and recent_window is not None
            and len(recent_window) >= LOOK_BACK
        )

        if use_lstm:
            forecasts = self._lstm_predict(start, hours, recent_window)
        else:
            forecasts = self._heuristic_predict(start, hours)

        return forecasts

    def _lstm_predict(
        self,
        start: datetime,
        hours: int,
        recent_window: list[float],
    ) -> list[dict]:
        """Run inference using the LSTM model."""
        # Build feature matrix from recent window
        feature_rows = []
        for i, occ in enumerate(recent_window[-LOOK_BACK:]):
            ts = start - timedelta(hours=LOOK_BACK - i)
            rolling = float(np.mean(recent_window[max(0, i-2):i+1]))
            feature_rows.append([
                occ, ts.hour, ts.weekday(),
                int(ts.weekday() >= 5),
                int(8 <= ts.hour <= 10),
                int(17 <= ts.hour <= 20),
                rolling,
            ])

        window_array = np.array(feature_rows, dtype=float)
        window_scaled = self._scaler.transform(window_array)

        forecasts = []
        current_window = window_scaled.copy()

        for i in range(hours):
            x = current_window[-LOOK_BACK:].reshape(1, LOOK_BACK, len(FEATURES))
            pred_scaled = float(self._model.predict(x, verbose=0)[0][0])
            pred_occ = max(0.0, min(1.0, pred_scaled))

            ts = start + timedelta(hours=i + 1)
            rolling = float(np.mean([row[0] for row in current_window[-3:]]))

            new_row_raw = [
                pred_occ, ts.hour, ts.weekday(),
                int(ts.weekday() >= 5),
                int(8 <= ts.hour <= 10),
                int(17 <= ts.hour <= 20),
                rolling,
            ]
            new_row_scaled = self._scaler.transform([new_row_raw])
            current_window = np.vstack([current_window, new_row_scaled])

            forecasts.append(self._build_forecast_entry(ts, pred_occ, confidence=0.85))

        return forecasts

    def _heuristic_predict(self, start: datetime, hours: int) -> list[dict]:
        """Generate heuristic-based predictions without ML."""
        import random
        random.seed(42)
        forecasts = []
        for i in range(hours):
            ts = start + timedelta(hours=i + 1)
            base = heuristic_prediction(ts)
            noise = random.gauss(0, 0.03)
            occ = round(max(0.0, min(1.0, base + noise)), 4)
            forecasts.append(self._build_forecast_entry(ts, occ, confidence=0.60))
        return forecasts

    def _build_forecast_entry(
        self, ts: datetime, occ: float, confidence: float
    ) -> dict:
        """Build a standardised forecast dict from raw occupancy value."""
        if occ < 0.40:
            demand = "low"
            price_mult = 0.80
        elif occ < 0.65:
            demand = "medium"
            price_mult = 1.00
        elif occ < 0.85:
            demand = "high"
            price_mult = 1.30
        else:
            demand = "very_high"
            price_mult = 1.60

        return {
            "timestamp"                    : ts.isoformat(),
            "predicted_occupancy"          : round(occ, 4),
            "predicted_occupancy_pct"      : round(occ * 100, 1),
            "confidence"                   : confidence,
            "demand_level"                 : demand,
            "recommended_price_multiplier" : price_mult,
        }

    # ── Summary ───────────────────────────────────────────────────────────

    def daily_summary(self, date: Optional[datetime] = None) -> dict:
        """Return a summary of predictions for the rest of the current day."""
        now = date or datetime.now()
        end_of_day = now.replace(hour=23, minute=0, second=0, microsecond=0)
        remaining_hours = max(1, int((end_of_day - now).total_seconds() // 3600))

        forecasts = self.predict_next_hours(hours=min(remaining_hours, 12))
        if not forecasts:
            return {}

        occupancies = [f["predicted_occupancy"] for f in forecasts]
        peak_idx = int(max(range(len(occupancies)), key=lambda i: occupancies[i]))

        return {
            "lot_id"          : self.lot_id,
            "summary_date"    : now.strftime("%Y-%m-%d"),
            "hours_forecast"  : len(forecasts),
            "avg_occupancy"   : round(sum(occupancies) / len(occupancies), 4),
            "peak_occupancy"  : round(max(occupancies), 4),
            "peak_hour"       : forecasts[peak_idx]["timestamp"],
            "model_available" : self._model is not None,
            "forecasts"       : forecasts,
        }


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    predictor = DemandPredictor(lot_id=1)

    print("=== 6-Hour Forecast ===")
    forecast = predictor.predict_next_hours(hours=6)
    for f in forecast:
        bar = "█" * int(f["predicted_occupancy"] * 20)
        print(
            f"  {f['timestamp'][11:16]}  "
            f"{f['predicted_occupancy_pct']:5.1f}%  {bar:<20}  "
            f"[{f['demand_level']:9s}]  ×{f['recommended_price_multiplier']}"
        )

    print("\n=== Daily Summary ===")
    summary = predictor.daily_summary()
    print(f"  Avg occupancy : {summary.get('avg_occupancy', 0):.1%}")
    print(f"  Peak occupancy: {summary.get('peak_occupancy', 0):.1%}")
    print(f"  Peak hour     : {summary.get('peak_hour', 'N/A')}")
