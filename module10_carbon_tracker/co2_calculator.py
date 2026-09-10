"""
Module 10 — CO2 Calculator
============================
Calculates CO2 savings when a driver uses a guided parking system
versus circling/cruising for a spot, and tracks lifetime totals.

Formula basis:
  - Average cruise speed searching for spot: 15 km/h
  - Fuel consumption while cruising: 8 L/100km (urban driving)
  - CO2 per litre of petrol: 2.31 kg/L
  - EV charging emission factor: 0.7 kg CO2e/kWh (India grid average)

Usage:
    from module10_carbon_tracker.co2_calculator import CO2Calculator
    calc = CO2Calculator()
    result = calc.calculate_session_savings(
        guided=True, minutes_saved=8.5, vehicle_type="car"
    )
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

# Fuel consumption (L/100km) while cruising for parking
CRUISE_FUEL_L_PER_100KM: dict = {
    "car":      8.0,
    "bike":     3.5,
    "truck":   15.0,
    "ev":       0.0,   # EVs don't burn fuel (handled separately)
    "handicap": 7.0,
}

# CO2 per litre of fuel (kg)
CO2_PER_LITRE_PETROL_KG = 2.31
CO2_PER_LITRE_DIESEL_KG = 2.68

# Average urban cruise speed while searching (km/h)
AVERAGE_CRUISE_SPEED_KMH = 15.0

# India grid average CO2 per kWh charged
EV_GRID_CO2_KG_PER_KWH = 0.70

# Trees absorb ~21 kg CO2/year ≈ 0.0576 kg/day
CO2_PER_TREE_KG_PER_DAY = 21.0 / 365.0


# ──────────────────────────────────────────────
# CO2 Calculator
# ──────────────────────────────────────────────

class CO2Calculator:
    """
    Calculates environmental impact savings for each parking session.
    """

    def __init__(self, fuel_type: str = "petrol"):
        """
        Args:
            fuel_type: "petrol" or "diesel"
        """
        self.fuel_type = fuel_type.lower()
        self.co2_per_litre = (
            CO2_PER_LITRE_PETROL_KG if self.fuel_type == "petrol"
            else CO2_PER_LITRE_DIESEL_KG
        )

    # ── Core Calculation ─────────────────────────────────────────────────

    def calculate_session_savings(
        self,
        guided: bool,
        minutes_saved: float,
        vehicle_type: str = "car",
        ev_kwh_charged: float = 0.0,
    ) -> dict:
        """
        Calculate CO2 saved for one parking session.

        Args:
            guided        : True if driver used ParkPilot guidance
            minutes_saved : Minutes of cruise time avoided (0 if not guided)
            vehicle_type  : car, bike, truck, ev, handicap
            ev_kwh_charged: kWh charged at EV bay this session

        Returns:
            {
                "co2_saved_grams": float,
                "fuel_saved_ml": float,
                "distance_avoided_km": float,
                "ev_co2_added_grams": float,
                "net_co2_saved_grams": float,
                "tree_equivalent_days": float,
                "summary": str,
            }
        """
        vtype = vehicle_type.lower()
        fuel_rate = CRUISE_FUEL_L_PER_100KM.get(vtype, 8.0)

        # Distance that would have been driven while searching
        hours_cruising = minutes_saved / 60.0
        distance_km = AVERAGE_CRUISE_SPEED_KMH * hours_cruising

        # Fuel saved (litres)
        fuel_saved_l = (fuel_rate / 100.0) * distance_km

        # CO2 saved from not burning fuel
        if vtype == "ev":
            co2_saved_kg = 0.0  # EV doesn't burn petrol
        else:
            co2_saved_kg = fuel_saved_l * self.co2_per_litre

        co2_saved_g = co2_saved_kg * 1000

        # EV charging emissions (added, not saved)
        ev_co2_added_g = ev_kwh_charged * EV_GRID_CO2_KG_PER_KWH * 1000

        net_co2_saved_g = co2_saved_g - ev_co2_added_g
        tree_days = co2_saved_kg / CO2_PER_TREE_KG_PER_DAY

        result = {
            "co2_saved_grams"    : round(co2_saved_g, 2),
            "fuel_saved_ml"      : round(fuel_saved_l * 1000, 2),
            "distance_avoided_km": round(distance_km, 3),
            "ev_co2_added_grams" : round(ev_co2_added_g, 2),
            "net_co2_saved_grams": round(max(0, net_co2_saved_g), 2),
            "tree_equivalent_days": round(tree_days, 4),
            "summary": self._build_summary(minutes_saved, co2_saved_g, vtype),
        }

        if guided:
            logger.info(
                f"Session CO2 saved: {co2_saved_g:.1f}g | "
                f"fuel: {fuel_saved_l*1000:.0f}ml | "
                f"vehicle: {vtype}"
            )
        return result

    # ── Aggregations ─────────────────────────────────────────────────────

    def aggregate_user_totals(self, sessions: list[dict]) -> dict:
        """
        Sum up CO2/fuel savings across multiple session records.

        Args:
            sessions: List of dicts with 'co2_saved_grams', 'fuel_saved_ml'

        Returns:
            Summary dict with totals and equivalences.
        """
        total_co2_g    = sum(s.get("co2_saved_grams", 0) for s in sessions)
        total_fuel_ml  = sum(s.get("fuel_saved_ml", 0) for s in sessions)
        total_sessions = len(sessions)

        total_co2_kg = total_co2_g / 1000
        tree_equiv   = total_co2_kg / (CO2_PER_TREE_KG_PER_DAY * 365)

        return {
            "total_sessions"     : total_sessions,
            "total_co2_saved_g"  : round(total_co2_g, 2),
            "total_co2_saved_kg" : round(total_co2_kg, 3),
            "total_fuel_saved_ml": round(total_fuel_ml, 2),
            "tree_equivalent_years": round(tree_equiv, 4),
            "avg_co2_per_session_g": round(total_co2_g / max(1, total_sessions), 2),
        }

    def monthly_city_totals(
        self, user_totals: list[dict], month: Optional[str] = None
    ) -> dict:
        """
        Aggregate savings across all users for a city-level report.

        Args:
            user_totals : List of per-user aggregate dicts
            month       : "YYYY-MM" string label

        Returns:
            City-level CO2/fuel report dict.
        """
        month_label = month or datetime.now().strftime("%Y-%m")
        city_co2_kg = sum(u.get("total_co2_saved_kg", 0) for u in user_totals)
        city_fuel_l = sum(u.get("total_fuel_saved_ml", 0) for u in user_totals) / 1000
        trees_yr    = city_co2_kg / (CO2_PER_TREE_KG_PER_DAY * 365)

        return {
            "month"              : month_label,
            "total_users"        : len(user_totals),
            "city_co2_saved_kg"  : round(city_co2_kg, 2),
            "city_fuel_saved_l"  : round(city_fuel_l, 2),
            "trees_equivalent_yr": round(trees_yr, 2),
            "generated_at"       : datetime.now().isoformat(),
        }

    # ── EV-specific ───────────────────────────────────────────────────────

    def ev_session_impact(self, kwh_charged: float, grid_state: str = "average") -> dict:
        """
        Calculate net CO2 impact for an EV charging session.

        Args:
            kwh_charged : Total kWh delivered
            grid_state  : "average" | "renewable" | "coal_heavy"

        Returns:
            dict with co2_emissions_g and equivalent petrol volume
        """
        factors = {"average": 0.70, "renewable": 0.10, "coal_heavy": 1.10}
        factor = factors.get(grid_state, 0.70)

        co2_g = kwh_charged * factor * 1000
        petrol_equivalent_ml = (kwh_charged / 8.9) * 1000  # ~8.9 kWh per litre petrol

        return {
            "kwh_charged"          : kwh_charged,
            "grid_state"           : grid_state,
            "co2_emissions_g"      : round(co2_g, 2),
            "petrol_equivalent_ml" : round(petrol_equivalent_ml, 2),
            "is_net_positive"      : True,  # Assumed EV replaces ICE
        }

    # ── Helpers ───────────────────────────────────────────────────────────

    def _build_summary(
        self, minutes_saved: float, co2_g: float, vehicle_type: str
    ) -> str:
        if co2_g <= 0:
            return "No emissions saved this session."
        return (
            f"You saved {minutes_saved:.0f} min of cruising and "
            f"avoided {co2_g:.0f}g of CO₂ emissions ({vehicle_type})."
        )


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    calc = CO2Calculator()

    # Simulate 8 minutes of cruise time saved for a car
    result = calc.calculate_session_savings(
        guided=True, minutes_saved=8.5, vehicle_type="car"
    )
    print("=== Single Session ===")
    for k, v in result.items():
        print(f"  {k:30s}: {v}")

    # EV session
    ev_result = calc.ev_session_impact(kwh_charged=25.0, grid_state="average")
    print("\n=== EV Charging Session ===")
    for k, v in ev_result.items():
        print(f"  {k:30s}: {v}")
