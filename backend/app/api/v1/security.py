"""
Module 3 — Security / Surveillance API
Endpoints for security events from Module 3 surveillance system.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.models.models import SecurityEvent, SecurityEventType

router = APIRouter(prefix="/security", tags=["Security & Surveillance"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class SecurityEventCreate(BaseModel):
    event_type: str  # loitering, vandalism, unauthorized, accident, other
    camera_id: Optional[str] = None
    location_zone: Optional[str] = None
    clip_path: Optional[str] = None
    snapshot_path: Optional[str] = None
    notes: Optional[str] = None


class SecurityEventResponse(BaseModel):
    id: int
    event_type: str
    timestamp: datetime
    camera_id: Optional[str]
    location_zone: Optional[str]
    clip_path: Optional[str]
    snapshot_path: Optional[str]
    resolved: bool
    notified: bool
    notes: Optional[str]

    class Config:
        from_attributes = True


class SecurityEventUpdate(BaseModel):
    resolved: Optional[bool] = None
    notes: Optional[str] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/events", response_model=List[SecurityEventResponse], summary="List security events")
def list_events(
    resolved: Optional[bool] = None,
    event_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Return all security events, optionally filtered."""
    query = db.query(SecurityEvent)
    if resolved is not None:
        query = query.filter(SecurityEvent.resolved == resolved)
    if event_type:
        try:
            query = query.filter(SecurityEvent.event_type == SecurityEventType(event_type))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")
    return query.order_by(desc(SecurityEvent.timestamp)).limit(limit).all()


@router.post("/events", response_model=SecurityEventResponse, summary="Log a security event")
def create_event(data: SecurityEventCreate, db: Session = Depends(get_db)):
    """Log a new security event (called by Module 3 alert system)."""
    try:
        etype = SecurityEventType(data.event_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event_type. Must be one of: {[e.value for e in SecurityEventType]}",
        )

    event = SecurityEvent(
        event_type=etype,
        timestamp=datetime.now(timezone.utc),
        camera_id=data.camera_id,
        location_zone=data.location_zone,
        clip_path=data.clip_path,
        snapshot_path=data.snapshot_path,
        notes=data.notes,
        resolved=False,
        notified=False,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.patch("/events/{event_id}/resolve", response_model=SecurityEventResponse, summary="Resolve a security event")
def resolve_event(event_id: int, data: SecurityEventUpdate, db: Session = Depends(get_db)):
    """Mark a security event as resolved with optional notes."""
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
    if data.resolved is not None:
        event.resolved = data.resolved
    if data.notes is not None:
        event.notes = data.notes
    db.commit()
    db.refresh(event)
    return event


@router.get("/events/{event_id}", response_model=SecurityEventResponse, summary="Get a single event")
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
    return event


@router.get("/stats", summary="Security event statistics")
def security_stats(db: Session = Depends(get_db)):
    """Aggregate stats: event counts by type and resolution rate."""
    total = db.query(SecurityEvent).count()
    unresolved = db.query(SecurityEvent).filter(SecurityEvent.resolved == False).count()  # noqa: E712
    by_type = (
        db.query(SecurityEvent.event_type, func.count(SecurityEvent.id))
        .group_by(SecurityEvent.event_type)
        .all()
    )
    return {
        "total_events": total,
        "unresolved": unresolved,
        "resolved": total - unresolved,
        "by_type": {str(etype): count for etype, count in by_type},
    }
