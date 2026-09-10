-- ═══════════════════════════════════════════════════════════════════════════
-- ParkPilot — Complete Database Schema
-- Compatible with SQLite and PostgreSQL
-- ═══════════════════════════════════════════════════════════════════════════

PRAGMA foreign_keys = ON;

-- ─── Users & Auth ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT    UNIQUE NOT NULL,
    full_name       TEXT,
    hashed_password TEXT,
    phone           TEXT,
    role            TEXT    DEFAULT 'driver'
                            CHECK(role IN ('driver','admin','municipality','provider','billing','data_scientist')),
    is_active       INTEGER DEFAULT 1,
    fcm_token       TEXT,                       -- Firebase push token
    co2_saved_total REAL    DEFAULT 0.0,        -- Module 10: lifetime CO2 saved (grams)
    eco_points      INTEGER DEFAULT 0,          -- Module 10: green badge points
    created_at      TEXT    DEFAULT (datetime('now')),
    updated_at      TEXT
);

-- ─── Vehicles ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vehicles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER REFERENCES users(id) ON DELETE CASCADE,
    license_plate   TEXT    UNIQUE NOT NULL,
    make            TEXT,
    model           TEXT,
    year            INTEGER,
    color           TEXT,
    vehicle_type    TEXT    DEFAULT 'car'
                            CHECK(vehicle_type IN ('car','bike','truck','ev','handicap')),
    is_ev           INTEGER DEFAULT 0,
    is_handicap     INTEGER DEFAULT 0,
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ─── Parking Lots ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS parking_lots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    address         TEXT,
    latitude        REAL,
    longitude       REAL,
    total_slots     INTEGER DEFAULT 0,
    ev_slots        INTEGER DEFAULT 0,
    levels          INTEGER DEFAULT 1,          -- Multi-level support (Module 9)
    price_per_hour  REAL    DEFAULT 30.0,
    current_rate    REAL    DEFAULT 30.0,       -- Dynamic rate (Module 12)
    is_active       INTEGER DEFAULT 1,
    created_at      TEXT    DEFAULT (datetime('now')),
    updated_at      TEXT
);

-- ─── Parking Slots ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS parking_slots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    parking_lot_id  INTEGER REFERENCES parking_lots(id) ON DELETE CASCADE,
    slot_number     TEXT    NOT NULL,
    zone            TEXT,                       -- Zone A, B, C
    level           INTEGER DEFAULT 1,          -- Floor level
    status          TEXT    DEFAULT 'available'
                            CHECK(status IN ('available','occupied','reserved','maintenance')),
    sensor_id       TEXT,
    camera_id       TEXT,
    coordinates     TEXT,                       -- JSON: {x, y, width, height}
    is_ev_slot      INTEGER DEFAULT 0,
    is_handicap     INTEGER DEFAULT 0,
    last_updated    TEXT    DEFAULT (datetime('now'))
);

-- ─── Reservations ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reservations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER REFERENCES users(id),
    slot_id         INTEGER REFERENCES parking_slots(id),
    vehicle_id      INTEGER REFERENCES vehicles(id),
    start_time      TEXT    NOT NULL,
    end_time        TEXT    NOT NULL,
    is_active       INTEGER DEFAULT 1,
    auto_release    INTEGER DEFAULT 1,          -- Release slot after 15 min grace period
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ─── Parking Sessions ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS parking_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER REFERENCES users(id),
    vehicle_id      INTEGER REFERENCES vehicles(id),
    slot_id         INTEGER REFERENCES parking_slots(id) NOT NULL,
    license_plate   TEXT,
    entry_time      TEXT    NOT NULL,
    exit_time       TEXT,
    duration_hours  REAL,
    amount          REAL    DEFAULT 0.0,
    is_active       INTEGER DEFAULT 1,
    qr_code_hash    TEXT,                       -- Module 8: linked QR ticket
    co2_saved_grams REAL    DEFAULT 0.0,        -- Module 10: CO2 saved this session
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ─── Transactions ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER REFERENCES parking_sessions(id),
    amount          REAL    NOT NULL,
    status          TEXT    DEFAULT 'pending'
                            CHECK(status IN ('pending','completed','failed','refunded')),
    payment_method  TEXT    DEFAULT 'cash'
                            CHECK(payment_method IN ('cash','upi','card','wallet','pass')),
    gateway_txn_id  TEXT,                       -- Razorpay / Paytm transaction ID
    receipt_path    TEXT,                       -- PDF receipt path
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ─── ANPR Logs — Module 2 ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS anpr_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    license_plate   TEXT,
    camera_id       TEXT,
    image_path      TEXT,
    confidence      REAL,
    direction       TEXT    CHECK(direction IN ('entry','exit','detected')),
    raw_text        TEXT,                       -- Raw OCR output before cleanup
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ─── Security Events — Module 3 ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS security_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type      TEXT    NOT NULL
                            CHECK(event_type IN ('loitering','vandalism','unauthorized','accident','other')),
    timestamp       TEXT    DEFAULT (datetime('now')),
    camera_id       TEXT,
    location_zone   TEXT,
    clip_path       TEXT,                       -- Saved video clip path
    snapshot_path   TEXT,                       -- Snapshot image path
    resolved        INTEGER DEFAULT 0,
    notified        INTEGER DEFAULT 0,
    notes           TEXT
);

-- ─── EV Sessions — Module 6 ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ev_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number    TEXT,
    charger_id      TEXT    NOT NULL,
    charger_type    TEXT    CHECK(charger_type IN ('type1','type2','ccs2')),
    start_time      TEXT    NOT NULL,
    end_time        TEXT,
    kwh_consumed    REAL    DEFAULT 0.0,
    fee_amount      REAL    DEFAULT 0.0,
    rate_per_kwh    REAL,
    status          TEXT    DEFAULT 'active'
                            CHECK(status IN ('active','completed','interrupted','fault')),
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ─── EV Queue — Module 6 ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ev_queue (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number    TEXT,
    user_id         INTEGER REFERENCES users(id),
    charger_type    TEXT,
    joined_at       TEXT    DEFAULT (datetime('now')),
    notified        INTEGER DEFAULT 0,
    position        INTEGER
);

-- ─── QR Tickets — Module 8 ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS qr_tickets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    plate_number    TEXT    NOT NULL,
    qr_code_hash    TEXT    UNIQUE NOT NULL,
    slot_id         INTEGER REFERENCES parking_slots(id),
    entry_time      TEXT    NOT NULL,
    used_status     INTEGER DEFAULT 0,          -- 0=unused, 1=used, 2=expired
    expiry_time     TEXT,
    ticket_type     TEXT    DEFAULT 'session'
                            CHECK(ticket_type IN ('session','visitor','prepaid','monthly')),
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ─── Demand Forecast — Module 7 ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS demand_forecast (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    parking_lot_id      INTEGER REFERENCES parking_lots(id),
    forecast_time       TEXT    NOT NULL,
    predicted_occupancy REAL,                   -- 0.0 to 1.0
    actual_occupancy    REAL,
    model_version       TEXT,
    horizon_hours       INTEGER,                -- 1, 6, 12, or 24
    created_at          TEXT    DEFAULT (datetime('now'))
);

-- ─── Occupancy Logs — Module 1 ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS occupancy_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id         INTEGER REFERENCES parking_slots(id),
    parking_lot_id  INTEGER REFERENCES parking_lots(id),
    status          TEXT    CHECK(status IN ('available','occupied')),
    confidence      REAL,                       -- Detection confidence score
    timestamp       TEXT    DEFAULT (datetime('now'))
);

-- ─── Dynamic Pricing Log — Module 12 ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pricing_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    parking_lot_id  INTEGER REFERENCES parking_lots(id),
    base_rate       REAL,
    occupancy_pct   REAL,
    weather_factor  REAL    DEFAULT 1.0,
    event_factor    REAL    DEFAULT 1.0,
    time_factor     REAL    DEFAULT 1.0,
    surge_multiplier REAL   DEFAULT 1.0,
    final_rate      REAL,
    reason          TEXT,                       -- Human-readable reason for change
    effective_from  TEXT    DEFAULT (datetime('now')),
    effective_to    TEXT
);

-- ─── Carbon Credits — Module 10 ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS carbon_credits (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER REFERENCES users(id),
    session_id      INTEGER REFERENCES parking_sessions(id),
    co2_saved_grams REAL    DEFAULT 0.0,
    fuel_saved_ml   REAL    DEFAULT 0.0,
    tree_equivalent REAL    DEFAULT 0.0,        -- Trees equivalent
    badge_awarded   TEXT,                       -- Badge name if milestone hit
    recorded_at     TEXT    DEFAULT (datetime('now'))
);

-- ─── Sensors ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sensors (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id       TEXT    UNIQUE NOT NULL,
    slot_id         INTEGER REFERENCES parking_slots(id),
    sensor_type     TEXT    DEFAULT 'ultrasonic'
                            CHECK(sensor_type IN ('ultrasonic','infrared','camera','ble','ev_power')),
    status          TEXT    DEFAULT 'online'
                            CHECK(status IN ('online','offline','fault')),
    last_reading    TEXT,
    last_value      TEXT,
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ─── Camera Feeds ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS camera_feeds (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id       TEXT    UNIQUE NOT NULL,
    parking_lot_id  INTEGER REFERENCES parking_lots(id),
    location_desc   TEXT,
    rtsp_url        TEXT,
    status          TEXT    DEFAULT 'online',
    camera_type     TEXT    DEFAULT 'surveillance'
                            CHECK(camera_type IN ('entry','exit','surveillance','parking')),
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ─── Parking Rates ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS parking_rates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    parking_lot_id  INTEGER REFERENCES parking_lots(id),
    vehicle_type    TEXT    DEFAULT 'car',
    base_rate       REAL    NOT NULL,
    additional_hour_rate REAL,
    overnight_rate  REAL,
    ev_discount_pct REAL    DEFAULT 10.0,
    handicap_discount_pct REAL DEFAULT 50.0,
    min_rate_cap    REAL    DEFAULT 20.0,
    max_rate_cap    REAL    DEFAULT 100.0,
    last_updated    TEXT    DEFAULT (datetime('now'))
);

-- ─── Revenue Log ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS revenue_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    parking_lot_id  INTEGER REFERENCES parking_lots(id),
    date            TEXT    NOT NULL,
    total_collected REAL    DEFAULT 0.0,
    vehicle_count   INTEGER DEFAULT 0,
    ev_revenue      REAL    DEFAULT 0.0,
    avg_duration    REAL    DEFAULT 0.0,
    peak_hour       INTEGER,
    created_at      TEXT    DEFAULT (datetime('now'))
);

-- ─── Voice Command Log — Module 11 ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS voice_commands (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER REFERENCES users(id),
    raw_text        TEXT,
    intent          TEXT,
    confidence      REAL,
    response_text   TEXT,
    success         INTEGER DEFAULT 1,
    recorded_at     TEXT    DEFAULT (datetime('now'))
);

-- ─── Indexes for Performance ─────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_vehicles_plate     ON vehicles(license_plate);
CREATE INDEX IF NOT EXISTS idx_sessions_plate     ON parking_sessions(license_plate);
CREATE INDEX IF NOT EXISTS idx_sessions_active    ON parking_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_slots_status       ON parking_slots(status);
CREATE INDEX IF NOT EXISTS idx_slots_lot          ON parking_slots(parking_lot_id);
CREATE INDEX IF NOT EXISTS idx_qr_hash            ON qr_tickets(qr_code_hash);
CREATE INDEX IF NOT EXISTS idx_anpr_plate         ON anpr_logs(license_plate);
CREATE INDEX IF NOT EXISTS idx_security_events    ON security_events(event_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_ev_sessions_plate  ON ev_sessions(plate_number);
CREATE INDEX IF NOT EXISTS idx_forecast_lot_time  ON demand_forecast(parking_lot_id, forecast_time);
CREATE INDEX IF NOT EXISTS idx_carbon_user        ON carbon_credits(user_id);

-- ─── Default Seed Data ───────────────────────────────────────────────────────
INSERT OR IGNORE INTO parking_lots (id, name, address, latitude, longitude, total_slots, ev_slots, price_per_hour)
VALUES
    (1, 'ParkPilot Central', 'MG Road, Bengaluru, Karnataka', 12.9716, 77.5946, 50, 5, 30.0),
    (2, 'ParkPilot North', 'Bandra, Mumbai, Maharashtra', 19.0596, 72.8295, 30, 3, 35.0);

INSERT OR IGNORE INTO parking_rates (parking_lot_id, vehicle_type, base_rate, additional_hour_rate, overnight_rate)
VALUES
    (1, 'car',      30.0, 20.0, 200.0),
    (1, 'bike',     15.0, 10.0, 100.0),
    (1, 'truck',    50.0, 30.0, 300.0),
    (1, 'ev',       27.0, 18.0, 180.0),
    (1, 'handicap', 15.0, 10.0, 100.0);
