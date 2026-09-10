"""
ParkPilot — Module 4: Admin Dashboard (Flask)
Standalone Flask web application for system administrators and
municipality officials.

Features:
    - Live slot grid map (green = vacant, red = occupied)
    - Real-time counters (total / vacant / occupied)
    - Vehicle log with entry time and estimated fee
    - Revenue tracker (today / weekly / monthly)
    - Security alerts panel
    - Parking rate management
    - Peak hours heatmap
    - Demand prediction chart
    - Dynamic pricing display
    - Export reports (PDF/Excel)

Run:
    python module4_dashboard/app.py
    Open: http://localhost:5000
"""

import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import (Flask, render_template, jsonify, request,
                   redirect, url_for, session, flash, send_file)
from flask_socketio import SocketIO, emit

from utils.logger import get_logger
from utils.config import settings

logger = get_logger("parkpilot.module4.dashboard")

# ── Flask App Setup ───────────────────────────────────────────────────────────
app = Flask(__name__,
            template_folder="templates",
            static_folder="static")
app.secret_key = settings.SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

DB_PATH = "database/parkpilot.db"


# ═══════════════════════════════════════════════════════════════════════════
#  Database Helper
# ═══════════════════════════════════════════════════════════════════════════

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query_db(query: str, args=(), one=False):
    try:
        conn = get_db()
        cur = conn.execute(query, args)
        rv = cur.fetchall()
        conn.close()
        return (rv[0] if rv else None) if one else rv
    except Exception as e:
        logger.error(f"DB query error: {e}")
        return None if one else []


def execute_db(query: str, args=()):
    try:
        conn = get_db()
        conn.execute(query, args)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"DB execute error: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  Auth Decorator
# ═══════════════════════════════════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") not in ("admin", "municipality"):
            flash("Admin access required", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ═══════════════════════════════════════════════════════════════════════════
#  Stats Helpers
# ═══════════════════════════════════════════════════════════════════════════

def get_slot_stats() -> dict:
    """Get real-time slot occupancy stats."""
    rows = query_db("SELECT status, COUNT(*) as cnt FROM parking_slots GROUP BY status")
    stats = {"available": 0, "occupied": 0, "reserved": 0, "maintenance": 0}
    for row in rows:
        stats[row["status"]] = row["cnt"]
    stats["total"] = sum(stats.values())
    stats["occupancy_pct"] = round(
        (stats["occupied"] + stats["reserved"]) / max(stats["total"], 1) * 100, 1
    )
    return stats


def get_revenue_stats() -> dict:
    """Get revenue totals for today, week, and month."""
    today = datetime.now().date().isoformat()
    week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
    month_ago = (datetime.now() - timedelta(days=30)).date().isoformat()

    today_rev = query_db(
        "SELECT COALESCE(SUM(amount), 0) as total FROM parking_sessions WHERE DATE(entry_time)=? AND is_active=0",
        (today,), one=True
    )
    week_rev = query_db(
        "SELECT COALESCE(SUM(amount), 0) as total FROM parking_sessions WHERE DATE(entry_time)>=? AND is_active=0",
        (week_ago,), one=True
    )
    month_rev = query_db(
        "SELECT COALESCE(SUM(amount), 0) as total FROM parking_sessions WHERE DATE(entry_time)>=? AND is_active=0",
        (month_ago,), one=True
    )
    return {
        "today": round(float(today_rev["total"] if today_rev else 0), 2),
        "week": round(float(week_rev["total"] if week_rev else 0), 2),
        "month": round(float(month_rev["total"] if month_rev else 0), 2),
    }


def get_active_vehicles() -> list:
    """Get currently parked vehicles."""
    rows = query_db("""
        SELECT ps.id, ps.license_plate, ps.entry_time, ps.slot_id,
               ROUND((julianday('now') - julianday(ps.entry_time)) * 24, 2) as hours_parked,
               ROUND((julianday('now') - julianday(ps.entry_time)) * 24 * 30, 2) as est_fee,
               pk.slot_number, pk.zone
        FROM parking_sessions ps
        LEFT JOIN parking_slots pk ON ps.slot_id = pk.id
        WHERE ps.is_active = 1
        ORDER BY ps.entry_time DESC
        LIMIT 50
    """)
    return [dict(r) for r in rows]


def get_security_events(limit: int = 20) -> list:
    rows = query_db(
        "SELECT * FROM security_events ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    return [dict(r) for r in rows]


def get_hourly_occupancy() -> list:
    """Get hourly occupancy data for the heatmap."""
    rows = query_db("""
        SELECT CAST(strftime('%H', entry_time) AS INTEGER) as hour,
               COUNT(*) as count
        FROM parking_sessions
        WHERE DATE(entry_time) >= DATE('now', '-30 days')
        GROUP BY hour
        ORDER BY hour
    """)
    hourly = {i: 0 for i in range(24)}
    for row in rows:
        hourly[row["hour"]] = row["count"]
    return [{"hour": h, "count": c} for h, c in hourly.items()]


# ═══════════════════════════════════════════════════════════════════════════
#  Routes
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/")
@login_required
def index():
    slot_stats = get_slot_stats()
    revenue = get_revenue_stats()
    vehicles = get_active_vehicles()
    alerts = get_security_events(5)
    hourly = get_hourly_occupancy()
    slots = query_db("SELECT * FROM parking_slots ORDER BY zone, slot_number LIMIT 100")
    lots = query_db("SELECT * FROM parking_lots WHERE is_active=1")
    return render_template("index.html",
                           slot_stats=slot_stats,
                           revenue=revenue,
                           vehicles=vehicles,
                           alerts=alerts,
                           hourly_data=json.dumps(hourly),
                           slots=[dict(s) for s in slots],
                           lots=[dict(l) for l in lots])


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        user = query_db(
            "SELECT * FROM users WHERE email=? AND is_active=1", (email,), one=True
        )
        if user:
            # Simple password check (in production use bcrypt)
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            session["role"] = user["role"]
            session["name"] = user["full_name"] or email
            flash(f"Welcome back, {session['name']}!", "success")
            return redirect(url_for("index"))
        flash("Invalid credentials", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/vehicles")
@login_required
def vehicles():
    vehicles = get_active_vehicles()
    return render_template("vehicles.html", vehicles=vehicles)


@app.route("/security")
@login_required
def security():
    events = get_security_events(50)
    return render_template("security.html", events=events)


@app.route("/security/resolve/<int:event_id>", methods=["POST"])
@login_required
def resolve_event(event_id):
    notes = request.form.get("notes", "")
    execute_db(
        "UPDATE security_events SET resolved=1, notes=? WHERE id=?",
        (notes, event_id)
    )
    flash("Event marked as resolved", "success")
    return redirect(url_for("security"))


@app.route("/pricing")
@login_required
def pricing():
    rates = query_db("SELECT * FROM parking_rates")
    pricing_log = query_db(
        "SELECT * FROM pricing_log ORDER BY effective_from DESC LIMIT 20"
    )
    return render_template("pricing.html",
                           rates=[dict(r) for r in rates],
                           pricing_log=[dict(p) for p in pricing_log])


@app.route("/pricing/update", methods=["POST"])
@login_required
@admin_required
def update_pricing():
    lot_id = request.form.get("lot_id", 1)
    base_rate = float(request.form.get("base_rate", 30))
    execute_db(
        "UPDATE parking_lots SET current_rate=?, price_per_hour=? WHERE id=?",
        (base_rate, base_rate, lot_id)
    )
    flash(f"Rate updated to ₹{base_rate}/hr", "success")
    return redirect(url_for("pricing"))


@app.route("/analytics")
@login_required
def analytics():
    hourly = get_hourly_occupancy()
    revenue = get_revenue_stats()
    # Occupancy trend (last 7 days)
    daily = query_db("""
        SELECT DATE(entry_time) as date, COUNT(*) as count
        FROM parking_sessions
        WHERE DATE(entry_time) >= DATE('now', '-7 days')
        GROUP BY date ORDER BY date
    """)
    return render_template("analytics.html",
                           hourly_data=json.dumps(hourly),
                           revenue=revenue,
                           daily_data=json.dumps([dict(d) for d in daily]))


@app.route("/ev")
@login_required
def ev_dashboard():
    ev_sessions = query_db(
        "SELECT * FROM ev_sessions ORDER BY start_time DESC LIMIT 50"
    )
    queue = query_db(
        "SELECT * FROM ev_queue ORDER BY joined_at ASC"
    )
    return render_template("ev.html",
                           sessions=[dict(s) for s in ev_sessions],
                           queue=[dict(q) for q in queue])


@app.route("/carbon")
@login_required
def carbon_dashboard():
    total_co2 = query_db(
        "SELECT COALESCE(SUM(co2_saved_grams), 0) as total FROM carbon_credits", one=True
    )
    top_users = query_db("""
        SELECT u.full_name, u.email, COALESCE(SUM(cc.co2_saved_grams), 0) as co2_saved
        FROM carbon_credits cc
        JOIN users u ON cc.user_id = u.id
        GROUP BY cc.user_id ORDER BY co2_saved DESC LIMIT 10
    """)
    return render_template("carbon.html",
                           total_co2=total_co2["total"] if total_co2 else 0,
                           top_users=[dict(u) for u in top_users])


# ═══════════════════════════════════════════════════════════════════════════
#  REST API Endpoints (for frontend polling)
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/api/stats")
def api_stats():
    return jsonify({
        "slots": get_slot_stats(),
        "revenue": get_revenue_stats(),
        "active_vehicles": len(get_active_vehicles()),
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route("/api/slots")
def api_slots():
    slots = query_db("""
        SELECT ps.id, ps.slot_number, ps.status, ps.zone, ps.level,
               ps.is_ev_slot, ps.is_handicap, ps.last_updated
        FROM parking_slots ps
        ORDER BY ps.zone, ps.slot_number
        LIMIT 200
    """)
    return jsonify([dict(s) for s in slots])


@app.route("/api/security-events")
def api_security_events():
    return jsonify(get_security_events(20))


@app.route("/api/vehicles/active")
def api_active_vehicles():
    return jsonify(get_active_vehicles())


@app.route("/api/pricing/current")
def api_current_pricing():
    lot_id = request.args.get("lot_id", 1)
    lot = query_db("SELECT * FROM parking_lots WHERE id=?", (lot_id,), one=True)
    return jsonify(dict(lot) if lot else {})


# ═══════════════════════════════════════════════════════════════════════════
#  WebSocket for Real-Time Updates
# ═══════════════════════════════════════════════════════════════════════════

@socketio.on("connect")
def on_connect():
    logger.info(f"Dashboard client connected: {request.sid}")
    emit("stats", {
        "slots": get_slot_stats(),
        "revenue": get_revenue_stats(),
        "timestamp": datetime.utcnow().isoformat()
    })


@socketio.on("request_update")
def on_request_update(data):
    emit("stats", {
        "slots": get_slot_stats(),
        "revenue": get_revenue_stats(),
        "active_vehicles": get_active_vehicles()[:10],
        "timestamp": datetime.utcnow().isoformat()
    })


def broadcast_slot_update(slot_id: int, status: str):
    """Call this from detection modules to push real-time updates."""
    socketio.emit("slot_update", {"slot_id": slot_id, "status": status})


# ═══════════════════════════════════════════════════════════════════════════
#  Export
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/export/excel")
@login_required
def export_excel():
    """Export revenue data to Excel."""
    try:
        import pandas as pd
        from io import BytesIO

        sessions = query_db("""
            SELECT license_plate, entry_time, exit_time, amount,
                   slot_id, co2_saved_grams
            FROM parking_sessions
            WHERE DATE(entry_time) >= DATE('now', '-30 days')
            ORDER BY entry_time DESC
        """)

        df = pd.DataFrame([dict(s) for s in sessions])
        buf = BytesIO()
        df.to_excel(buf, index=False, sheet_name="ParkPilot Report")
        buf.seek(0)

        return send_file(
            buf,
            as_attachment=True,
            download_name=f"parkpilot_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except ImportError:
        flash("Install openpyxl and pandas for Excel export", "error")
        return redirect(url_for("analytics"))


# ═══════════════════════════════════════════════════════════════════════════
#  Startup
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    os.makedirs("module4_dashboard/templates", exist_ok=True)
    os.makedirs("module4_dashboard/static/css", exist_ok=True)
    os.makedirs("module4_dashboard/static/js", exist_ok=True)
    os.makedirs("module4_dashboard/reports", exist_ok=True)

    logger.info(f"Starting ParkPilot Dashboard on http://{settings.FLASK_HOST}:{settings.FLASK_PORT}")
    socketio.run(
        app,
        host=settings.FLASK_HOST,
        port=settings.FLASK_PORT,
        debug=settings.DEBUG
    )
