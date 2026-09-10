"""
Module 10 — Badge & Milestone System
======================================
Awards eco-achievement badges to users based on their CO2 savings
milestones, and manages badge levels, points, and leaderboards.

Usage:
    from module10_carbon_tracker.badge_system import BadgeSystem
    bs = BadgeSystem()
    awarded = bs.check_and_award(user_id=1, total_co2_saved_g=5200)
"""

import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Badge Definitions
# ──────────────────────────────────────────────

BADGES = [
    {
        "id"         : "seedling",
        "name"       : "🌱 Seedling",
        "description": "Saved first 500g of CO₂",
        "threshold_g": 500,
        "points"     : 10,
        "level"      : 1,
        "color"      : "#86efac",
    },
    {
        "id"         : "leaf",
        "name"       : "🍃 Green Leaf",
        "description": "Saved 2 kg of CO₂",
        "threshold_g": 2000,
        "points"     : 25,
        "level"      : 2,
        "color"      : "#4ade80",
    },
    {
        "id"         : "sapling",
        "name"       : "🌿 Sapling",
        "description": "Saved 5 kg of CO₂",
        "threshold_g": 5000,
        "points"     : 50,
        "level"      : 3,
        "color"      : "#22c55e",
    },
    {
        "id"         : "tree",
        "name"       : "🌳 Tree Planter",
        "description": "Saved 10 kg of CO₂ — equivalent to planting a tree!",
        "threshold_g": 10000,
        "points"     : 100,
        "level"      : 4,
        "color"      : "#16a34a",
    },
    {
        "id"         : "forest",
        "name"       : "🌲 Forest Guardian",
        "description": "Saved 50 kg of CO₂",
        "threshold_g": 50000,
        "points"     : 300,
        "level"      : 5,
        "color"      : "#15803d",
    },
    {
        "id"         : "earth",
        "name"       : "🌍 Earth Champion",
        "description": "Saved 100 kg of CO₂ — you're making a real difference!",
        "threshold_g": 100000,
        "points"     : 750,
        "level"      : 6,
        "color"      : "#166534",
    },
    {
        "id"         : "climate_hero",
        "name"       : "⚡ Climate Hero",
        "description": "Saved 500 kg of CO₂ — legendary status!",
        "threshold_g": 500000,
        "points"     : 2500,
        "level"      : 7,
        "color"      : "#14532d",
    },
]

# Sort by threshold ascending
BADGES.sort(key=lambda b: b["threshold_g"])


# ──────────────────────────────────────────────
# Badge System
# ──────────────────────────────────────────────

class BadgeSystem:
    """
    Manages eco-achievement badges for ParkPilot users.
    Designed to be stateless — pass in user data each time.
    """

    # ── Querying Badges ──────────────────────────────────────────────────

    def get_all_badges(self) -> list[dict]:
        """Return the complete badge catalogue."""
        return BADGES

    def get_earned_badges(self, total_co2_saved_g: float) -> list[dict]:
        """Return all badges the user has earned based on total CO2 saved."""
        return [b for b in BADGES if total_co2_saved_g >= b["threshold_g"]]

    def get_next_badge(self, total_co2_saved_g: float) -> Optional[dict]:
        """Return the next badge the user hasn't yet earned."""
        for badge in BADGES:
            if total_co2_saved_g < badge["threshold_g"]:
                return badge
        return None  # All badges earned

    def current_badge(self, total_co2_saved_g: float) -> Optional[dict]:
        """Return the highest badge currently earned."""
        earned = self.get_earned_badges(total_co2_saved_g)
        return earned[-1] if earned else None

    # ── Award Detection ───────────────────────────────────────────────────

    def check_and_award(
        self,
        user_id: int,
        total_co2_saved_g: float,
        previously_awarded_ids: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        Compare total CO2 saved against badge thresholds.
        Return list of newly earned badges (not previously awarded).

        Args:
            user_id               : User identifier (for logging)
            total_co2_saved_g     : User's total lifetime CO2 saved (grams)
            previously_awarded_ids: Badge IDs already awarded to this user

        Returns:
            List of newly earned badge dicts (may be empty).
        """
        prev_ids = set(previously_awarded_ids or [])
        newly_earned = []

        for badge in BADGES:
            if (
                total_co2_saved_g >= badge["threshold_g"]
                and badge["id"] not in prev_ids
            ):
                entry = {
                    **badge,
                    "earned_at": datetime.now().isoformat(),
                    "user_id"  : user_id,
                }
                newly_earned.append(entry)
                logger.info(
                    f"🏅 Badge awarded to user {user_id}: "
                    f"{badge['name']} (threshold: {badge['threshold_g']}g)"
                )

        return newly_earned

    # ── Progress ─────────────────────────────────────────────────────────

    def progress_to_next(self, total_co2_saved_g: float) -> dict:
        """
        Calculate progress percentage to the next badge milestone.

        Returns:
            {
                "current_badge"   : dict | None,
                "next_badge"      : dict | None,
                "progress_pct"    : float,          # 0–100
                "grams_remaining" : float,
                "total_points"    : int,
            }
        """
        current = self.current_badge(total_co2_saved_g)
        nxt     = self.next_badge = self.get_next_badge(total_co2_saved_g)
        total_pts = sum(b["points"] for b in self.get_earned_badges(total_co2_saved_g))

        if nxt is None:
            return {
                "current_badge"  : current,
                "next_badge"     : None,
                "progress_pct"   : 100.0,
                "grams_remaining": 0.0,
                "total_points"   : total_pts,
            }

        # Progress between current threshold and next threshold
        prev_threshold = current["threshold_g"] if current else 0
        span = nxt["threshold_g"] - prev_threshold
        progress = (total_co2_saved_g - prev_threshold) / max(1, span) * 100

        return {
            "current_badge"  : current,
            "next_badge"     : nxt,
            "progress_pct"   : round(min(100, progress), 1),
            "grams_remaining": round(nxt["threshold_g"] - total_co2_saved_g, 1),
            "total_points"   : total_pts,
        }

    # ── Leaderboard ───────────────────────────────────────────────────────

    def build_leaderboard(self, user_stats: list[dict], top_n: int = 10) -> list[dict]:
        """
        Build a leaderboard from a list of user stat dicts.

        Args:
            user_stats: List of {user_id, name, total_co2_saved_g}
            top_n: Number of top users to return

        Returns:
            Sorted leaderboard with rank and badge info.
        """
        sorted_users = sorted(
            user_stats,
            key=lambda u: u.get("total_co2_saved_g", 0),
            reverse=True,
        )

        leaderboard = []
        for rank, u in enumerate(sorted_users[:top_n], start=1):
            co2_g = u.get("total_co2_saved_g", 0)
            badge = self.current_badge(co2_g)
            leaderboard.append({
                "rank"            : rank,
                "user_id"         : u.get("user_id"),
                "name"            : u.get("name", f"User {u.get('user_id')}"),
                "total_co2_saved_g": co2_g,
                "total_co2_saved_kg": round(co2_g / 1000, 2),
                "current_badge"   : badge["name"] if badge else "—",
                "total_points"    : sum(
                    b["points"] for b in self.get_earned_badges(co2_g)
                ),
            })
        return leaderboard


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    bs = BadgeSystem()

    print("=== Badge Catalogue ===")
    for b in bs.get_all_badges():
        print(f"  [{b['level']}] {b['name']:25s} → {b['threshold_g']/1000:.1f} kg CO₂ | {b['points']} pts")

    print("\n=== User Progress (5.2 kg saved) ===")
    progress = bs.progress_to_next(total_co2_saved_g=5200)
    print(f"  Current badge: {progress['current_badge']}")
    print(f"  Next badge   : {progress['next_badge']['name'] if progress['next_badge'] else 'All done!'}")
    print(f"  Progress     : {progress['progress_pct']}%")
    print(f"  Remaining    : {progress['grams_remaining']:.0f}g")
    print(f"  Points       : {progress['total_points']}")

    print("\n=== Newly Awarded Badges ===")
    new = bs.check_and_award(user_id=1, total_co2_saved_g=5200, previously_awarded_ids=["seedling"])
    for b in new:
        print(f"  🏅 {b['name']} earned at {b['earned_at']}")

    print("\n=== Leaderboard ===")
    users = [
        {"user_id": 1, "name": "Priya Singh",   "total_co2_saved_g": 52000},
        {"user_id": 2, "name": "Rahul Mehta",   "total_co2_saved_g": 9800},
        {"user_id": 3, "name": "Anjali Kumar",  "total_co2_saved_g": 15000},
        {"user_id": 4, "name": "Dev Patel",     "total_co2_saved_g": 800},
    ]
    for row in bs.build_leaderboard(users):
        print(f"  #{row['rank']} {row['name']:20s} {row['total_co2_saved_kg']} kg | {row['current_badge']}")
