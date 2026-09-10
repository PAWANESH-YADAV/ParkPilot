"""
Module 12 — Dynamic Pricing API
Endpoints for real-time pricing, pricing history, and manual override.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.models.models import DynamicPricing, ParkingLot

router = APIRouter(prefix="/pricing", tags=["Dynamic Pricing"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class PricingUpdateRequest(BaseModel):
    parking_lot_id: int
    base_price: float
    occupancy_pct: float = 0.0      # 0-100
    weather_factor: float = 1.0
    event_factor: float = 1.0
    time_factor: float = 1.0
    reason: Optional[str] = None


class DynamicPricingResponse(BaseModel):
    id: int
    parking_lot_id: Optional[int]
    base_price: Optional[float]
    surge_multiplier: Optional[float]
    effective_price: Optional[float]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Pricing Engine Logic ─────────────────────────────────────────────────────

def compute_surge_multiplier(
    occupancy_pct: float,
    weather_factor: float = 1.0,
    event_factor: float = 1.0,
    time_factor: float = 1.0,
) -> float:
    """
    Rule-based surge pricing:
    - occupancy < 50%  → 0.9x  (discount)
    - occupancy 50-80% → 1.0x  (normal)
    - occupancy 80-90% → 1.3x  (moderate surge)
    - occupancy > 90%  → 1.6x  (high surge)
    Then multiplied by weather, event, and time factors.
    """
    if occupancy_pct < 50:
        occ_multiplier = 0.9
    elif occupancy_pct < 80:
        occ_multiplier = 1.0
    elif occupancy_pct < 90:
        occ_multiplier = 1.3
    else:
        occ_multiplier = 1.6

    combined = occ_multiplier * weather_factor * event_factor * time_factor
    # Clamp between 0.5x and 3.0x
    return round(max(0.5, min(3.0, combined)), 3)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/current/{lot_id}", summary="Get current dynamic rate for a lot")
def current_rate(lot_id: int, db: Session = Depends(get_db)):
    """Return the most recent effective price for a parking lot."""
    lot = db.query(ParkingLot).filter(ParkingLot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Parking lot not found.")

    latest = (
        db.query(DynamicPricing)
        .filter(DynamicPricing.parking_lot_id == lot_id)
        .order_by(desc(DynamicPricing.created_at))
        .first()
    )

    return {
        "lot_id": lot_id,
        "lot_name": lot.name,
        "base_price": lot.price_per_hour,
        "effective_price": latest.effective_price if latest else lot.price_per_hour,
        "surge_multiplier": latest.surge_multiplier if latest else 1.0,
        "last_updated": latest.created_at if latest else None,
    }


@router.post("/update", response_model=DynamicPricingResponse, summary="Recalculate and set dynamic price")
def update_pricing(data: PricingUpdateRequest, db: Session = Depends(get_db)):
    """
    Trigger the pricing engine for a lot.
    Computes surge multiplier from all demand signals and saves a new pricing record.
    """
    lot = db.query(ParkingLot).filter(ParkingLot.id == data.parking_lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Parking lot not found.")

    surge = compute_surge_multiplier(
        data.occupancy_pct,
        data.weather_factor,
        data.event_factor,
        data.time_factor,
    )
    effective = round(data.base_price * surge, 2)

    record = DynamicPricing(
        parking_lot_id=data.parking_lot_id,
        base_price=data.base_price,
        surge_multiplier=surge,
        effective_price=effective,
        start_time=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/history/{lot_id}", response_model=List[DynamicPricingResponse], summary="Pricing history for a lot")
def pricing_history(lot_id: int, limit: int = 48, db: Session = Depends(get_db)):
    """Return recent pricing history records for a parking lot."""
    records = (
        db.query(DynamicPricing)
        .filter(DynamicPricing.parking_lot_id == lot_id)
        .order_by(desc(DynamicPricing.created_at))
        .limit(limit)
        .all()
    )
    return records


@router.get("/factors", summary="Explain current pricing factors")
def pricing_factors(
    occupancy_pct: float = 70,
    weather_factor: float = 1.0,
    event_factor: float = 1.0,
    time_factor: float = 1.0,
):
    """Explain what surge multiplier would result from given demand signals."""
    surge = compute_surge_multiplier(occupancy_pct, weather_factor, event_factor, time_factor)
    explanation = []
    if occupancy_pct < 50:
        explanation.append("Low occupancy — discount applied (0.9x)")
    elif occupancy_pct < 80:
        explanation.append("Normal occupancy — standard rate (1.0x)")
    elif occupancy_pct < 90:
        explanation.append("High occupancy — moderate surge (1.3x)")
    else:
        explanation.append("Very high occupancy — peak surge (1.6x)")
    if weather_factor > 1.0:
        explanation.append(f"Weather: {weather_factor}x factor active")
    if event_factor > 1.0:
        explanation.append(f"Event nearby: {event_factor}x factor active")
    return {
        "inputs": {
            "occupancy_pct": occupancy_pct,
            "weather_factor": weather_factor,
            "event_factor": event_factor,
            "time_factor": time_factor,
        },
        "surge_multiplier": surge,
        "explanation": explanation,
    }
