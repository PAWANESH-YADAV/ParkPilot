"""
Module 12 — Generate Pricing Model
Creates and serializes pricing_model.pkl using scikit-learn.
Run this once to generate the pre-trained model file.

Usage:
    cd PARKPILOT
    python module12_dynamic_pricing/generate_model.py
"""

import os
import pickle
import numpy as np
from datetime import datetime

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[WARNING] scikit-learn not installed. Saving rule-based fallback model.")


# ─── Synthetic Training Data Generation ──────────────────────────────────────

def generate_training_data(n_samples: int = 5000):
    """
    Generate synthetic parking pricing training data.
    Features: [occupancy_pct, hour_of_day, day_of_week, weather_factor, event_factor, is_weekend]
    Target: effective_price_multiplier (0.5 to 3.0)
    """
    np.random.seed(42)

    occupancy = np.random.uniform(0, 100, n_samples)
    hour = np.random.randint(0, 24, n_samples)
    day_of_week = np.random.randint(0, 7, n_samples)
    weather = np.random.choice([1.0, 1.1, 1.2, 1.3, 0.9], n_samples,
                                p=[0.5, 0.2, 0.15, 0.1, 0.05])
    event = np.random.choice([1.0, 1.2, 1.5, 2.0], n_samples,
                              p=[0.6, 0.2, 0.15, 0.05])
    is_weekend = (day_of_week >= 5).astype(float)

    # Rule-based target (ground truth for ML to learn)
    occ_mult = np.where(occupancy < 50, 0.9,
                np.where(occupancy < 80, 1.0,
                np.where(occupancy < 90, 1.3, 1.6)))
    time_mult = np.where((hour >= 8) & (hour <= 10), 1.2,  # morning rush
                np.where((hour >= 17) & (hour <= 19), 1.25, 1.0))  # evening rush
    weekend_mult = np.where(is_weekend, 1.1, 1.0)
    noise = np.random.normal(0, 0.03, n_samples)  # slight noise

    target = np.clip(occ_mult * weather * event * time_mult * weekend_mult + noise, 0.5, 3.0)

    X = np.column_stack([occupancy, hour, day_of_week, weather, event, is_weekend])
    y = target
    return X, y


# ─── Rule-Based Fallback ──────────────────────────────────────────────────────

class RuleBasedPricingModel:
    """Fallback model if scikit-learn is not available."""

    def predict(self, X):
        results = []
        for row in X:
            occ, hour, _, weather, event, _ = row
            if occ < 50:
                mult = 0.9
            elif occ < 80:
                mult = 1.0
            elif occ < 90:
                mult = 1.3
            else:
                mult = 1.6
            mult *= weather * event
            if 8 <= int(hour) <= 10 or 17 <= int(hour) <= 19:
                mult *= 1.15
            results.append(round(min(3.0, max(0.5, mult)), 3))
        return np.array(results)

    def feature_names(self):
        return ["occupancy_pct", "hour_of_day", "day_of_week",
                "weather_factor", "event_factor", "is_weekend"]


# ─── Main Training Script ─────────────────────────────────────────────────────

def train_and_save(output_path: str = None):
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(__file__), "pricing_model.pkl"
        )

    print("=" * 60)
    print("ParkPilot Dynamic Pricing Model — Training")
    print("=" * 60)

    if not SKLEARN_AVAILABLE:
        print("[INFO] Saving rule-based fallback model...")
        model_data = {
            "model": RuleBasedPricingModel(),
            "model_type": "rule_based",
            "feature_names": ["occupancy_pct", "hour_of_day", "day_of_week",
                               "weather_factor", "event_factor", "is_weekend"],
            "trained_at": datetime.utcnow().isoformat(),
            "version": "1.0.0-fallback",
        }
    else:
        print(f"[1/5] Generating {5000} synthetic training samples...")
        X, y = generate_training_data(5000)

        print("[2/5] Splitting train/test...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        print("[3/5] Training RandomForestRegressor...")
        rf = Pipeline([
            ("scaler", StandardScaler()),
            ("model", RandomForestRegressor(
                n_estimators=200,
                max_depth=12,
                min_samples_leaf=5,
                random_state=42,
                n_jobs=-1,
            )),
        ])
        rf.fit(X_train, y_train)

        print("[4/5] Evaluating model...")
        preds = rf.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        print(f"       MAE  : {mae:.4f}")
        print(f"       R²   : {r2:.4f}")

        print("[5/5] Packaging model artifact...")
        model_data = {
            "model": rf,
            "model_type": "RandomForestRegressor",
            "feature_names": ["occupancy_pct", "hour_of_day", "day_of_week",
                               "weather_factor", "event_factor", "is_weekend"],
            "metrics": {"mae": round(mae, 4), "r2": round(r2, 4)},
            "n_training_samples": len(X_train),
            "trained_at": datetime.utcnow().isoformat(),
            "version": "1.0.0",
        }

    with open(output_path, "wb") as f:
        pickle.dump(model_data, f)

    size_kb = os.path.getsize(output_path) / 1024
    print(f"\n✅ Model saved → {output_path}  ({size_kb:.1f} KB)")
    print("=" * 60)
    return output_path


def load_model(model_path: str = None):
    """Load pricing model from pkl file."""
    if model_path is None:
        model_path = os.path.join(os.path.dirname(__file__), "pricing_model.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Pricing model not found at {model_path}. "
            "Run: python module12_dynamic_pricing/generate_model.py"
        )
    with open(model_path, "rb") as f:
        return pickle.load(f)


def predict_multiplier(
    occupancy_pct: float,
    hour_of_day: int = None,
    day_of_week: int = None,
    weather_factor: float = 1.0,
    event_factor: float = 1.0,
    model_path: str = None,
) -> float:
    """
    Use the trained model to predict a surge multiplier.

    Args:
        occupancy_pct: Current occupancy percentage (0-100)
        hour_of_day: Current hour (0-23), defaults to now
        day_of_week: Day of week (0=Mon, 6=Sun), defaults to today
        weather_factor: Weather demand multiplier (default 1.0)
        event_factor: Event demand multiplier (default 1.0)
        model_path: Path to pkl file

    Returns:
        Surge multiplier (float, clamped 0.5-3.0)
    """
    now = datetime.now()
    if hour_of_day is None:
        hour_of_day = now.hour
    if day_of_week is None:
        day_of_week = now.weekday()

    is_weekend = 1.0 if day_of_week >= 5 else 0.0
    X = np.array([[occupancy_pct, hour_of_day, day_of_week,
                   weather_factor, event_factor, is_weekend]])

    data = load_model(model_path)
    pred = data["model"].predict(X)[0]
    return round(float(np.clip(pred, 0.5, 3.0)), 3)


if __name__ == "__main__":
    train_and_save()
    print("\n[DEMO] Predicting for 85% occupancy, 6 PM Friday:")
    try:
        mult = predict_multiplier(85, hour_of_day=18, day_of_week=4)
        print(f"       Surge multiplier = {mult}x")
        print(f"       For ₹30 base rate → ₹{round(30 * mult, 2)}/hr")
    except Exception as e:
        print(f"       Could not run demo: {e}")
