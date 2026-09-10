"""
ParkPilot — Module 6: EV Billing System
Generates itemized bills for EV charging sessions.
Handles combined parking + charging invoices.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger
from utils.config import settings

logger = get_logger("parkpilot.module6.ev_billing")

CHARGER_RATES = {
    "type1": {"name": "AC Slow (3.3 kW)",  "rate": settings.EV_TYPE1_RATE},
    "type2": {"name": "AC Fast (22 kW)",   "rate": settings.EV_TYPE2_RATE},
    "ccs2":  {"name": "DC Fast (60 kW)",   "rate": settings.EV_CCS2_RATE},
}


class EVBillingSystem:
    """
    Calculates and generates EV charging bills.

    Bill Components:
        - Charging fee (kWh × rate/kWh)
        - Parking fee (if combined session)
        - Taxes (GST 18%)
        - Any applicable discounts

    Usage:
        biller = EVBillingSystem()
        bill = biller.calculate(kwh=15.5, charger_type="type2")
        biller.generate_invoice(bill, session_data)
    """

    GST_RATE = 0.18  # 18% GST on EV charging

    def __init__(self, receipts_dir: str = "module6_ev_charging/receipts/"):
        self.receipts_dir = receipts_dir
        os.makedirs(receipts_dir, exist_ok=True)

    def calculate(
        self,
        kwh_consumed: float,
        charger_type: str = "type2",
        parking_fee: float = 0.0,
        is_member: bool = False,
        include_gst: bool = True
    ) -> dict:
        """
        Calculate complete EV charging bill.

        Args:
            kwh_consumed: Energy consumed in kWh
            charger_type: 'type1', 'type2', or 'ccs2'
            parking_fee: Associated parking fee (if any)
            is_member: Member discount applied
            include_gst: Apply GST to charging fee

        Returns:
            Bill dict with itemized breakdown
        """
        charger_info = CHARGER_RATES.get(charger_type, CHARGER_RATES["type2"])
        rate = charger_info["rate"]

        # Charging fee
        charging_fee = round(kwh_consumed * rate, 2)

        # Member discount (10%)
        member_discount = round(charging_fee * 0.10, 2) if is_member else 0.0
        fee_after_discount = charging_fee - member_discount

        # GST
        gst_amount = round(fee_after_discount * self.GST_RATE, 2) if include_gst else 0.0

        # Combined total
        ev_subtotal = fee_after_discount + gst_amount
        grand_total = round(ev_subtotal + parking_fee, 2)

        bill = {
            "charger_type": charger_type,
            "charger_name": charger_info["name"],
            "rate_per_kwh": rate,
            "kwh_consumed": round(kwh_consumed, 3),
            "charging_fee": charging_fee,
            "member_discount": member_discount,
            "fee_after_discount": round(fee_after_discount, 2),
            "gst_rate_pct": self.GST_RATE * 100,
            "gst_amount": gst_amount,
            "ev_total": round(ev_subtotal, 2),
            "parking_fee": parking_fee,
            "grand_total": grand_total,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(
            f"EV Bill | {charger_type} | {kwh_consumed} kWh | "
            f"₹{charging_fee} + GST ₹{gst_amount} = ₹{ev_subtotal:.2f}"
        )
        return bill

    def generate_invoice(self, bill: dict, session: dict) -> str:
        """
        Generate HTML invoice for an EV charging session.

        Args:
            bill: Bill dict from calculate()
            session: Session dict with plate_number, start_time, end_time, charger_id

        Returns:
            Path to generated HTML invoice file
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        invoice_num = f"EV-INV-{ts}"
        filename = os.path.join(self.receipts_dir, f"ev_invoice_{ts}.html")

        plate = session.get("plate_number", "N/A")
        charger_id = session.get("charger_id", "N/A")
        start = _fmt_time(session.get("start_time"))
        end = _fmt_time(session.get("end_time"))
        dur = session.get("duration_minutes", 0)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>EV Invoice — {invoice_num}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial; background: #f8fafc; margin: 0; padding: 20px; }}
  .card {{ max-width: 520px; margin: auto; background: #fff; border-radius: 16px;
           padding: 32px; box-shadow: 0 4px 24px rgba(0,0,0,0.1); }}
  .header {{ text-align: center; background: linear-gradient(135deg,#16a34a,#15803d);
             color: #fff; border-radius: 12px; padding: 24px; margin-bottom: 24px; }}
  .header h1 {{ margin: 0 0 4px; font-size: 1.6em; }}
  .header p {{ margin: 0; opacity: 0.85; font-size: 0.85em; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
  td {{ padding: 10px 8px; border-bottom: 1px solid #f1f5f9; font-size: 0.9em; }}
  td:first-child {{ color: #6b7280; }}
  td:last-child {{ text-align: right; font-weight: 600; color: #111827; }}
  .total-row td {{ color: #15803d !important; font-size: 1.15em;
                   border-top: 2px solid #16a34a; background: #f0fdf4; }}
  .badge {{ display: inline-flex; align-items: center; gap: 8px; background: #dcfce7;
            color: #15803d; padding: 6px 14px; border-radius: 99px; font-weight: 600;
            margin: 16px 0; }}
  .footer {{ text-align: center; color: #94a3b8; font-size: 0.8em; margin-top: 20px; }}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <h1>⚡ EV Charging Invoice</h1>
    <p>ParkPilot EV Charging Network</p>
  </div>

  <div style="text-align:center">
    <div class="badge">🔋 {bill['kwh_consumed']} kWh charged via {bill['charger_name']}</div>
  </div>

  <table>
    <tr><td>Invoice Number</td><td>{invoice_num}</td></tr>
    <tr><td>Vehicle Plate</td><td>{plate}</td></tr>
    <tr><td>Charger ID</td><td>{charger_id}</td></tr>
    <tr><td>Charger Type</td><td>{bill['charger_name']}</td></tr>
    <tr><td>Session Start</td><td>{start}</td></tr>
    <tr><td>Session End</td><td>{end}</td></tr>
    <tr><td>Duration</td><td>{dur:.0f} minutes</td></tr>
    <tr><td>Energy Consumed</td><td>{bill['kwh_consumed']} kWh</td></tr>
    <tr><td>Rate</td><td>₹{bill['rate_per_kwh']}/kWh</td></tr>
    <tr><td>Charging Fee</td><td>₹{bill['charging_fee']:.2f}</td></tr>
    {"<tr><td>Member Discount</td><td>-₹" + str(bill['member_discount']) + "</td></tr>" if bill['member_discount'] > 0 else ""}
    <tr><td>GST (18%)</td><td>₹{bill['gst_amount']:.2f}</td></tr>
    {"<tr><td>Parking Fee</td><td>₹" + str(bill['parking_fee']) + "</td></tr>" if bill['parking_fee'] > 0 else ""}
    <tr class="total-row"><td>TOTAL PAYABLE</td><td>₹{bill['grand_total']:.2f}</td></tr>
  </table>

  <div class="footer">
    <p>🌱 Every kWh charged at ParkPilot is powered by renewable energy targets.</p>
    <p>Zero direct CO₂ emissions | Zero Emission Vehicle — Thank you!</p>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
  </div>
</div>
</body>
</html>"""

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"EV invoice generated: {filename}")
        return filename


def _fmt_time(t) -> str:
    if isinstance(t, datetime):
        return t.strftime("%d %b %Y, %I:%M %p")
    if isinstance(t, str):
        try:
            return datetime.fromisoformat(t).strftime("%d %b %Y, %I:%M %p")
        except ValueError:
            return t
    return str(t) if t else "N/A"


if __name__ == "__main__":
    biller = EVBillingSystem()
    bill = biller.calculate(kwh_consumed=18.5, charger_type="ccs2", parking_fee=70.0)
    print(f"\nEV Bill Summary:")
    for k, v in bill.items():
        print(f"  {k}: {v}")

    invoice = biller.generate_invoice(bill, {
        "plate_number": "KA05AB1234",
        "charger_id": "EV-CCS2-03",
        "start_time": "2024-01-15T10:00:00",
        "end_time": "2024-01-15T10:45:00",
        "duration_minutes": 45
    })
    print(f"\nInvoice: {invoice}")
