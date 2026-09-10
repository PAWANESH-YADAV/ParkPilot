"""
ParkPilot — Module 2: Bill Generator
Generates PDF and HTML parking receipts/invoices.

Features:
    - Professional PDF receipt (reportlab)
    - HTML receipt (email-ready)
    - QR code embedded on receipt
    - Sends via email/SMS after generation

Usage:
    from module2_anpr.bill_generator import BillGenerator
    gen = BillGenerator()
    pdf_path = gen.generate_pdf(session_data)
"""

import os
import sys
import json
import qrcode
from datetime import datetime
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger("parkpilot.module2.bill_generator")

RECEIPTS_DIR = "module2_anpr/receipts/"
os.makedirs(RECEIPTS_DIR, exist_ok=True)


class BillGenerator:
    """
    Generates parking receipts in PDF and HTML format.

    Args:
        receipts_dir: Directory to save generated receipts
        company_name: Parking company name on receipt
        company_address: Company address
        gst_number: GST registration number
    """

    def __init__(
        self,
        receipts_dir: str = RECEIPTS_DIR,
        company_name: str = "ParkPilot",
        company_address: str = "MG Road, Bengaluru, Karnataka — 560001",
        gst_number: str = "29AAXPB1234E1ZX"
    ):
        self.receipts_dir = receipts_dir
        self.company_name = company_name
        self.company_address = company_address
        self.gst_number = gst_number
        os.makedirs(receipts_dir, exist_ok=True)

    # ── PDF Generation ────────────────────────────────────────────────────────

    def generate_pdf(self, session: dict) -> str:
        """
        Generate a professional PDF parking receipt.

        Args:
            session: Dict with keys:
                - receipt_number, plate_number, vehicle_type
                - entry_time, exit_time
                - duration_hours, base_fee, discount_amount,
                  surge_amount, final_fee, payment_method
                - customer_name (optional)

        Returns:
            Path to generated PDF file, or empty string on failure
        """
        try:
            from reportlab.lib.pagesizes import A5
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                SimpleDocTemplate, Table, TableStyle, Paragraph,
                Spacer, HRFlowable, Image as RLImage
            )
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        except ImportError:
            logger.warning("reportlab not installed — generating HTML receipt only")
            return self.generate_html(session)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        receipt_num = session.get("receipt_number", f"PP{ts}")
        filename = os.path.join(self.receipts_dir, f"receipt_{receipt_num}.pdf")

        doc = SimpleDocTemplate(
            filename,
            pagesize=A5,
            topMargin=1*cm,
            bottomMargin=1*cm,
            leftMargin=1.5*cm,
            rightMargin=1.5*cm
        )

        styles = getSampleStyleSheet()
        header_style = ParagraphStyle("Header", parent=styles["Heading1"],
                                       fontSize=16, textColor=colors.HexColor("#1d4ed8"),
                                       alignment=TA_CENTER, spaceAfter=4)
        sub_style = ParagraphStyle("Sub", parent=styles["Normal"],
                                    fontSize=8, textColor=colors.HexColor("#64748b"),
                                    alignment=TA_CENTER)
        label_style = ParagraphStyle("Label", parent=styles["Normal"],
                                      fontSize=9, textColor=colors.HexColor("#374151"))
        value_style = ParagraphStyle("Value", parent=styles["Normal"],
                                      fontSize=9, fontName="Helvetica-Bold",
                                      textColor=colors.HexColor("#111827"))
        total_style = ParagraphStyle("Total", parent=styles["Normal"],
                                      fontSize=14, fontName="Helvetica-Bold",
                                      textColor=colors.HexColor("#1d4ed8"), alignment=TA_RIGHT)

        story = []

        # Header
        story.append(Paragraph(f"🚗 {self.company_name}", header_style))
        story.append(Paragraph("PARKING RECEIPT", sub_style))
        story.append(Paragraph(self.company_address, sub_style))
        story.append(Paragraph(f"GST: {self.gst_number}", sub_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
        story.append(Spacer(1, 0.3*cm))

        # QR Code (encode receipt number)
        qr_img = self._generate_qr_image(receipt_num, size_cm=3)
        if qr_img:
            story.append(qr_img)
            story.append(Spacer(1, 0.2*cm))

        # Receipt details table
        entry_str = _fmt_time(session.get("entry_time"))
        exit_str = _fmt_time(session.get("exit_time"))
        dur = session.get("duration_hours", 0)

        data = [
            ["Receipt No.", receipt_num],
            ["Vehicle Plate", session.get("plate_number", "N/A")],
            ["Vehicle Type", session.get("vehicle_type", "Car").title()],
            ["Customer", session.get("customer_name", "Walk-in")],
            ["Entry Time", entry_str],
            ["Exit Time", exit_str],
            ["Duration", f"{int(dur)}h {int((dur%1)*60)}m"],
            ["Payment Method", session.get("payment_method", "Cash").upper()],
        ]

        tbl = Table(data, colWidths=[5*cm, 7*cm])
        tbl.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#6b7280")),
            ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#111827")),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.3*cm))

        # Fee breakdown
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1")))
        story.append(Spacer(1, 0.2*cm))

        fee_data = [
            ["Base Fee", f"\u20B9{session.get('base_fee', 0):.2f}"],
            ["Discount", f"-\u20B9{session.get('discount_amount', 0):.2f}"],
            ["Surge", f"+\u20B9{session.get('surge_amount', 0):.2f}"],
        ]
        fee_tbl = Table(fee_data, colWidths=[9*cm, 3*cm])
        fee_tbl.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#6b7280")),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(fee_tbl)
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1d4ed8")))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(f"TOTAL: \u20B9{session.get('final_fee', 0):.2f}", total_style))
        story.append(Spacer(1, 0.3*cm))

        # Footer
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            "Thank you for using ParkPilot! Drive safe. 🌱 You saved CO2 today.",
            sub_style
        ))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", sub_style))

        doc.build(story)
        logger.info(f"PDF receipt generated: {filename}")
        return filename

    def _generate_qr_image(self, data: str, size_cm: float = 3):
        """Generate a QR code image for embedding in PDF."""
        try:
            from reportlab.platypus import Image as RLImage
            qr = qrcode.QRCode(version=1, box_size=4, border=2)
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            buf = BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)

            from reportlab.lib.units import cm
            return RLImage(buf, width=size_cm*cm, height=size_cm*cm, hAlign="CENTER")
        except Exception as e:
            logger.warning(f"QR in PDF failed: {e}")
            return None

    # ── HTML Generation ───────────────────────────────────────────────────────

    def generate_html(self, session: dict) -> str:
        """
        Generate an HTML receipt (email-compatible).

        Returns:
            Path to generated HTML file
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        receipt_num = session.get("receipt_number", f"PP{ts}")
        filename = os.path.join(self.receipts_dir, f"receipt_{receipt_num}.html")

        entry_str = _fmt_time(session.get("entry_time"))
        exit_str = _fmt_time(session.get("exit_time"))
        dur = session.get("duration_hours", 0)
        dur_str = f"{int(dur)}h {int((dur%1)*60)}m"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ParkPilot Receipt #{receipt_num}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f1f5f9; margin: 0; padding: 20px; }}
  .card {{ max-width: 480px; margin: auto; background: #fff; border-radius: 16px; padding: 32px;
           box-shadow: 0 4px 24px rgba(0,0,0,0.12); }}
  .header {{ text-align: center; margin-bottom: 24px; }}
  .header h1 {{ color: #1d4ed8; font-size: 1.8em; margin: 0 0 4px; }}
  .header p {{ color: #64748b; font-size: 0.85em; margin: 0; }}
  table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
  td {{ padding: 10px 8px; border-bottom: 1px solid #f1f5f9; font-size: 0.9em; }}
  td:first-child {{ color: #6b7280; }}
  td:last-child {{ font-weight: 600; color: #111827; text-align: right; }}
  .total-row td {{ color: #1d4ed8 !important; font-size: 1.1em; border-top: 2px solid #1d4ed8; }}
  .footer {{ text-align: center; color: #94a3b8; font-size: 0.8em; margin-top: 20px; }}
  .badge {{ display: inline-block; background: #dcfce7; color: #166534; padding: 4px 12px;
            border-radius: 99px; font-size: 0.8em; margin-top: 12px; }}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <h1>🚗 {self.company_name}</h1>
    <p>PARKING RECEIPT</p>
    <p>{self.company_address}</p>
  </div>
  <table>
    <tr><td>Receipt No.</td><td>{receipt_num}</td></tr>
    <tr><td>Vehicle Plate</td><td>{session.get('plate_number', 'N/A')}</td></tr>
    <tr><td>Vehicle Type</td><td>{session.get('vehicle_type', 'Car').title()}</td></tr>
    <tr><td>Customer</td><td>{session.get('customer_name', 'Walk-in')}</td></tr>
    <tr><td>Entry Time</td><td>{entry_str}</td></tr>
    <tr><td>Exit Time</td><td>{exit_str}</td></tr>
    <tr><td>Duration</td><td>{dur_str}</td></tr>
    <tr><td>Base Fee</td><td>₹{session.get('base_fee', 0):.2f}</td></tr>
    <tr><td>Discount</td><td>-₹{session.get('discount_amount', 0):.2f}</td></tr>
    <tr><td>Surge</td><td>+₹{session.get('surge_amount', 0):.2f}</td></tr>
    <tr class="total-row"><td>TOTAL PAID</td><td>₹{session.get('final_fee', 0):.2f}</td></tr>
  </table>
  <div class="footer">
    <div class="badge">🌱 CO₂ Saved Today: ~{session.get('co2_saved_g', 480):.0f}g</div>
    <p>Thank you for using ParkPilot!</p>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
  </div>
</div>
</body>
</html>"""

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"HTML receipt generated: {filename}")
        return filename


def _fmt_time(t) -> str:
    """Format datetime to human-readable string."""
    if isinstance(t, datetime):
        return t.strftime("%d %b %Y, %I:%M %p")
    if isinstance(t, str):
        try:
            dt = datetime.fromisoformat(t)
            return dt.strftime("%d %b %Y, %I:%M %p")
        except ValueError:
            return t
    return str(t) if t else "N/A"


if __name__ == "__main__":
    gen = BillGenerator()
    demo_session = {
        "receipt_number": "PP20240115001",
        "plate_number": "KA05AB1234",
        "vehicle_type": "car",
        "customer_name": "Rahul Sharma",
        "entry_time": "2024-01-15T09:00:00",
        "exit_time": "2024-01-15T11:30:00",
        "duration_hours": 2.5,
        "base_fee": 70.0,
        "discount_amount": 0.0,
        "surge_amount": 0.0,
        "final_fee": 70.0,
        "payment_method": "UPI",
        "co2_saved_g": 480
    }

    pdf = gen.generate_pdf(demo_session)
    html = gen.generate_html(demo_session)
    print(f"PDF: {pdf}")
    print(f"HTML: {html}")
