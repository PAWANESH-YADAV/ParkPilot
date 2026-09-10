from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.session import get_db
from app.models.models import Sensor, ParkingSlot, ParkingSlotStatus, OccupancyLog
from app.schemas.schemas import SensorUpdate

router = APIRouter(prefix="/sensor", tags=["Sensors"])


@router.post("/update")
def update_sensor(data: SensorUpdate, db: Session = Depends(get_db)):
    sensor = db.query(Sensor).filter(Sensor.sensor_id == data.sensor_id).first()
    if sensor:
        sensor.status = data.status
        sensor.last_reading = datetime.now(timezone.utc)
        
        if sensor.slot_id:
            slot = db.query(ParkingSlot).filter(ParkingSlot.id == sensor.slot_id).first()
            if slot:
                new_status = ParkingSlotStatus.OCCUPIED if data.occupied else ParkingSlotStatus.AVAILABLE
                if slot.status != new_status:
                    slot.status = new_status
                    log = OccupancyLog(
                        slot_id=slot.id,
                        status=new_status.value
                    )
                    db.add(log)
        db.commit()
    
    return {"success": True}


@router.get("/status")
def get_sensors(db: Session = Depends(get_db)):
    sensors = db.query(Sensor).all()
    return sensors
