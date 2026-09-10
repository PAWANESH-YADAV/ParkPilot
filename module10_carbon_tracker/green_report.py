"""
Module 10 — Green Report Generator
=====================================
Generates monthly city-level and per-lot green impact reports
as formatted text, JSON, and optionally PDF (if reportlab is installed).

Usage:
    from module10_carbon_tracker.green_report import GreenReportGenerator
    gen = GreenReportGenerator()
    report = gen.generate_monthly_report(month="2024-06", lot_id=1)
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    )
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    logger.warning("reportlab not installed. PDF export disabled.")
    REPORTLAB_AVAILABLE = False

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


# ──────────────────────────────────────────────
# Report Data Builder
# ──────────────────────────────────────────────

class GreenReportGenerator:
    """
    Builds monthly green impact reports from carbon tracker data.
    """

    EMISSION_FACTORS = {
        "car"  : {"cruise_l_per_100km": 8.0, "co2_kg_per_l": 2.31},
        "bike" : {"cruise_l_per_100km": 3.5, "co2_kg_per_l": 2.31},
        "truck": {"cruise_l_per_100km": 15.0, "co2_kg_per_l": 2.68},
        "ev"   : {"cruise_l_per_100km": 0.0, "co2_kg_per_l": 0.0},
    }
    TREE_ABSORB_KG_YR = 21.0

    def __init__(self, output_dir: str = REPORTS_DIR):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # ── Report Generation ─────────────────────────────────────────────────

    def generate_monthly_report(
        self,
        month: str,                        # "YYYY-MM"
        lot_id: int = 1,
        lot_name: str = "ParkPilot Central",
        session_count: int = 0,
        total_co2_saved_g: float = 0.0,
        total_fuel_saved_ml: float = 0.0,
        ev_sessions: int = 0,
        top_contributors: Optional[list[dict]] = None,
        save_json: bool = True,
        save_pdf: bool = True,
    ) -> dict:
        """
        Generate a complete monthly green report.

        Args:
            month             : Report month "YYYY-MM"
            lot_id            : Parking lot ID
            lot_name          : Parking lot name
            session_count     : Total parking sessions this month
            total_co2_saved_g : Total CO2 saved (grams)
            total_fuel_saved_ml: Total fuel saved (ml)
            ev_sessions       : Number of EV charging sessions
            top_contributors  : [{name, co2_saved_g, sessions}]
            save_json, save_pdf: Whether to save output files

        Returns:
            Report dict with all metrics and file paths.
        """
        # If no real data provided, generate sample report
        if session_count == 0:
            return self._generate_sample_report(month, lot_id, lot_name, save_json, save_pdf)

        co2_kg = total_co2_saved_g / 1000
        fuel_l = total_fuel_saved_ml / 1000
        tree_yr = co2_kg / self.TREE_ABSORB_KG_YR
        cars_off_road = co2_kg / 4600   # Avg car emits 4.6 tonnes/year

        report = {
            "report_id"          : f"GR-{lot_id}-{month.replace('-', '')}",
            "month"              : month,
            "lot_id"             : lot_id,
            "lot_name"           : lot_name,
            "generated_at"       : datetime.now().isoformat(),
            "metrics": {
                "total_sessions"         : session_count,
                "ev_sessions"            : ev_sessions,
                "ev_pct"                 : round(ev_sessions / max(1, session_count) * 100, 1),
                "total_co2_saved_g"      : round(total_co2_saved_g, 2),
                "total_co2_saved_kg"     : round(co2_kg, 2),
                "total_fuel_saved_ml"    : round(total_fuel_saved_ml, 2),
                "total_fuel_saved_l"     : round(fuel_l, 2),
                "tree_years_equivalent"  : round(tree_yr, 2),
                "cars_off_road_equivalent": round(cars_off_road, 4),
                "avg_co2_per_session_g"  : round(total_co2_saved_g / max(1, session_count), 2),
            },
            "top_contributors"   : top_contributors or [],
            "badges_awarded_count": 0,
            "summary"            : self._build_summary_text(month, co2_kg, session_count, lot_name),
            "json_path"          : None,
            "pdf_path"           : None,
        }

        if save_json:
            report["json_path"] = self._save_json(report)
        if save_pdf and REPORTLAB_AVAILABLE:
            report["pdf_path"] = self._save_pdf(report)

        logger.info(
            f"Report {report['report_id']} generated: "
            f"{co2_kg:.2f} kg CO₂ saved, {session_count} sessions"
        )
        return report

    # ── Sample Report ─────────────────────────────────────────────────────

    def _generate_sample_report(
        self, month: str, lot_id: int, lot_name: str, save_json: bool, save_pdf: bool
    ) -> dict:
        """Generate a realistic sample report for demo/testing."""
        import random
        random.seed(lot_id + hash(month) % 1000)

        sessions = random.randint(800, 2000)
        ev_s = random.randint(40, 200)
        co2_g = sessions * random.uniform(40, 120)
        fuel_ml = sessions * random.uniform(15, 45)

        contributors = [
            {"rank": i+1, "name": f"User_{random.randint(100,999)}", 
             "co2_saved_g": round(random.uniform(500, 5000), 1),
             "sessions": random.randint(5, 30)}
            for i in range(5)
        ]
        contributors.sort(key=lambda x: -x["co2_saved_g"])

        return self.generate_monthly_report(
            month=month, lot_id=lot_id, lot_name=lot_name,
            session_count=sessions, total_co2_saved_g=co2_g,
            total_fuel_saved_ml=fuel_ml, ev_sessions=ev_s,
            top_contributors=contributors,
            save_json=save_json, save_pdf=save_pdf,
        )

    # ── Save JSON ─────────────────────────────────────────────────────────

    def _save_json(self, report: dict) -> str:
        filename = f"{report['report_id']}.json"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report JSON saved: {filepath}")
        return filepath

    # ── Save PDF ──────────────────────────────────────────────────────────

    def _save_pdf(self, report: dict) -> str:
        """Generate a formatted PDF report using reportlab."""
        filename = f"{report['report_id']}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title_style = styles["Heading1"]
        elements.append(Paragraph(f"🌿 ParkPilot Green Report — {report['month']}", title_style))
        elements.append(Paragraph(f"Lot: {report['lot_name']}", styles["Heading2"]))
        elements.append(Spacer(1, 12))

        # Summary
        elements.append(Paragraph(report["summary"], styles["Normal"]))
        elements.append(Spacer(1, 20))

        # Metrics table
        m = report["metrics"]
        table_data = [
            ["Metric", "Value"],
            ["Total Sessions",             str(m["total_sessions"])],
            ["EV Sessions",                f"{m['ev_sessions']} ({m['ev_pct']}%)"],
            ["CO₂ Saved",                  f"{m['total_co2_saved_kg']} kg"],
            ["Fuel Saved",                 f"{m['total_fuel_saved_l']:.1f} litres"],
            ["Tree-Year Equivalent",       f"{m['tree_years_equivalent']} tree-years"],
            ["Cars Off Road Equivalent",   f"{m['cars_off_road_equivalent']:.4f}"],
            ["Avg CO₂ per Session",        f"{m['avg_co2_per_session_g']:.1f} g"],
        ]

        table = Table(table_data, colWidths=[250, 200])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#166534")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0fdf4"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bbf7d0")),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

        # Top contributors
        if report.get("top_contributors"):
            elements.append(Paragraph("🏅 Top Green Contributors", styles["Heading3"]))
            contrib_data = [["Rank", "User", "CO₂ Saved (g)", "Sessions"]]
            for c in report["top_contributors"][:5]:
                contrib_data.append([
                    str(c.get("rank", "?")),
                    c.get("name", "—"),
                    str(round(c.get("co2_saved_g", 0), 1)),
                    str(c.get("sessions", 0)),
                ])
            ctable = Table(contrib_data, colWidths=[50, 200, 130, 80])
            ctable.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#22c55e")),
                ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
                ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]))
            elements.append(ctable)

        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            f"Generated by ParkPilot Carbon Tracker | {report['generated_at'][:10]}",
            styles["Normal"]
        ))

        doc.build(elements)
        logger.info(f"Report PDF saved: {filepath}")
        return filepath

    # ── Text Summary ──────────────────────────────────────────────────────

    def _build_summary_text(
        self, month: str, co2_kg: float, sessions: int, lot_name: str
    ) -> str:
        tree_yr = co2_kg / self.TREE_ABSORB_KG_YR
        return (
            f"In {month}, {lot_name} helped save {co2_kg:.2f} kg of CO₂ emissions "
            f"across {sessions:,} parking sessions — equivalent to planting "
            f"{tree_yr:.1f} trees for a year. ParkPilot's smart guidance "
            f"reduces unnecessary cruising, cutting fuel waste and emissions citywide."
        )


# ──────────────────────────────────────────────
# CLI Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    gen = GreenReportGenerator()

    print("=== Generating Monthly Green Report ===")
    report = gen.generate_monthly_report(
        month="2024-06",
        lot_id=1,
        lot_name="ParkPilot Central",
        session_count=1450,
        total_co2_saved_g=92500,
        total_fuel_saved_ml=40000,
        ev_sessions=120,
        top_contributors=[
            {"rank": 1, "name": "Priya S.",  "co2_saved_g": 4200, "sessions": 28},
            {"rank": 2, "name": "Rahul M.",  "co2_saved_g": 3100, "sessions": 21},
            {"rank": 3, "name": "Anjali K.", "co2_saved_g": 2800, "sessions": 18},
        ],
        save_pdf=REPORTLAB_AVAILABLE,
    )

    print(f"\nReport ID  : {report['report_id']}")
    print(f"CO₂ Saved  : {report['metrics']['total_co2_saved_kg']} kg")
    print(f"Tree-Years : {report['metrics']['tree_years_equivalent']}")
    print(f"JSON       : {report['json_path']}")
    print(f"PDF        : {report.get('pdf_path', 'N/A (reportlab not installed)')}")
    print(f"\nSummary: {report['summary']}")
