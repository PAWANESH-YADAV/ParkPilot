from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta

from app.db.session import get_db
from app.models.models import (
    Reservation, User, UserRole, ReservationStatus,
    ParkingSlot, ParkingSlotStatus, ParkingLot,
)
from app.schemas.schemas import (
    Reservation as ReservationSchema,
    ReservationCreate,
    ReservationUpdate,
    ReservationDetail,
    ReservationCreateExtended,
    ReservationExtend,
)
from app.core.security import get_current_active_user

router = APIRouter(tags=["Reservations"])


def require_admin(current_user: User) -> None:
    if current_user.role not in (UserRole.ADMIN, UserRole.PROVIDER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Provider role required",
        )


def can_access_reservation(reservation: Reservation, current_user: User) -> bool:
    if current_user.role in (UserRole.ADMIN, UserRole.PROVIDER):
        return True
    return reservation.user_id == current_user.id


def _enrich(reservation: Reservation, db: Session) -> ReservationDetail:
    slot = db.query(ParkingSlot).filter(ParkingSlot.id == reservation.slot_id).first()
    lot = None
    if slot:
        lot = db.query(ParkingLot).filter(ParkingLot.id == slot.parking_lot_id).first()
    data = {
        **{
            c.name: getattr(reservation, c.name)
            for c in reservation.__table__.columns
        },
        "parking_lot_id": slot.parking_lot_id if slot else None,
        "parking_lot_name": lot.name if lot else None,
        "slot_number": slot.slot_number if slot else None,
    }
    return ReservationDetail(**data)


def _calculate_amount(
    db: Session,
    slot_id: Optional[int],
    start_time,
    end_time,
    explicit_amount: Optional[float] = None,
) -> float:
    if explicit_amount is not None:
        return round(explicit_amount, 2)
    rate = 10.0
    if slot_id:
        slot = db.query(ParkingSlot).filter(ParkingSlot.id == slot_id).first()
        if slot:
            lot = db.query(ParkingLot).filter(ParkingLot.id == slot.parking_lot_id).first()
            if lot:
                rate = lot.price_per_hour
    duration_h = (end_time - start_time).total_seconds() / 3600.0
    if duration_h <= 0:
        duration_h = 0.5
    base = rate * duration_h
    service_fee = base * 0.05
    return round(base + service_fee, 2)


def _find_available_slot(db: Session, parking_lot_id: int) -> Optional[ParkingSlot]:
    return (
        db.query(ParkingSlot)
        .filter(
            ParkingSlot.parking_lot_id == parking_lot_id,
            ParkingSlot.status == ParkingSlotStatus.AVAILABLE,
        )
        .order_by(ParkingSlot.slot_number.asc())
        .first()
    )


@router.post("/reservations/book", response_model=ReservationDetail)
def create_reservation_extended(
    data: ReservationCreateExtended,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if data.end_time <= data.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    duration_h = (data.end_time - data.start_time).total_seconds() / 3600.0
    if duration_h < 0.5 / 3600:
        raise HTTPException(status_code=400, detail="Minimum duration is 30 minutes")

    lot = db.query(ParkingLot).filter(ParkingLot.id == data.parking_lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Parking lot not found")

    slot = _find_available_slot(db, data.parking_lot_id)
    if not slot:
        raise HTTPException(status_code=400, detail="No available slots at this parking lot")

    amount = _calculate_amount(db, slot.id, data.start_time, data.end_time, data.amount)

    db_reservation = Reservation(
        user_id=current_user.id,
        slot_id=slot.id,
        vehicle_id=data.vehicle_id,
        start_time=data.start_time,
        end_time=data.end_time,
        status=ReservationStatus.CONFIRMED,
        amount=amount,
        license_plate=data.license_plate,
        vehicle_type=data.vehicle_type,
        payment_method=data.payment_method,
    )
    db.add(db_reservation)
    slot.status = ParkingSlotStatus.RESERVED
    db.commit()
    db.refresh(db_reservation)
    return _enrich(db_reservation, db)


@router.post("/reservations", response_model=ReservationSchema)
def create_reservation(
    reservation: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if reservation.end_time <= reservation.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    amount = _calculate_amount(
        db,
        reservation.slot_id,
        reservation.start_time,
        reservation.end_time,
        reservation.amount,
    )
    db_reservation = Reservation(
        **reservation.model_dump(exclude_unset=True, exclude={"amount"}),
        user_id=current_user.id,
        status=ReservationStatus.CONFIRMED,
        amount=amount,
    )
    db.add(db_reservation)

    slot = db.query(ParkingSlot).filter(ParkingSlot.id == reservation.slot_id).first()
    if slot:
        slot.status = ParkingSlotStatus.RESERVED

    db.commit()
    db.refresh(db_reservation)
    return db_reservation


@router.get("/reservations", response_model=List[ReservationDetail])
def get_user_reservations(
    status_filter: Optional[ReservationStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    q = db.query(Reservation).filter(
        Reservation.user_id == current_user.id,
    )
    if status_filter:
        q = q.filter(Reservation.status == status_filter)
    reservations = q.order_by(Reservation.created_at.desc()).all()
    return [_enrich(r, db) for r in reservations]


@router.get("/reservations/all", response_model=List[ReservationSchema])
def get_all_reservations_admin(
    status_filter: Optional[ReservationStatus] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    require_admin(current_user)
    q = db.query(Reservation)
    if status_filter:
        q = q.filter(Reservation.status == status_filter)
    if user_id:
        q = q.filter(Reservation.user_id == user_id)
    return q.order_by(Reservation.created_at.desc()).all()


def _release_slot(db: Session, slot_id: Optional[int]):
    if not slot_id:
        return
    slot = db.query(ParkingSlot).filter(ParkingSlot.id == slot_id).first()
    if slot and slot.status == ParkingSlotStatus.RESERVED:
        slot.status = ParkingSlotStatus.AVAILABLE


@router.get("/reservations/{reservation_id}", response_model=ReservationDetail)
def get_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if not can_access_reservation(reservation, current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    return _enrich(reservation, db)


@router.patch("/reservations/{reservation_id}", response_model=ReservationDetail)
def update_reservation(
    reservation_id: int,
    update: ReservationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if not can_access_reservation(reservation, current_user):
        raise HTTPException(status_code=403, detail="Not authorized")

    if current_user.role not in (UserRole.ADMIN, UserRole.PROVIDER):
        if update.status and update.status != ReservationStatus.CANCELLED:
            raise HTTPException(status_code=403, detail="Only admins may change status to non-cancelled values")
        if update.status == ReservationStatus.CANCELLED and reservation.status in (
            ReservationStatus.ACTIVE,
            ReservationStatus.COMPLETED,
        ):
            raise HTTPException(status_code=400, detail="Cannot cancel an active/completed reservation")

    patch = update.model_dump(exclude_unset=True)
    if patch.get("status") == ReservationStatus.CANCELLED:
        patch["is_active"] = False
        _release_slot(db, reservation.slot_id)
    for field, value in patch.items():
        setattr(reservation, field, value)

    db.commit()
    db.refresh(reservation)
    return _enrich(reservation, db)


@router.post("/reservations/{reservation_id}/extend", response_model=ReservationDetail)
def extend_reservation(
    reservation_id: int,
    ext: ReservationExtend,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if not can_access_reservation(reservation, current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    if reservation.status not in (ReservationStatus.CONFIRMED, ReservationStatus.ACTIVE):
        raise HTTPException(status_code=400, detail="Cannot extend this reservation")
    if ext.hours <= 0:
        raise HTTPException(status_code=400, detail="Hours must be positive")

    new_end = reservation.end_time + timedelta(hours=ext.hours)
    duration_h = (new_end - reservation.start_time).total_seconds() / 3600.0
    if duration_h > 24:
        raise HTTPException(status_code=400, detail="Maximum booking is 24 hours")

    reservation.end_time = new_end
    reservation.amount = _calculate_amount(
        db, reservation.slot_id, reservation.start_time, new_end
    )
    db.commit()
    db.refresh(reservation)
    return _enrich(reservation, db)


@router.delete("/reservations/{reservation_id}", response_model=ReservationDetail)
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if not can_access_reservation(reservation, current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    if reservation.status == ReservationStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot cancel a completed reservation")

    reservation.status = ReservationStatus.CANCELLED
    reservation.is_active = False
    _release_slot(db, reservation.slot_id)
    db.commit()
    db.refresh(reservation)
    return _enrich(reservation, db)
