from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import httpx

from app.db.session import get_db
from app.models.models import ANPRLog, ParkingSession, ParkingSlot, ParkingSlotStatus, ParkingLot
from app.schemas.schemas import ANPRRequest, ANPRResponse
from app.core.config import settings

router = APIRouter(prefix="/anpr", tags=["ANPR"])


@router.post("/detect", response_model=ANPRResponse)
async def detect_plate(request: ANPRRequest, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.AI_SERVICE_URL}/anpr/detect",
            json=request.model_dump()
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="ANPR service error")
        result = response.json()
        
        log = ANPRLog(
            license_plate=result.get("license_plate"),
            camera_id=request.camera_id,
            confidence=result.get("confidence", 0),
            direction="detected"
        )
        db.add(log)
        db.commit()
        
        return result


@router.post("/entry")
async def vehicle_entry(request: ANPRRequest, db: Session = Depends(get_db)):
    result = await detect_plate(request, db)
    if not result.license_plate:
        return {"success": False, "message": "Plate not detected"}
    
    slot = db.query(ParkingSlot).filter(ParkingSlot.status == ParkingSlotStatus.AVAILABLE).first()
    if not slot:
        return {"success": False, "message": "No available slots"}
    
    session = ParkingSession(
        slot_id=slot.id,
        license_plate=result.license_plate,
        entry_time=datetime.now(timezone.utc),
        is_active=True
    )
    slot.status = ParkingSlotStatus.OCCUPIED
    db.add(session)
    db.commit()
    
    return {"success": True, "session_id": session.id, "license_plate": result.license_plate}


@router.post("/exit")
async def vehicle_exit(request: ANPRRequest, db: Session = Depends(get_db)):
    result = await detect_plate(request, db)
    if not result.license_plate:
        return {"success": False, "message": "Plate not detected"}
    
    session = db.query(ParkingSession).filter(
        ParkingSession.license_plate == result.license_plate,
        ParkingSession.is_active == True
    ).first()
    
    if not session:
        return {"success": False, "message": "Active session not found"}
    
    exit_time = datetime.now(timezone.utc)
    duration = (exit_time - session.entry_time).total_seconds() / 3600
    slot = db.query(ParkingSlot).filter(ParkingSlot.id == session.slot_id).first()
    lot = db.query(ParkingLot).filter(ParkingLot.id == slot.parking_lot_id).first() if slot else None
    
    rate = lot.price_per_hour if lot else 10.0
    amount = round(max(0, duration) * rate, 2)
    session.exit_time = exit_time
    session.amount = amount
    session.is_active = False
    if slot:
        slot.status = ParkingSlotStatus.AVAILABLE
    db.commit()
    
    return {"success": True, "session_id": session.id, "amount": amount}
