"""
ParkPilot — Module 2: Fee Calculator
Computes parking fees based on duration, vehicle type, and current pricing rules.

Fee Structure:
    First 1 hour  : Rs.30
    Each add. hour: Rs.20
    Overnight>8h  : Rs.200 flat
    Handicap      : 50% discount
    EV            : -10% discount
    Dynamic rate  : applied on top if Module 12 is active

Usage:
    from module2_anpr.fee_calculator import FeeCalculator
    calc = FeeCalculator()
    result = calc.calculate(entry_time, exit_time, vehicle_type="car")
"""

from datetime import datetime, timedelta
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger
from utils.config import settings

logger = get_logger("parkpilot.module2.fee_calculator")


class FeeCalculator:
    """
    Parking fee calculator supporting multiple vehicle types and pricing rules.

    Pricing Tiers (base, configurable via Config):
        First hour : Rs.30
        Additional : Rs.20/hr (per additional hour or part thereof)
        Overnight  : Rs.200 flat (if duration > 8 hours)

    Discounts:
        Handicap   : 50% off
        EV         : 10% off
        Night (10pm–6am) : 30% off (if entry during night hours)

    Surge Multiplier (Module 12 Dynamic Pricing):
        Applied as: final_fee = base_fee × surge_multiplier
    """

    def __init__(
        self,
        base_rate: float = None,
        additional_hour_rate: float = None,
        overnight_flat_rate: float = None
    ):
        self.base_rate = base_rate or settings.BASE_RATE_PER_HOUR
        self.add_rate = additional_hour_rate or settings.ADDITIONAL_HOUR_RATE
        self.overnight_rate = overnight_flat_rate or settings.OVERNIGHT_FLAT_RATE

        logger.info(
            f"FeeCalculator initialized | Base: ₹{self.base_rate}/hr "
            f"| Add: ₹{self.add_rate}/hr | Overnight: ₹{self.overnight_rate}"
        )

    # ── Core Calculation ──────────────────────────────────────────────────────

    def calculate(
        self,
        entry_time: datetime,
        exit_time: datetime,
        vehicle_type: str = "car",
        is_handicap: bool = False,
        is_ev: bool = False,
        surge_multiplier: float = 1.0,
        membership_discount: float = 0.0
    ) -> dict:
        """
        Calculate complete parking fee.

        Args:
            entry_time: Vehicle entry datetime (UTC)
            exit_time: Vehicle exit datetime (UTC)
            vehicle_type: 'car', 'bike', 'truck', 'ev', 'handicap'
            is_handicap: Wheelchair/disabled vehicle flag
            is_ev: Electric vehicle flag
            surge_multiplier: Dynamic pricing multiplier (1.0 = standard)
            membership_discount: Member discount fraction (0.0–1.0)

        Returns:
            dict with:
                - duration_minutes: Parking duration in minutes
                - duration_hours: Duration in fractional hours
                - base_fee: Fee before discounts
                - discount_amount: Total discount applied
                - surge_amount: Surge charge added
                - final_fee: Final amount to charge
                - breakdown: Itemized fee breakdown dict
                - tier: Pricing tier applied
        """
        if exit_time <= entry_time:
            logger.warning("Exit time is not after entry time — returning zero fee")
            return self._zero_result(entry_time, exit_time)

        duration = exit_time - entry_time
        duration_minutes = duration.total_seconds() / 60
        duration_hours = duration.total_seconds() / 3600

        # ── Bike gets half rate ────────────────────────────────────────────
        rate_multiplier = 0.5 if vehicle_type == "bike" else (
            1.5 if vehicle_type == "truck" else 1.0
        )
        effective_base = self.base_rate * rate_multiplier
        effective_add = self.add_rate * rate_multiplier
        effective_overnight = self.overnight_rate * rate_multiplier

        # ── Tier-based base fee ────────────────────────────────────────────
        tier, base_fee = self._calculate_tiered_fee(
            duration_hours, effective_base, effective_add, effective_overnight
        )

        # ── Discounts ─────────────────────────────────────────────────────
        discount_pct = 0.0
        discount_labels = []

        if is_handicap:
            discount_pct += settings.HANDICAP_DISCOUNT
            discount_labels.append(f"Handicap ({settings.HANDICAP_DISCOUNT*100:.0f}%)")

        if is_ev:
            discount_pct += settings.EV_DISCOUNT
            discount_labels.append(f"EV ({settings.EV_DISCOUNT*100:.0f}%)")

        if self._is_night_entry(entry_time):
            night_discount = 0.30
            discount_pct += night_discount
            discount_labels.append(f"Night Discount (30%)")

        if membership_discount > 0:
            discount_pct += membership_discount
            discount_labels.append(f"Member Discount ({membership_discount*100:.0f}%)")

        discount_pct = min(discount_pct, 0.75)  # Cap total discount at 75%
        discount_amount = round(base_fee * discount_pct, 2)
        after_discount = base_fee - discount_amount

        # ── Surge Pricing (Module 12) ──────────────────────────────────────
        surge_amount = round(after_discount * (surge_multiplier - 1.0), 2)
        final_fee = max(round(after_discount * surge_multiplier, 2), 0.0)

        # ── Apply rate caps ────────────────────────────────────────────────
        final_fee = min(final_fee, settings.MAX_PRICE_CAP * duration_hours)

        result = {
            "entry_time": entry_time.isoformat(),
            "exit_time": exit_time.isoformat(),
            "duration_minutes": round(duration_minutes, 1),
            "duration_hours": round(duration_hours, 2),
            "vehicle_type": vehicle_type,
            "tier": tier,
            "base_fee": round(base_fee, 2),
            "discount_pct": round(discount_pct * 100, 1),
            "discount_amount": discount_amount,
            "discount_labels": discount_labels,
            "surge_multiplier": surge_multiplier,
            "surge_amount": surge_amount,
            "final_fee": round(final_fee, 2),
            "breakdown": {
                "base": round(base_fee, 2),
                "discounts": -discount_amount,
                "surge": surge_amount,
                "total": round(final_fee, 2)
            }
        }

        logger.info(
            f"Fee calculated | Plate session | Duration: {duration_hours:.2f}h | "
            f"Tier: {tier} | Base: ₹{base_fee:.2f} | Final: ₹{final_fee:.2f}"
        )
        return result

    def _calculate_tiered_fee(
        self,
        hours: float,
        base_rate: float,
        add_rate: float,
        overnight_rate: float
    ) -> tuple:
        """
        Apply tiered pricing rules.

        Returns:
            (tier_name, fee_amount)
        """
        if hours <= 0:
            return "zero", 0.0

        if hours > 8:
            return "overnight", overnight_rate

        if hours <= 1:
            # First hour — flat base rate
            return "first_hour", base_rate

        # First hour + additional hours (round up partial hours)
        additional_hours = hours - 1.0
        additional_fee = add_rate * additional_hours  # Charge for exact time
        total = base_rate + additional_fee
        return "standard", round(total, 2)

    def _is_night_entry(self, entry_time: datetime) -> bool:
        """Check if entry is during night hours (10pm–6am) — night discount applies."""
        hour = entry_time.hour
        return hour >= 22 or hour < 6

    def _zero_result(self, entry_time: datetime, exit_time: datetime) -> dict:
        return {
            "entry_time": entry_time.isoformat(),
            "exit_time": exit_time.isoformat(),
            "duration_minutes": 0.0,
            "duration_hours": 0.0,
            "vehicle_type": "car",
            "tier": "zero",
            "base_fee": 0.0,
            "discount_pct": 0.0,
            "discount_amount": 0.0,
            "discount_labels": [],
            "surge_multiplier": 1.0,
            "surge_amount": 0.0,
            "final_fee": 0.0,
            "breakdown": {}
        }

    # ── Utility Methods ───────────────────────────────────────────────────────

    def estimate_fee(self, entry_time: datetime, now: datetime = None, **kwargs) -> dict:
        """
        Estimate current fee for an active session (vehicle still parked).
        Uses current time as exit_time.
        """
        now = now or datetime.utcnow()
        return self.calculate(entry_time, now, **kwargs)

    def calculate_prepaid(self, hours: float, vehicle_type: str = "car") -> float:
        """
        Calculate fee for a prepaid parking session (known duration).

        Args:
            hours: Duration in hours
            vehicle_type: Vehicle type

        Returns:
            Fee amount in Rupees
        """
        now = datetime.utcnow()
        exit_t = now + timedelta(hours=hours)
        result = self.calculate(now, exit_t, vehicle_type=vehicle_type)
        return result["final_fee"]

    def get_rate_table(self) -> list:
        """
        Get formatted rate table for display on boards/app.

        Returns:
            List of rate tier dicts
        """
        return [
            {"tier": "First 1 hour", "rate": f"₹{self.base_rate:.0f}", "note": ""},
            {"tier": "Each additional hour", "rate": f"₹{self.add_rate:.0f}/hr", "note": ""},
            {"tier": "Overnight (>8h)", "rate": f"₹{self.overnight_rate:.0f} flat", "note": ""},
            {"tier": "2-Wheeler", "rate": "50% off above rates", "note": ""},
            {"tier": "Heavy Vehicle", "rate": "1.5× above rates", "note": ""},
            {"tier": "Handicap", "rate": "50% discount", "note": ""},
            {"tier": "EV Charging", "rate": "10% discount", "note": ""},
            {"tier": "Night (10pm–6am)", "rate": "30% discount", "note": ""},
        ]


# ═══════════════════════════════════════════════════════════════════════════
#  Quick-use convenience function
# ═══════════════════════════════════════════════════════════════════════════

_calculator = None

def calculate_fee(entry_time: datetime, exit_time: datetime, **kwargs) -> dict:
    """Module-level quick calculator — uses default singleton FeeCalculator."""
    global _calculator
    if _calculator is None:
        _calculator = FeeCalculator()
    return _calculator.calculate(entry_time, exit_time, **kwargs)


if __name__ == "__main__":
    # Demo
    calc = FeeCalculator()
    entry = datetime(2024, 1, 15, 9, 0, 0)
    exit_ = datetime(2024, 1, 15, 11, 30, 0)  # 2.5 hours

    result = calc.calculate(entry, exit_, vehicle_type="car")
    print(f"\n{'='*50}")
    print(f"  ParkPilot — Fee Calculator Demo")
    print(f"{'='*50}")
    print(f"  Duration : {result['duration_hours']:.2f} hours")
    print(f"  Tier     : {result['tier']}")
    print(f"  Base Fee : ₹{result['base_fee']:.2f}")
    print(f"  Discount : -₹{result['discount_amount']:.2f}")
    print(f"  Surge    : +₹{result['surge_amount']:.2f}")
    print(f"  FINAL    : ₹{result['final_fee']:.2f}")
    print(f"{'='*50}\n")

    # Rate table
    print("Rate Table:")
    for row in calc.get_rate_table():
        print(f"  {row['tier']:30} {row['rate']}")
