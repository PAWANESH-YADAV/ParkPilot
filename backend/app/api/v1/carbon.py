"""
Module 10 — Carbon Tracker API
Endpoints for CO2 savings, eco badges, and green city reports.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.db.session import get_db
from app.models.models import CarbonCredit, User

router = APIRouter(prefix="/carbon", tags=["Carbon Tracker"])

# Badge milestones (grams of CO2 saved)
BADGE_MILESTONES = [
    (100,   "🌱 Green Starter"),
    (500,   "⚡ EV Champion"),
    (1000,  "🌍 Carbon Saver"),
    (5000,  "🏆 Eco Warrior"),
    (10000, "🚀 Planet Hero"),
    (25000, "♻️ Zero Emission"),
]


# ─── Schemas ──────────────────────────────────────────────────────────────────

class CarbonRecordCreate(BaseModel):
    user_id: int
    session_id: Optional[int] = None
    co2_saved_grams: float
    fuel_saved_ml: float = 0.0
    tree_equivalent: float = 0.0


class CarbonCreditResponse(BaseModel):
    id: int
    user_id: Optional[int]
    session_id: Optional[int]
    co2_saved_grams: float
    fuel_saved_ml: float
    tree_equivalent: float
    badge_awarded: Optional[str]
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _compute_badge(total_grams: float) -> Optional[str]:
    """Return the highest badge earned for this total CO2 saved."""
    earned = None
    for threshold, badge in BADGE_MILESTONES:
        if total_grams >= threshold:
            earned = badge
    return earned


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/user/{user_id}", summary="Get user CO2 savings summary")
def user_carbon_summary(user_id: int, db: Session = Depends(get_db)):
    """Return total CO2 savings and badge status for a user."""
    credits = db.query(CarbonCredit).filter(CarbonCredit.user_id == user_id).all()
    if not credits:
        return {
            "user_id": user_id,
            "total_co2_grams": 0.0,
            "total_fuel_ml": 0.0,
            "trees_equivalent": 0.0,
            "current_badge": None,
            "sessions_count": 0,
        }

    total_co2 = sum(c.co2_saved_grams for c in credits)
    total_fuel = sum(c.fuel_saved_ml for c in credits)
    total_trees = sum(c.tree_equivalent for c in credits)
    badge = _compute_badge(total_co2)

    return {
        "user_id": user_id,
        "total_co2_grams": round(total_co2, 2),
        "total_co2_kg": round(total_co2 / 1000, 3),
        "total_fuel_ml": round(total_fuel, 2),
        "trees_equivalent": round(total_trees, 4),
        "current_badge": badge,
        "sessions_count": len(credits),
    }


@router.get("/badges/{user_id}", summary="Get user eco badges")
def user_badges(user_id: int, db: Session = Depends(get_db)):
    """Return all badges with earned/not-earned status for a user."""
    total_co2 = (
        db.query(func.sum(CarbonCredit.co2_saved_grams))
        .filter(CarbonCredit.user_id == user_id)
        .scalar()
        or 0.0
    )
    badges = []
    for threshold, badge in BADGE_MILESTONES:
        badges.append({
            "name": badge,
            "threshold_grams": threshold,
            "earned": total_co2 >= threshold,
            "progress_pct": min(100, round((total_co2 / threshold) * 100, 1)),
        })
    return {"user_id": user_id, "total_co2_grams": round(total_co2, 2), "badges": badges}


@router.post("/record", response_model=CarbonCreditResponse, summary="Record a carbon saving")
def record_carbon(data: CarbonRecordCreate, db: Session = Depends(get_db)):
    """Record CO2 savings for a parking session (called by Module 10)."""
    # Check if new badge earned
    total_before = (
        db.query(func.sum(CarbonCredit.co2_saved_grams))
        .filter(CarbonCredit.user_id == data.user_id)
        .scalar()
        or 0.0
    )
    total_after = total_before + data.co2_saved_grams
    badge_before = _compute_badge(total_before)
    badge_after = _compute_badge(total_after)
    new_badge = badge_after if badge_after != badge_before else None

    credit = CarbonCredit(
        user_id=data.user_id,
        session_id=data.session_id,
        co2_saved_grams=data.co2_saved_grams,
        fuel_saved_ml=data.fuel_saved_ml,
        tree_equivalent=data.tree_equivalent,
        badge_awarded=new_badge,
        recorded_at=datetime.now(timezone.utc),
    )
    db.add(credit)
    db.commit()
    db.refresh(credit)
    return credit


@router.get("/report/monthly", summary="Monthly green city report")
def monthly_report(
    year: int = datetime.now().year,
    month: int = datetime.now().month,
    db: Session = Depends(get_db),
):
    """Aggregate monthly CO2 savings across all users for city green report."""
    credits = db.query(CarbonCredit).all()
    # Filter by month/year
    monthly = [
        c for c in credits
        if c.recorded_at.year == year and c.recorded_at.month == month
    ]
    total_co2 = sum(c.co2_saved_grams for c in monthly)
    total_fuel = sum(c.fuel_saved_ml for c in monthly)
    total_trees = sum(c.tree_equivalent for c in monthly)
    unique_users = len(set(c.user_id for c in monthly if c.user_id))

    return {
        "year": year,
        "month": month,
        "unique_eco_users": unique_users,
        "total_co2_saved_grams": round(total_co2, 2),
        "total_co2_saved_kg": round(total_co2 / 1000, 3),
        "total_fuel_saved_liters": round(total_fuel / 1000, 3),
        "trees_equivalent": round(total_trees, 2),
        "sessions_count": len(monthly),
    }


@router.get("/leaderboard", summary="Top eco users leaderboard")
def leaderboard(limit: int = 10, db: Session = Depends(get_db)):
    """Return top users by CO2 saved."""
    rows = (
        db.query(CarbonCredit.user_id, func.sum(CarbonCredit.co2_saved_grams).label("total"))
        .filter(CarbonCredit.user_id.isnot(None))
        .group_by(CarbonCredit.user_id)
        .order_by(func.sum(CarbonCredit.co2_saved_grams).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "rank": i + 1,
            "user_id": row.user_id,
            "total_co2_grams": round(row.total, 2),
            "badge": _compute_badge(row.total),
        }
        for i, row in enumerate(rows)
    ]
