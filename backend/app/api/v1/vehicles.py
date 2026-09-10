from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.models import Vehicle, User
from app.schemas.schemas import Vehicle as VehicleSchema, VehicleCreate
from app.core.security import get_current_active_user

router = APIRouter(tags=["Vehicles"])


@router.post("/vehicles", response_model=VehicleSchema)
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_vehicle = Vehicle(**vehicle.model_dump(), user_id=current_user.id)
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


@router.get("/vehicles", response_model=List[VehicleSchema])
def get_user_vehicles(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    vehicles = db.query(Vehicle).filter(Vehicle.user_id == current_user.id).all()
    return vehicles
