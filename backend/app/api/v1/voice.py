"""
Module 11 — Voice Assistant API
Endpoints for voice command processing and history.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.db.session import get_db
from app.models.models import VoiceCommand

router = APIRouter(prefix="/voice", tags=["Voice Assistant"])

# ─── Intent definitions ───────────────────────────────────────────────────────
# Maps keywords → (intent_name, response_template)
INTENT_MAP = {
    ("book", "reserve", "parking"): (
        "book_parking",
        "I'll help you book a parking slot. Please tell me your preferred lot and duration.",
    ),
    ("available", "slots", "free", "empty"): (
        "check_availability",
        "Currently, 23 slots are available at ParkPilot Central and 8 at ParkPilot North.",
    ),
    ("navigate", "direction", "guide", "where", "how to reach"): (
        "navigate",
        "Starting indoor navigation. Follow the green LED path to your slot.",
    ),
    ("pay", "payment", "billing", "fee", "charge"): (
        "payment_inquiry",
        "Your current session fee is ₹75. Would you like to pay now?",
    ),
    ("cancel", "exit", "leave", "end session"): (
        "cancel_session",
        "Ending your parking session. Thank you for using ParkPilot!",
    ),
    ("ev", "charging", "electric", "battery"): (
        "ev_status",
        "EV Charger EV-01 is available at Level 1. Rate: ₹12/kWh.",
    ),
    ("hello", "hi", "help"): (
        "greeting",
        "Hello! I'm ParkPilot Assistant. I can help you book, navigate, or pay for parking.",
    ),
}


# ─── Schemas ──────────────────────────────────────────────────────────────────

class VoiceCommandRequest(BaseModel):
    raw_text: str
    user_id: Optional[int] = None


class VoiceCommandResponse(BaseModel):
    id: int
    user_id: Optional[int]
    raw_text: Optional[str]
    intent: Optional[str]
    confidence: Optional[float]
    response_text: Optional[str]
    success: bool
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Intent Detection ─────────────────────────────────────────────────────────

def detect_intent(text: str):
    """Simple keyword-based NLP intent detection."""
    text_lower = text.lower()
    best_intent = None
    best_response = "I didn't understand that. Try: 'book parking', 'check availability', or 'pay'."
    best_score = 0.0

    for keywords, (intent, response) in INTENT_MAP.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        score = matches / len(keywords) if keywords else 0
        if score > best_score:
            best_score = score
            best_intent = intent
            best_response = response

    if best_score == 0:
        best_intent = "unknown"
        best_score = 0.0

    return best_intent, round(best_score, 3), best_response


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/command", summary="Process a voice command")
def process_command(data: VoiceCommandRequest, db: Session = Depends(get_db)):
    """
    Classify intent from raw text (Module 11 integration).
    Returns the detected intent and a response string for TTS.
    """
    if not data.raw_text or not data.raw_text.strip():
        raise HTTPException(status_code=400, detail="raw_text must not be empty.")

    intent, confidence, response = detect_intent(data.raw_text)
    success = intent != "unknown"

    record = VoiceCommand(
        user_id=data.user_id,
        raw_text=data.raw_text,
        intent=intent,
        confidence=confidence,
        response_text=response,
        success=success,
        recorded_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "raw_text": data.raw_text,
        "intent": intent,
        "confidence": confidence,
        "response_text": response,
        "success": success,
        "tts_ready": True,
    }


@router.get("/history/{user_id}", response_model=List[VoiceCommandResponse], summary="Get command history")
def command_history(user_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """Retrieve voice command history for a specific user."""
    commands = (
        db.query(VoiceCommand)
        .filter(VoiceCommand.user_id == user_id)
        .order_by(desc(VoiceCommand.recorded_at))
        .limit(limit)
        .all()
    )
    return commands


@router.get("/intents", summary="List all supported intents")
def list_intents():
    """Return all recognized intent categories."""
    intents = list({intent for _, (intent, _) in INTENT_MAP.items()})
    return {"supported_intents": sorted(intents), "count": len(intents)}


@router.get("/stats", summary="Voice assistant usage statistics")
def voice_stats(db: Session = Depends(get_db)):
    """Aggregate: total commands, success rate, top intents."""
    from sqlalchemy import func
    total = db.query(VoiceCommand).count()
    successful = db.query(VoiceCommand).filter(VoiceCommand.success == True).count()  # noqa: E712
    by_intent = (
        db.query(VoiceCommand.intent, func.count(VoiceCommand.id).label("cnt"))
        .group_by(VoiceCommand.intent)
        .order_by(func.count(VoiceCommand.id).desc())
        .all()
    )
    return {
        "total_commands": total,
        "successful": successful,
        "success_rate_pct": round((successful / total * 100) if total else 0, 1),
        "by_intent": [{"intent": i, "count": c} for i, c in by_intent],
    }
