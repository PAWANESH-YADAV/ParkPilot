"""
Module 7 — Data Collection
==========================
Collects historical parking occupancy data from the database and
external sources, then preprocesses it for LSTM training.

Usage:
    python collect_data.py --lot-id 1 --days 90 --output data/lot1_history.csv
"""

import os
import csv
import json
import sqlite3
import argparse
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
DEFAULT_DB_PATH = os.environ.get("PARKPILOT_DB", "parkpilot.db")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")


# ──────────────────────────────────────────────
# Feature Engineering Helpers
# ──────────────────────────────────────────────

def extract_time_features(dt: datetime) -> dict:
    """Return dict of engineered time features from a datetime object."""
    return {
        "hour": dt.hour,
        "day_of_week": dt.weekday(),          # 0=Mon … 6=Sun
        "is_weekend": int(dt.weekday() >= 5),
        "month": dt.month,
        "day_of_month": dt.day,
        "is_morning_peak": int(8 <= dt.hour <= 10),
        "is_evening_peak": int(17 <= dt.hour <= 20),
        "is_night": int(dt.hour < 6 or dt.hour >= 22),
    }


def rolling_average(values: list, window: int = 3) -> list:
    """Compute a simple rolling average over a list of floats."""
    result = []
    for i, v in enumerate(values):
        start = max(0, i - window + 1)
        avg = sum(values[start: i + 1]) / (i - start + 1)
        result.append(round(avg, 4))
    return result


# ──────────────────────────────────────────────
# Database Queries
# ──────────────────────────────────────────────

class OccupancyCollector:
    """
    Fetches hourly occupancy data from the SQLite parking database.
    Falls back to synthetic data generation when DB is unavailable.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> bool:
        try:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
            return True
        except Exception as e:
            logger.warning(f"Could not connect to DB: {e}. Will use synthetic data.")
            return False

    def close(self):
        if self._conn:
            self._conn.close()

    def fetch_hourly_occupancy(
        self,
        parking_lot_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict]:
        """
        Returns list of hourly records:
            {timestamp, occupancy_count, total_slots, occupancy_pct, …features}
        """
        if not self._conn:
            logger.info("Using synthetic data generator.")
            return self._generate_synthetic(parking_lot_id, start_date, end_date)

        query = """
            SELECT
                strftime('%Y-%m-%d %H:00:00', ol.timestamp) AS hour_bucket,
                COUNT(CASE WHEN ol.status = 'occupied' THEN 1 END) AS occupied_count,
                COUNT(*) AS sample_count,
                pl.total_slots
            FROM occupancy_logs ol
            JOIN parking_slots ps ON ps.id = ol.slot_id
            JOIN parking_lots  pl ON pl.id = ps.parking_lot_id
            WHERE ps.parking_lot_id = ?
              AND ol.timestamp BETWEEN ? AND ?
            GROUP BY hour_bucket
            ORDER BY hour_bucket
        """
        cursor = self._conn.execute(
            query,
            (
                parking_lot_id,
                start_date.isoformat(),
                end_date.isoformat(),
            ),
        )
        rows = cursor.fetchall()

        if not rows:
            logger.warning("No DB rows found — generating synthetic data.")
            return self._generate_synthetic(parking_lot_id, start_date, end_date)

        records = []
        for row in rows:
            ts = datetime.fromisoformat(row["hour_bucket"])
            total = row["total_slots"] or 1
            pct = round(row["occupied_count"] / total, 4)
            rec = {"timestamp": row["hour_bucket"], "occupancy_pct": pct, **extract_time_features(ts)}
            records.append(rec)
        return records

    # ── Synthetic data fallback ──────────────────────────────────────────────

    def _generate_synthetic(
        self,
        parking_lot_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict]:
        """
        Generates realistic synthetic occupancy data for a parking lot
        based on typical urban traffic patterns.
        """
        import math, random

        random.seed(parking_lot_id)
        records = []
        current = start_date.replace(minute=0, second=0, microsecond=0)

        while current <= end_date:
            h = current.hour
            dow = current.weekday()

            # Base occupancy curve (0–1)
            if dow < 5:  # Weekday
                if 7 <= h <= 9:
                    base = 0.55 + 0.35 * math.sin(math.pi * (h - 7) / 2)
                elif 9 <= h <= 17:
                    base = 0.75 + 0.15 * math.sin(math.pi * (h - 9) / 8)
                elif 17 <= h <= 20:
                    base = 0.80 - 0.40 * (h - 17) / 3
                else:
                    base = 0.10 + 0.05 * random.random()
            else:  # Weekend
                if 10 <= h <= 20:
                    base = 0.50 + 0.30 * math.sin(math.pi * (h - 10) / 10)
                else:
                    base = 0.10

            noise = random.gauss(0, 0.05)
            occ = round(max(0.0, min(1.0, base + noise)), 4)

            rec = {
                "timestamp": current.strftime("%Y-%m-%d %H:%M:%S"),
                "parking_lot_id": parking_lot_id,
                "occupancy_pct": occ,
                **extract_time_features(current),
            }
            records.append(rec)
            current += timedelta(hours=1)

        # Add rolling average feature
        occ_values = [r["occupancy_pct"] for r in records]
        rolling = rolling_average(occ_values, window=3)
        for i, rec in enumerate(records):
            rec["occ_rolling_3h"] = rolling[i]

        logger.info(f"Generated {len(records)} synthetic hourly records.")
        return records


# ──────────────────────────────────────────────
# Export
# ──────────────────────────────────────────────

def save_to_csv(records: list[dict], filepath: str):
    if not records:
        logger.warning("No records to save.")
        return
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    logger.info(f"Saved {len(records)} rows → {filepath}")


def save_to_json(records: list[dict], filepath: str):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    logger.info(f"Saved {len(records)} records → {filepath}")


# ──────────────────────────────────────────────
# Stats Summary
# ──────────────────────────────────────────────

def print_summary(records: list[dict]):
    if not records:
        print("No data.")
        return
    values = [r["occupancy_pct"] for r in records]
    print("\n── Data Collection Summary ──────────────────────────")
    print(f"  Records    : {len(records)}")
    print(f"  Date range : {records[0]['timestamp']} → {records[-1]['timestamp']}")
    print(f"  Avg occ    : {sum(values)/len(values):.2%}")
    print(f"  Max occ    : {max(values):.2%}")
    print(f"  Min occ    : {min(values):.2%}")
    print("─────────────────────────────────────────────────────\n")


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ParkPilot — Collect occupancy data for LSTM training")
    parser.add_argument("--lot-id", type=int, default=1, help="Parking lot ID")
    parser.add_argument("--days", type=int, default=90, help="Number of historical days")
    parser.add_argument("--db", type=str, default=DEFAULT_DB_PATH, help="SQLite DB path")
    parser.add_argument("--output", type=str, default=None, help="Output CSV file path")
    parser.add_argument("--format", choices=["csv", "json"], default="csv", help="Output format")
    args = parser.parse_args()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)

    collector = OccupancyCollector(db_path=args.db)
    collector.connect()

    records = collector.fetch_hourly_occupancy(args.lot_id, start_date, end_date)
    collector.close()

    print_summary(records)

    out_path = args.output or os.path.join(OUTPUT_DIR, f"lot{args.lot_id}_history.{args.format}")

    if args.format == "json":
        save_to_json(records, out_path)
    else:
        save_to_csv(records, out_path)


if __name__ == "__main__":
    main()
