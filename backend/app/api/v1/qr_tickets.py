"""
Module 8 — QR Ticket System API
Endpoints for QR code generation, validation, and visitor passes.
"""

import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import QRTicket, QRTicketType

router = APIRouter(prefix="/qr", tags=["QR Ticket System"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class QRGenerateRequest(BaseModel):
    plate_number: str
    slot_id: Optional[int] = None
    ticket_type: str = "session"  # session, visitor, prepaid, monthly
    duration_hours: float = 2.0


class QRScanRequest(BaseModel):
    qr_hash: str


class QRTicketResponse(BaseModel):
    id: int
    plate_number: str
    qr_code_hash: str
    slot_id: Optional[int]
    entry_time: datetime
    expiry_time: Optional[datetime]
    used_status: int
    ticket_type: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _generate_hash(plate: str) -> str:
    """Generate a unique QR hash for a plate + timestamp."""
    raw = f"{plate}-{secrets.token_hex(8)}-{datetime.utcnow().isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32].upper()


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=QRTicketResponse, summary="Generate a QR ticket")
def generate_qr(data: QRGenerateRequest, db: Session = Depends(get_db)):
    """Create a new QR ticket for a parking session."""
    try:
        ttype = QRTicketType(data.ticket_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ticket_type. Must be one of: {[t.value for t in QRTicketType]}",
        )

    qr_hash = _generate_hash(data.plate_number)
    entry = datetime.now(timezone.utc)
    expiry = entry + timedelta(hours=data.duration_hours)

    ticket = QRTicket(
        plate_number=data.plate_number,
        qr_code_hash=qr_hash,
        slot_id=data.slot_id,
        entry_time=entry,
        expiry_time=expiry,
        used_status=0,
        ticket_type=ttype,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/scan", summary="Validate a scanned QR code")
def scan_qr(data: QRScanRequest, db: Session = Depends(get_db)):
    """
    Validate a QR hash on entry/exit.
    - Returns ticket info if valid and unused.
    - Marks ticket as used (status=1) on first scan.
    """
    ticket = db.query(QRTicket).filter(QRTicket.qr_code_hash == data.qr_hash).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="QR code not found.")

    now = datetime.now(timezone.utc)

    # Expiry check
    if ticket.expiry_time and now > ticket.expiry_time.replace(tzinfo=timezone.utc):
        ticket.used_status = 2  # expired
        db.commit()
        return {"valid": False, "reason": "QR ticket has expired.", "ticket_id": ticket.id}

    if ticket.used_status == 1:
        return {"valid": False, "reason": "QR ticket already used.", "ticket_id": ticket.id}
    if ticket.used_status == 2:
        return {"valid": False, "reason": "QR ticket expired.", "ticket_id": ticket.id}

    # Mark as used
    ticket.used_status = 1
    db.commit()
    return {
        "valid": True,
        "ticket_id": ticket.id,
        "plate_number": ticket.plate_number,
        "slot_id": ticket.slot_id,
        "ticket_type": ticket.ticket_type,
        "entry_time": ticket.entry_time,
        "expiry_time": ticket.expiry_time,
    }


@router.post("/visitor", response_model=QRTicketResponse, summary="Generate a visitor pass")
def generate_visitor_pass(
    plate_number: str,
    duration_hours: float = 4.0,
    db: Session = Depends(get_db),
):
    """Generate a time-limited visitor pass (Module 8 visitor_pass.py integration)."""
    qr_hash = _generate_hash(plate_number)
    entry = datetime.now(timezone.utc)
    expiry = entry + timedelta(hours=duration_hours)

    ticket = QRTicket(
        plate_number=plate_number,
        qr_code_hash=qr_hash,
        entry_time=entry,
        expiry_time=expiry,
        used_status=0,
        ticket_type=QRTicketType.VISITOR,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/tickets", response_model=List[QRTicketResponse], summary="List QR tickets")
def list_tickets(
    plate_number: Optional[str] = None,
    ticket_type: Optional[str] = None,
    used_status: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List QR tickets with optional filters."""
    query = db.query(QRTicket)
    if plate_number:
        query = query.filter(QRTicket.plate_number == plate_number)
    if ticket_type:
        query = query.filter(QRTicket.ticket_type == ticket_type)
    if used_status is not None:
        query = query.filter(QRTicket.used_status == used_status)
    return query.order_by(QRTicket.created_at.desc()).limit(limit).all()


@router.get("/tickets/{ticket_id}", response_model=QRTicketResponse, summary="Get a QR ticket by ID")
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(QRTicket).filter(QRTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return ticket
