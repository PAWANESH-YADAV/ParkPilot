from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import base64
import numpy as np
from PIL import Image
import io

from app.services.yolo_service import VehicleDetector
from app.services.anpr_service import ANPRService
from app.services.ml_service import DemandPredictor, DynamicPricingModel

app = FastAPI(title="ParkPilot AI Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vehicle_detector = VehicleDetector()
anpr_service = ANPRService()
demand_predictor = DemandPredictor()
pricing_model = DynamicPricingModel()


@app.get("/")
def root():
    return {"message": "ParkPilot AI Service"}


@app.post("/yolo/detect")
async def detect_vehicles(data: dict):
    image_data = base64.b64decode(data["image"])
    image = Image.open(io.BytesIO(image_data))
    image_np = np.array(image)
    results = vehicle_detector.detect(image_np)
    return results


@app.post("/anpr/detect")
async def detect_plate(data: dict):
    image_data = base64.b64decode(data["image"])
    image = Image.open(io.BytesIO(image_data))
    image_np = np.array(image)
    result = anpr_service.detect_and_recognize(image_np)
    return result


@app.get("/predict/demand")
async def predict_demand(parking_lot_id: int):
    predictions = demand_predictor.predict(parking_lot_id)
    return predictions


@app.get("/predict/revenue")
async def predict_revenue():
    prediction = demand_predictor.predict_revenue()
    return prediction


@app.get("/pricing/recommendation")
async def get_pricing(parking_lot_id: int):
    recommendation = pricing_model.get_recommendation(parking_lot_id)
    return recommendation


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
