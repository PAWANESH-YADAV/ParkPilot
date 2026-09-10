from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import stripe

from app.db.session import get_db
from app.models.models import Transaction, ParkingSession, TransactionStatus
from app.schemas.schemas import TransactionCreate, Transaction as TransactionSchema
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY
router = APIRouter(tags=["Billing"])


@router.post("/payment", response_model=TransactionSchema)
def process_payment(data: TransactionCreate, db: Session = Depends(get_db)):
    session = db.query(ParkingSession).filter(ParkingSession.id == data.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(data.amount * 100),
            currency="usd",
            metadata={"session_id": data.session_id}
        )
        
        transaction = Transaction(
            session_id=data.session_id,
            amount=data.amount,
            status=TransactionStatus.COMPLETED,
            payment_method=data.payment_method,
            stripe_payment_id=payment_intent.id
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoice/{session_id}")
def get_invoice(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ParkingSession).filter(ParkingSession.id == session_id).first()
    transaction = db.query(Transaction).filter(Transaction.session_id == session_id).first()
    return {"session": session, "transaction": transaction}
