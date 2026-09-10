import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import joblib
import os
from datetime import datetime, timedelta

# Create sample training data
def generate_sample_data():
    data = []
    base_time = datetime(2024, 1, 1)
    
    for i in range(365 * 24)  # 2 years of hourly data
        for parking_lot_id in [1, 2, 3]:
            time = base_time + timedelta(hours=i)
            hour = time.hour
            day_of_week = time.weekday()
            month = time.month
            is_weekend = 1 if day_of_week >= 5 else 0
            
            # Simulate occupancy pattern
            base_occupancy = 30 + 30 * np.sin(2 * np.pi * (hour / 24))
            if is_weekend:
                base_occupancy += 20
            occupancy = min(max(base_occupancy + np.random.normal(0, 5), 0), 100)
            
            data.append({
                'parking_lot_id': parking_lot_id,
                'hour': hour,
                'day_of_week': day_of_week,
                'month': month,
                'is_weekend': is_weekend,
                'occupancy': occupancy
            })
    
    return pd.DataFrame(data)

def train_model():
    print("Generating training data...")
    df = generate_sample_data()
    
    X = df[['parking_lot_id', 'hour', 'day_of_week', 'month', 'is_weekend']]
    y = df['occupancy']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training model...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    print(f"Model trained! MAE: {mae:.2f}%")
    
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/demand_predictor.pkl')
    print("Model saved to models/demand_predictor.pkl")
    
    return model

if __name__ == "__main__":
    train_model()
