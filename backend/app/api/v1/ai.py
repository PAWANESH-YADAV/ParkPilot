from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import httpx

from app.db.session import get_db
from app.schemas.schemas import DemandPredictionResponse, PricingRecommendation
from app.core.config import settings

router = APIRouter(prefix="/predict", tags=["AI"])


@router.get("/demand", response_model=List[DemandPredictionResponse])
async def get_demand_prediction(parking_lot_id: int, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.AI_SERVICE_URL}/predict/demand",
            params={"parking_lot_id": parking_lot_id}
        )
        return response.json()


@router.get("/revenue")
async def get_revenue_prediction(db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.AI_SERVICE_URL}/predict/revenue")
        return response.json()


@router.get("/pricing/recommendation", response_model=PricingRecommendation)
async def get_pricing_recommendation(parking_lot_id: int, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.AI_SERVICE_URL}/pricing/recommendation",
            params={"parking_lot_id": parking_lot_id}
        )
        return response.json()
