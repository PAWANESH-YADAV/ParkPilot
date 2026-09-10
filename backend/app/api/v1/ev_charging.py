"""
Module 6 — EV Charging API
Endpoints for managing EV charging sessions and queue.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.db.session import get_db
from app.models.models import EVSession, EVSessionStatus

router = APIRouter(prefix="/ev", tags=["EV Charging"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class EVSessionStartRequest(BaseModel):
    plate_number: str
    charger_id: str
    charger_type: str = "type2"  # type1, type2, ccs2
    rate_per_kwh: float = 8.0


class EVSessionStopRequest(BaseModel):
    kwh_consumed: float


class EVSessionResponse(BaseModel):
    id: int
    plate_number: Optional[str]
    charger_id: str
    charger_type: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    kwh_consumed: float
    fee_amount: float
    rate_per_kwh: Optional[float]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QueueEntry(BaseModel):
    position: int
    plate_number: str
    charger_type: str
    wait_time_minutes: int


# In-memory queue (in production, use Redis or DB table)
_ev_queue: List[dict] = []


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/session/start", response_model=EVSessionResponse, summary="Start EV charging session")
def start_ev_session(data: EVSessionStartRequest, db: Session = Depends(get_db)):
    """Begin a new EV charging session on a charger."""
    # Check no active session on same charger
    active = db.query(EVSession).filter(
        EVSession.charger_id == data.charger_id,
        EVSession.status == EVSessionStatus.ACTIVE,
    ).first()
    if active:
        raise HTTPException(
            status_code=409,
            detail=f"Charger {data.charger_id} already has an active session (ID {active.id}).",
        )

    session = EVSession(
        plate_number=data.plate_number,
        charger_id=data.charger_id,
        charger_type=data.charger_type,
        start_time=datetime.now(timezone.utc),
        rate_per_kwh=data.rate_per_kwh,
        status=EVSessionStatus.ACTIVE,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/session/{session_id}", response_model=EVSessionResponse, summary="Get EV session status")
def get_ev_session(session_id: int, db: Session = Depends(get_db)):
    """Fetch details of a specific EV charging session."""
    session = db.query(EVSession).filter(EVSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="EV session not found.")
    return session


@router.post("/session/{session_id}/stop", response_model=EVSessionResponse, summary="Stop EV charging session")
def stop_ev_session(
    session_id: int, data: EVSessionStopRequest, db: Session = Depends(get_db)
):
    """End an EV charging session and compute the billing amount."""
    session = db.query(EVSession).filter(EVSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="EV session not found.")
    if session.status != EVSessionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Session is not active.")

    session.end_time = datetime.now(timezone.utc)
    session.kwh_consumed = data.kwh_consumed
    session.fee_amount = round(data.kwh_consumed * (session.rate_per_kwh or 8.0), 2)
    session.status = EVSessionStatus.COMPLETED
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=List[EVSessionResponse], summary="List all EV sessions")
def list_ev_sessions(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List EV sessions, optionally filtered by status."""
    query = db.query(EVSession)
    if status:
        try:
            query = query.filter(EVSession.status == EVSessionStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    return query.order_by(EVSession.created_at.desc()).limit(limit).all()


@router.get("/stats", summary="EV charging statistics")
def ev_stats(db: Session = Depends(get_db)):
    """Aggregate stats: total sessions, energy dispensed, revenue."""
    total = db.query(EVSession).count()
    active = db.query(EVSession).filter(EVSession.status == EVSessionStatus.ACTIVE).count()
    completed = db.query(EVSession).filter(EVSession.status == EVSessionStatus.COMPLETED).count()
    total_kwh = db.query(func.sum(EVSession.kwh_consumed)).scalar() or 0.0
    total_revenue = db.query(func.sum(EVSession.fee_amount)).scalar() or 0.0
    return {
        "total_sessions": total,
        "active_sessions": active,
        "completed_sessions": completed,
        "total_kwh_dispensed": round(total_kwh, 2),
        "total_revenue_inr": round(total_revenue, 2),
    }


@router.get("/queue", summary="Get EV charging queue")
def get_queue():
    """Return the current EV charging wait queue."""
    return {
        "queue_length": len(_ev_queue),
        "entries": [
            {**e, "position": i + 1, "wait_time_minutes": (i + 1) * 20}
            for i, e in enumerate(_ev_queue)
        ],
    }


@router.post("/queue/join", summary="Join EV charging queue")
def join_queue(plate_number: str, charger_type: str = "type2"):
    """Add a vehicle to the EV charging queue."""
    already_in = any(e["plate_number"] == plate_number for e in _ev_queue)
    if already_in:
        raise HTTPException(status_code=409, detail="Vehicle already in queue.")
    _ev_queue.append({"plate_number": plate_number, "charger_type": charger_type})
    position = len(_ev_queue)
    return {
        "message": "Added to queue.",
        "position": position,
        "estimated_wait_minutes": position * 20,
    }


@router.delete("/queue/leave", summary="Leave EV charging queue")
def leave_queue(plate_number: str):
    """Remove a vehicle from the EV charging queue."""
    global _ev_queue
    before = len(_ev_queue)
    _ev_queue = [e for e in _ev_queue if e["plate_number"] != plate_number]
    if len(_ev_queue) == before:
        raise HTTPException(status_code=404, detail="Vehicle not in queue.")
    return {"message": "Removed from queue.", "queue_length": len(_ev_queue)}
