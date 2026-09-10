import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
import joblib
import os


class DemandPredictor:
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.model_path = "app/models/demand_predictor.pkl"
        
        # Try to load pre-trained model
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                print("Model loaded successfully!")
            except Exception as e:
                print(f"Error loading model: {e}")

    def _generate_features(self, parking_lot_id: int, times: list):
        features = []
        for t in times:
            features.append({
                "parking_lot_id": parking_lot_id,
                "hour": t.hour,
                "day_of_week": t.weekday(),
                "month": t.month,
                "is_weekend": 1 if t.weekday() >= 5 else 0,
            })
        return pd.DataFrame(features)

    def predict(self, parking_lot_id: int, hours_ahead: int = 24):
        base_time = datetime.utcnow()
        future_times = [base_time + timedelta(hours=i) for i in range(hours_ahead)]
        
        features = self._generate_features(parking_lot_id, future_times)
        
        if not self.is_trained or self.model is None:
            # Fallback to heuristic if model not trained
            predictions = []
            for t in future_times:
                hour_factor = 0.3 + 0.4 * np.sin(2 * np.pi * (t.hour / 24))
                weekend_factor = 0.2 if t.weekday() >= 5 else 0
                pred = hour_factor + weekend_factor
                predictions.append(min(max(pred, 0), 1))
        else:
            predictions = self.model.predict(features)
        
        results = []
        for i, time in enumerate(future_times):
            results.append({
                "parking_lot_id": parking_lot_id,
                "prediction_time": time.isoformat(),
                "predicted_occupancy": min(max(float(predictions[i]), 0.0), 1.0)
            })
        
        return results

    def predict_revenue(self):
        daily = np.random.uniform(500, 2000)
        weekly = daily * 7
        monthly = daily * 30
        
        return {
            "daily": round(daily, 2),
            "weekly": round(weekly, 2),
            "monthly": round(monthly, 2)
        }


class DynamicPricingModel:
    def __init__(self):
        self.base_prices = {1: 10.0, 2: 15.0, 3: 8.0}

    def get_recommendation(self, parking_lot_id: int):
        base_price = self.base_prices.get(parking_lot_id, 10.0)
        
        hour = datetime.utcnow().hour
        if 7 <= hour <= 10 or 17 <= hour <= 20:
            surge = 1.5
        elif hour >= 22 or hour <= 6:
            surge = 0.7
        else:
            surge = 1.0
        
        effective_price = base_price * surge
        
        return {
            "parking_lot_id": parking_lot_id,
            "base_price": base_price,
            "surge_multiplier": surge,
            "effective_price": round(effective_price, 2)
        }
