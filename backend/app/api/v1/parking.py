from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import math

from app.db.session import get_db
from app.models.models import ParkingLot, ParkingSlot, User, ParkingSlotStatus
from app.schemas.schemas import (
    ParkingLot as ParkingLotSchema,
    ParkingLotCreate,
    ParkingLotWithAvailability,
    ParkingSlot as ParkingSlotSchema,
    ParkingSlotCreate,
)
from app.core.security import get_current_active_user

router = APIRouter(tags=["Parking"])


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _count_available(db: Session, lot_id: int) -> int:
    return (
        db.query(ParkingSlot)
        .filter(
            ParkingSlot.parking_lot_id == lot_id,
            ParkingSlot.status == ParkingSlotStatus.AVAILABLE,
        )
        .count()
    )


@router.get("/parkinglots", response_model=List[ParkingLotWithAvailability])
def get_parking_lots(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search by name or address"),
    lat: Optional[float] = Query(None, description="User latitude for distance"),
    lon: Optional[float] = Query(None, description="User longitude for distance"),
    vehicle_type: Optional[str] = Query(None, description="Filter by vehicle type"),
):
    q = db.query(ParkingLot).filter(ParkingLot.is_active == True)
    if search:
        q = q.filter(
            (ParkingLot.name.ilike(f"%{search}%")) |
            (ParkingLot.address.ilike(f"%{search}%"))
        )
    lots = q.offset(skip).limit(limit).all()

    results = []
    for lot in lots:
        vt_list = lot.vehicle_types or []
        if vehicle_type and vehicle_type.lower() not in [v.lower() for v in vt_list]:
            continue
        available = _count_available(db, lot.id)
        data = ParkingLotWithAvailability(
            id=lot.id,
            name=lot.name,
            address=lot.address,
            latitude=lot.latitude,
            longitude=lot.longitude,
            total_slots=lot.total_slots,
            price_per_hour=lot.price_per_hour,
            vehicle_types=lot.vehicle_types,
            features=lot.features,
            rating=lot.rating,
            is_active=lot.is_active,
            created_at=lot.created_at,
            updated_at=lot.updated_at,
            available_slots=available,
            distance=None,
        )
        if lat is not None and lon is not None and lot.latitude and lot.longitude:
            dist = _haversine_km(lat, lon, lot.latitude, lot.longitude)
            data.distance = f"{dist:.1f} km"
        results.append(data)

    if lat is not None and lon is not None:
        results.sort(
            key=lambda x: float(x.distance.split()[0]) if x.distance else float("inf")
        )
    return results


@router.post("/parkinglots", response_model=ParkingLotSchema)
def create_parking_lot(lot: ParkingLotCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_lot = ParkingLot(**lot.model_dump())
    db.add(db_lot)
    db.commit()
    db.refresh(db_lot)
    return db_lot


@router.get("/parkinglots/{lot_id}", response_model=ParkingLotSchema)
def get_parking_lot(lot_id: int, db: Session = Depends(get_db)):
    lot = db.query(ParkingLot).filter(ParkingLot.id == lot_id).first()
    if lot is None:
        raise HTTPException(status_code=404, detail="Parking lot not found")
    return lot


@router.get("/parkinglots/{lot_id}/slots", response_model=List[ParkingSlotSchema])
def get_parking_slots(lot_id: int, db: Session = Depends(get_db)):
    slots = db.query(ParkingSlot).filter(ParkingSlot.parking_lot_id == lot_id).all()
    return slots


@router.post("/parkingslots", response_model=ParkingSlotSchema)
def create_parking_slot(slot: ParkingSlotCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_slot = ParkingSlot(**slot.model_dump())
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot


@router.get("/parkinglots/{lot_id}/available_slot")
def get_available_slot_for_lot(
    lot_id: int,
    vehicle_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    lot = db.query(ParkingLot).filter(ParkingLot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Parking lot not found")
    slot = (
        db.query(ParkingSlot)
        .filter(
            ParkingSlot.parking_lot_id == lot_id,
            ParkingSlot.status == ParkingSlotStatus.AVAILABLE,
        )
        .order_by(ParkingSlot.slot_number.asc())
        .first()
    )
    if not slot:
        return {"slot_id": None, "slot_number": None, "message": "No available slots"}
    return {
        "slot_id": slot.id,
        "slot_number": slot.slot_number,
        "status": slot.status,
    }


@router.get("/slots", response_model=List[ParkingSlotSchema])
def get_all_slots(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    slots = db.query(ParkingSlot).offset(skip).limit(limit).all()
    return slots
