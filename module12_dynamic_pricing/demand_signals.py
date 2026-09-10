"""
Module 12 — Demand Signals
============================
Fetches real-time external demand signals (weather, local events,
public holidays) that influence dynamic parking prices.

Dependencies (optional):
    pip install requests

Usage:
    from module12_dynamic_pricing.demand_signals import DemandSignalProvider
    provider = DemandSignalProvider(city="Bengaluru", api_key="...")
    signals = provider.get_current_signals()
"""

import os
import json
import logging
import random
from datetime import datetime, timedelta, date
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    logger.warning("requests not installed. Using synthetic demand signals.")
    REQUESTS_AVAILABLE = False


# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────

OPENWEATHER_API_KEY  = os.environ.get("OPENWEATHER_API_KEY", "")
TICKETMASTER_API_KEY = os.environ.get("TICKETMASTER_API_KEY", "")
DEFAULT_CITY         = os.environ.get("PARKPILOT_CITY", "Bengaluru")
CACHE_TTL_MINUTES    = 15  # Cache signal data for 15 minutes


# ──────────────────────────────────────────────
# Indian Public Holidays (simplified static list)
# ──────────────────────────────────────────────

INDIA_HOLIDAYS_2024 = {
    "01-26": "Republic Day",
    "03-25": "Holi",
    "04-14": "Dr. Ambedkar Jayanti",
    "04-17": "Ram Navami",
    "05-23": "Buddha Purnima",
    "08-15": "Independence Day",
    "10-02": "Gandhi Jayanti",
    "10-12": "Dussehra",
    "10-31": "Halloween",
    "11-01": "Kannada Rajyotsava",
    "11-15": "Diwali",
    "12-25": "Christmas",
}


# ──────────────────────────────────────────────
# Demand Signal
# ──────────────────────────────────────────────

class DemandSignal:
    """Container for all demand factors at a point in time."""

    def __init__(self):
        self.timestamp          = datetime.now().isoformat()
        self.weather_factor     = 1.0
        self.weather_condition  = "clear"
        self.event_factor       = 1.0
        self.event_name         = None
        self.holiday_factor     = 1.0
        self.holiday_name       = None
        self.combined_factor    = 1.0
        self.source             = "synthetic"

    def compute_combined(self):
        """Compute overall combined demand multiplier."""
        raw = self.weather_factor * self.event_factor * self.holiday_factor
        self.combined_factor = round(min(2.5, max(0.5, raw)), 3)

    def to_dict(self) -> dict:
        self.compute_combined()
        return {
            "timestamp"         : self.timestamp,
            "weather_factor"    : self.weather_factor,
            "weather_condition" : self.weather_condition,
            "event_factor"      : self.event_factor,
            "event_name"        : self.event_name,
            "holiday_factor"    : self.holiday_factor,
            "holiday_name"      : self.holiday_name,
            "combined_factor"   : self.combined_factor,
            "source"            : self.source,
        }


# ──────────────────────────────────────────────
# Demand Signal Provider
# ──────────────────────────────────────────────

class DemandSignalProvider:
    """
    Aggregates demand signals from multiple external APIs.
    Falls back to synthetic/rule-based signals when APIs are unavailable.
    """

    WEATHER_FACTORS = {
        "clear"     : 1.0,
        "clouds"    : 1.0,
        "drizzle"   : 1.15,
        "rain"      : 1.30,    # Heavy rain → more drivers avoid public transport
        "thunderstorm": 1.40,
        "snow"      : 1.50,
        "fog"       : 1.10,
        "haze"      : 1.05,
        "mist"      : 1.08,
    }

    def __init__(
        self,
        city: str = DEFAULT_CITY,
        weather_api_key: str = OPENWEATHER_API_KEY,
        events_api_key: str = TICKETMASTER_API_KEY,
    ):
        self.city            = city
        self.weather_api_key = weather_api_key
        self.events_api_key  = events_api_key
        self._cache: Optional[dict] = None
        self._cache_expires: Optional[datetime] = None

    # ── Main Entry ────────────────────────────────────────────────────────

    def get_current_signals(self) -> dict:
        """
        Get all demand signals, using cache if fresh.

        Returns:
            {
                "weather_factor": float,
                "event_factor": float,
                "holiday_factor": float,
                "combined_factor": float,
                ...
            }
        """
        if self._is_cache_valid():
            return self._cache

        signal = DemandSignal()

        # Weather
        weather = self._get_weather()
        signal.weather_factor   = weather["factor"]
        signal.weather_condition = weather["condition"]

        # Holiday
        holiday = self._check_holiday()
        signal.holiday_factor = holiday["factor"]
        signal.holiday_name   = holiday["name"]

        # Events
        event = self._get_nearby_events()
        signal.event_factor = event["factor"]
        signal.event_name   = event["name"]

        signal.source = "live_apis" if REQUESTS_AVAILABLE and self.weather_api_key else "synthetic"
        signal.compute_combined()

        data = signal.to_dict()
        self._cache = data
        self._cache_expires = datetime.now() + timedelta(minutes=CACHE_TTL_MINUTES)

        logger.info(
            f"Demand signals: weather={signal.weather_factor} "
            f"event={signal.event_factor} "
            f"holiday={signal.holiday_factor} "
            f"combined={signal.combined_factor}"
        )
        return data

    # ── Weather ───────────────────────────────────────────────────────────

    def _get_weather(self) -> dict:
        """Fetch current weather from OpenWeatherMap API."""
        if not (REQUESTS_AVAILABLE and self.weather_api_key):
            return self._synthetic_weather()

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": self.city, "appid": self.weather_api_key, "units": "metric"}

        try:
            resp = requests.get(url, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            condition = data["weather"][0]["main"].lower()
            factor = self.WEATHER_FACTORS.get(condition, 1.0)
            return {"condition": condition, "factor": factor}
        except Exception as e:
            logger.warning(f"Weather API error: {e}. Using synthetic.")
            return self._synthetic_weather()

    def _synthetic_weather(self) -> dict:
        """Generate realistic synthetic weather based on time of year."""
        month = datetime.now().month
        # India: Monsoon Jun–Sep
        if 6 <= month <= 9:
            condition = random.choices(
                ["rain", "drizzle", "thunderstorm", "clouds"],
                weights=[0.4, 0.25, 0.15, 0.20]
            )[0]
        elif month in (1, 2):
            condition = random.choices(["mist", "fog", "clear", "clouds"], weights=[0.3, 0.2, 0.3, 0.2])[0]
        else:
            condition = random.choices(["clear", "clouds", "haze"], weights=[0.5, 0.3, 0.2])[0]
        return {"condition": condition, "factor": self.WEATHER_FACTORS.get(condition, 1.0)}

    # ── Events ────────────────────────────────────────────────────────────

    def _get_nearby_events(self) -> dict:
        """Check for nearby public events that raise parking demand."""
        # In production: query Ticketmaster / Google Places / Eventbrite API
        # For now: use a simple day-of-week and local simulation
        now = datetime.now()
        dow = now.weekday()

        # Simulate large events on Friday/Saturday evenings
        if dow in (4, 5) and 17 <= now.hour <= 23:
            if random.random() < 0.35:
                events = [
                    "IPL Match at Chinnaswamy Stadium",
                    "Concert at Palace Grounds",
                    "Tech Conference at NIMHANS Convention Centre",
                    "Shopping Festival at Orion Mall",
                ]
                event_name = random.choice(events)
                factor = round(random.uniform(1.25, 1.60), 2)
                return {"name": event_name, "factor": factor}

        return {"name": None, "factor": 1.0}

    # ── Holidays ──────────────────────────────────────────────────────────

    def _check_holiday(self) -> dict:
        """Check if today is a public holiday."""
        today = datetime.now().strftime("%m-%d")
        holiday_name = INDIA_HOLIDAYS_2024.get(today)
        if holiday_name:
            return {"name": holiday_name, "factor": 1.20}

        # Day before major holiday
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%m-%d")
        eve_holiday = INDIA_HOLIDAYS_2024.get(tomorrow)
        if eve_holiday:
            return {"name": f"Eve of {eve_holiday}", "factor": 1.10}

        return {"name": None, "factor": 1.0}

    # ── Historical Signals ────────────────────────────────────────────────

    def generate_historical_signals(
        self, days: int = 30
    ) -> list[dict]:
        """
        Generate a list of historical demand signals for backtesting.

        Returns:
            List of 24 * days hourly signal dicts.
        """
        signals = []
        start = datetime.now() - timedelta(days=days)

        for day_offset in range(days):
            day = start + timedelta(days=day_offset)
            for hour in range(24):
                ts = day.replace(hour=hour, minute=0, second=0)
                month_day = ts.strftime("%m-%d")
                holiday = INDIA_HOLIDAYS_2024.get(month_day)

                # Weather: more rain in monsoon months
                if 6 <= ts.month <= 9:
                    weather_c = random.choices(
                        ["clear", "rain", "drizzle"],
                        weights=[0.4, 0.35, 0.25]
                    )[0]
                else:
                    weather_c = random.choices(["clear", "clouds", "haze"], weights=[0.6, 0.25, 0.15])[0]

                w_factor = self.WEATHER_FACTORS.get(weather_c, 1.0)
                h_factor = 1.20 if holiday else 1.0

                # Events only on Fri/Sat evenings
                e_factor = 1.0
                e_name   = None
                if ts.weekday() in (4, 5) and 17 <= ts.hour <= 22 and random.random() < 0.25:
                    e_factor = round(random.uniform(1.2, 1.5), 2)
                    e_name   = "Event"

                combined = round(min(2.5, w_factor * h_factor * e_factor), 3)
                signals.append({
                    "timestamp"        : ts.isoformat(),
                    "weather_factor"   : w_factor,
                    "weather_condition": weather_c,
                    "event_factor"     : e_factor,
                    "event_name"       : e_name,
                    "holiday_factor"   : h_factor,
                    "holiday_name"     : holiday,
                    "combined_factor"  : combined,
                })
        return signals

    # ── Cache ─────────────────────────────────────────────────────────────

    def _is_cache_valid(self) -> bool:
        return (
            self._cache is not None
            and self._cache_expires is not None
            and datetime.now() < self._cache_expires
        )

    def invalidate_cache(self):
        self._cache = None
        self._cache_expires = None


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    provider = DemandSignalProvider(city="Bengaluru")

    print("=== Current Demand Signals ===")
    signals = provider.get_current_signals()
    for k, v in signals.items():
        if v is not None:
            print(f"  {k:25s}: {v}")

    print("\n=== Historical Signals (last 3 days, sample) ===")
    historical = provider.generate_historical_signals(days=3)
    print(f"  Generated {len(historical)} hourly signal records")
    combined_values = [h["combined_factor"] for h in historical]
    print(f"  Avg combined factor : {sum(combined_values)/len(combined_values):.3f}")
    print(f"  Max combined factor : {max(combined_values):.3f}")
