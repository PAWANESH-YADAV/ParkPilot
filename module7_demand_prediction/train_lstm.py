"""
Module 7 — LSTM Demand Prediction Training
============================================
Trains an LSTM model to forecast parking occupancy 1–24 hours ahead.

Dependencies:
    pip install tensorflow numpy pandas scikit-learn

Usage:
    python train_lstm.py --input data/lot1_history.csv --epochs 50 --lot-id 1
"""

import os
import json
import logging
import argparse
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

MODEL_DIR   = os.path.join(os.path.dirname(__file__), "models")
DATA_DIR    = os.path.join(os.path.dirname(__file__), "data")
LOOK_BACK   = 24   # Hours of history to look back
HORIZON     = 6    # Hours ahead to predict
FEATURES    = ["occupancy_pct", "hour", "day_of_week", "is_weekend",
               "is_morning_peak", "is_evening_peak", "occ_rolling_3h"]


# ──────────────────────────────────────────────
# TensorFlow / Keras — graceful import
# ──────────────────────────────────────────────

try:
    import numpy as np
    import pandas as pd
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.model_selection import train_test_split
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
    from tensorflow.keras.optimizers import Adam
    ML_AVAILABLE = True
    logger.info(f"TensorFlow {tf.__version__} loaded.")
except ImportError as exc:
    logger.warning(f"TensorFlow/scikit-learn not installed: {exc}. Using stub mode.")
    ML_AVAILABLE = False


# ──────────────────────────────────────────────
# Data Preprocessing
# ──────────────────────────────────────────────

def load_dataset(csv_path: str) -> "pd.DataFrame":
    """Load and validate the CSV dataset."""
    if not ML_AVAILABLE:
        raise RuntimeError("pandas not available.")
    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    missing = [f for f in FEATURES if f not in df.columns]
    if missing:
        logger.warning(f"Missing features: {missing}. Filling with 0.")
        for col in missing:
            df[col] = 0
    logger.info(f"Loaded {len(df)} rows from {csv_path}")
    return df


def create_sequences(
    data: "np.ndarray",
    look_back: int = LOOK_BACK,
    horizon: int = HORIZON,
) -> tuple:
    """
    Create sliding-window sequences for LSTM input.

    Returns:
        X: (samples, look_back, features)
        y: (samples,) — occupancy_pct at t+horizon
    """
    X, y = [], []
    for i in range(len(data) - look_back - horizon + 1):
        X.append(data[i: i + look_back])
        y.append(data[i + look_back + horizon - 1, 0])  # column 0 = occupancy_pct
    return np.array(X), np.array(y)


# ──────────────────────────────────────────────
# Model Architecture
# ──────────────────────────────────────────────

def build_lstm_model(n_features: int, look_back: int = LOOK_BACK) -> "tf.keras.Model":
    """
    Build a stacked LSTM model for time-series occupancy forecasting.
    Architecture:
        LSTM(128) → Dropout(0.2) → BatchNorm
        LSTM(64)  → Dropout(0.2) → BatchNorm
        Dense(32) → Dense(1) — linear output (occupancy ratio 0–1)
    """
    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=(look_back, n_features)),
        Dropout(0.2),
        BatchNormalization(),
        LSTM(64, return_sequences=False),
        Dropout(0.2),
        BatchNormalization(),
        Dense(32, activation="relu"),
        Dense(1, activation="sigmoid"),  # Output: occupancy ratio [0, 1]
    ])

    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss="mse",
        metrics=["mae"],
    )
    logger.info(f"LSTM model built: {model.count_params():,} parameters")
    return model


# ──────────────────────────────────────────────
# Training Pipeline
# ──────────────────────────────────────────────

class LSTMTrainer:
    """End-to-end training pipeline for ParkPilot demand prediction."""

    def __init__(self, lot_id: int = 1, look_back: int = LOOK_BACK, horizon: int = HORIZON):
        self.lot_id    = lot_id
        self.look_back = look_back
        self.horizon   = horizon
        self.scaler    = MinMaxScaler() if ML_AVAILABLE else None
        self.model     = None
        self.history_  = None

    def prepare_data(self, df: "pd.DataFrame") -> tuple:
        """Scale features and create LSTM sequences."""
        feature_data = df[FEATURES].values.astype(float)
        scaled = self.scaler.fit_transform(feature_data)
        X, y = create_sequences(scaled, self.look_back, self.horizon)
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.15, shuffle=False
        )
        logger.info(
            f"Train: {X_train.shape}, Val: {X_val.shape} | "
            f"Features: {len(FEATURES)}"
        )
        return X_train, X_val, y_train, y_val

    def train(
        self,
        csv_path: str,
        epochs: int = 50,
        batch_size: int = 32,
    ) -> dict:
        """
        Full training run.

        Returns:
            dict with model_path, scaler_path, final_val_loss, history
        """
        if not ML_AVAILABLE:
            logger.warning("TensorFlow not available — saving stub model metadata.")
            return self._save_stub_metadata(csv_path)

        df = load_dataset(csv_path)
        X_train, X_val, y_train, y_val = self.prepare_data(df)

        self.model = build_lstm_model(n_features=len(FEATURES), look_back=self.look_back)

        os.makedirs(MODEL_DIR, exist_ok=True)
        model_path = os.path.join(MODEL_DIR, f"lstm_lot{self.lot_id}.h5")
        scaler_path = os.path.join(MODEL_DIR, f"scaler_lot{self.lot_id}.pkl")

        callbacks = [
            EarlyStopping(patience=10, restore_best_weights=True, monitor="val_loss"),
            ModelCheckpoint(model_path, save_best_only=True, monitor="val_loss"),
            ReduceLROnPlateau(factor=0.5, patience=5, min_lr=1e-5),
        ]

        logger.info(f"Starting training: {epochs} epochs, batch={batch_size}")
        hist = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1,
        )
        self.history_ = hist.history

        # Save scaler
        import pickle
        with open(scaler_path, "wb") as f:
            pickle.dump(self.scaler, f)

        final_val_loss = min(hist.history.get("val_loss", [9999]))

        metadata = {
            "lot_id"        : self.lot_id,
            "trained_at"    : datetime.now().isoformat(),
            "look_back"     : self.look_back,
            "horizon_hours" : self.horizon,
            "features"      : FEATURES,
            "epochs_ran"    : len(hist.history["loss"]),
            "final_val_loss": round(final_val_loss, 6),
            "model_path"    : model_path,
            "scaler_path"   : scaler_path,
        }
        meta_path = os.path.join(MODEL_DIR, f"metadata_lot{self.lot_id}.json")
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Training complete. Val loss: {final_val_loss:.4f}")
        logger.info(f"Model saved: {model_path}")
        return metadata

    def _save_stub_metadata(self, csv_path: str) -> dict:
        """Save placeholder metadata when TF is unavailable."""
        os.makedirs(MODEL_DIR, exist_ok=True)
        meta = {
            "lot_id"      : self.lot_id,
            "trained_at"  : datetime.now().isoformat(),
            "status"      : "stub_tensorflow_unavailable",
            "features"    : FEATURES,
            "csv_source"  : csv_path,
        }
        meta_path = os.path.join(MODEL_DIR, f"metadata_lot{self.lot_id}.json")
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        logger.info(f"Stub metadata saved: {meta_path}")
        return meta


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ParkPilot LSTM Trainer")
    parser.add_argument("--input",   type=str, required=False, help="Path to CSV dataset")
    parser.add_argument("--lot-id",  type=int, default=1)
    parser.add_argument("--epochs",  type=int, default=50)
    parser.add_argument("--batch",   type=int, default=32)
    parser.add_argument("--look-back", type=int, default=LOOK_BACK)
    parser.add_argument("--horizon",   type=int, default=HORIZON)
    args = parser.parse_args()

    csv_path = args.input or os.path.join(DATA_DIR, f"lot{args.lot_id}_history.csv")
    if not os.path.exists(csv_path):
        logger.warning(f"CSV not found: {csv_path}. Generating synthetic data first…")
        from module7_demand_prediction.collect_data import OccupancyCollector, save_to_csv
        from datetime import timedelta
        collector = OccupancyCollector()
        records = collector._generate_synthetic(
            args.lot_id,
            datetime.now() - timedelta(days=90),
            datetime.now(),
        )
        save_to_csv(records, csv_path)

    trainer = LSTMTrainer(lot_id=args.lot_id, look_back=args.look_back, horizon=args.horizon)
    metadata = trainer.train(csv_path, epochs=args.epochs, batch_size=args.batch)

    print("\n── Training Result ──────────────────────────────────")
    for k, v in metadata.items():
        print(f"  {k:20s}: {v}")


if __name__ == "__main__":
    main()
