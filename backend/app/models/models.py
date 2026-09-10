from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class UserRole(str, enum.Enum):
    DRIVER = "driver"
    ADMIN = "admin"
    MUNICIPALITY = "municipality"
    PROVIDER = "provider"
    BILLING = "billing"
    DATA_SCIENTIST = "data_scientist"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String)
    role = Column(SQLEnum(UserRole), default=UserRole.DRIVER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    vehicles = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")
    reservations = relationship("Reservation", back_populates="user")
    parking_sessions = relationship("ParkingSession", back_populates="user")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    license_plate = Column(String, unique=True, index=True, nullable=False)
    make = Column(String)
    model = Column(String)
    year = Column(Integer)
    color = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="vehicles")
    parking_sessions = relationship("ParkingSession", back_populates="vehicle")


class ParkingLot(Base):
    __tablename__ = "parking_lots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    total_slots = Column(Integer, default=0)
    price_per_hour = Column(Float, default=10.0)
    is_active = Column(Boolean, default=True)
    vehicle_types = Column(JSON, default=[])
    features = Column(JSON, default=[])
    rating = Column(Float, default=4.5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    slots = relationship("ParkingSlot", back_populates="parking_lot", cascade="all, delete-orphan")


class ParkingSlotStatus(str, enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"


class ReservationStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VehicleType(str, enum.Enum):
    CAR = "car"
    BIKE = "bike"
    SUV = "suv"


class PaymentMethod(str, enum.Enum):
    CARD = "card"
    UPI = "upi"
    WALLET = "wallet"


class ParkingSlot(Base):
    __tablename__ = "parking_slots"

    id = Column(Integer, primary_key=True, index=True)
    parking_lot_id = Column(Integer, ForeignKey("parking_lots.id"), nullable=False)
    slot_number = Column(String, nullable=False)
    status = Column(SQLEnum(ParkingSlotStatus), default=ParkingSlotStatus.AVAILABLE)
    sensor_id = Column(String)
    camera_id = Column(String)
    coordinates = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    parking_lot = relationship("ParkingLot", back_populates="slots")
    reservations = relationship("Reservation", back_populates="slot")
    parking_sessions = relationship("ParkingSession", back_populates="slot")


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    slot_id = Column(Integer, ForeignKey("parking_slots.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(SQLEnum(ReservationStatus), default=ReservationStatus.PENDING)
    amount = Column(Float, default=0.0)
    license_plate = Column(String)
    vehicle_type = Column(SQLEnum(VehicleType), default=VehicleType.CAR)
    payment_method = Column(SQLEnum(PaymentMethod), default=PaymentMethod.CARD)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="reservations")
    slot = relationship("ParkingSlot", back_populates="reservations")


class ParkingSession(Base):
    __tablename__ = "parking_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    slot_id = Column(Integer, ForeignKey("parking_slots.id"), nullable=False)
    entry_time = Column(DateTime(timezone=True), nullable=False)
    exit_time = Column(DateTime(timezone=True))
    license_plate = Column(String)
    amount = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="parking_sessions")
    vehicle = relationship("Vehicle", back_populates="parking_sessions")
    slot = relationship("ParkingSlot", back_populates="parking_sessions")
    transaction = relationship("Transaction", back_populates="session", uselist=False)


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("parking_sessions.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    payment_method = Column(String)
    stripe_payment_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ParkingSession", back_populates="transaction")


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, unique=True, index=True, nullable=False)
    slot_id = Column(Integer, ForeignKey("parking_slots.id"))
    type = Column(String)
    status = Column(String, default="online")
    last_reading = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CameraFeed(Base):
    __tablename__ = "camera_feeds"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, unique=True, index=True, nullable=False)
    parking_lot_id = Column(Integer, ForeignKey("parking_lots.id"))
    rtsp_url = Column(String)
    status = Column(String, default="online")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ANPRLog(Base):
    __tablename__ = "anpr_logs"

    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String, index=True)
    camera_id = Column(String)
    image_path = Column(String)
    confidence = Column(Float)
    direction = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OccupancyLog(Base):
    __tablename__ = "occupancy_logs"

    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("parking_slots.id"))
    status = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class DemandPrediction(Base):
    __tablename__ = "demand_predictions"

    id = Column(Integer, primary_key=True, index=True)
    parking_lot_id = Column(Integer, ForeignKey("parking_lots.id"))
    prediction_time = Column(DateTime(timezone=True), nullable=False)
    predicted_occupancy = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DynamicPricing(Base):
    __tablename__ = "dynamic_pricing"

    id = Column(Integer, primary_key=True, index=True)
    parking_lot_id = Column(Integer, ForeignKey("parking_lots.id"))
    base_price = Column(Float)
    surge_multiplier = Column(Float, default=1.0)
    effective_price = Column(Float)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Module 6: EV Session ─────────────────────────────────────────────────────

class EVSessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    FAULT = "fault"


class EVSession(Base):
    __tablename__ = "ev_sessions"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, index=True)
    charger_id = Column(String, nullable=False)
    charger_type = Column(String)  # type1, type2, ccs2
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    kwh_consumed = Column(Float, default=0.0)
    fee_amount = Column(Float, default=0.0)
    rate_per_kwh = Column(Float)
    status = Column(SQLEnum(EVSessionStatus), default=EVSessionStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Module 3: Security Event ─────────────────────────────────────────────────

class SecurityEventType(str, enum.Enum):
    LOITERING = "loitering"
    VANDALISM = "vandalism"
    UNAUTHORIZED = "unauthorized"
    ACCIDENT = "accident"
    OTHER = "other"


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(SQLEnum(SecurityEventType), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    camera_id = Column(String)
    location_zone = Column(String)
    clip_path = Column(String)
    snapshot_path = Column(String)
    resolved = Column(Boolean, default=False)
    notified = Column(Boolean, default=False)
    notes = Column(Text)


# ─── Module 8: QR Ticket ──────────────────────────────────────────────────────

class QRTicketType(str, enum.Enum):
    SESSION = "session"
    VISITOR = "visitor"
    PREPAID = "prepaid"
    MONTHLY = "monthly"


class QRTicket(Base):
    __tablename__ = "qr_tickets"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, nullable=False)
    qr_code_hash = Column(String, unique=True, nullable=False, index=True)
    slot_id = Column(Integer, ForeignKey("parking_slots.id"))
    entry_time = Column(DateTime(timezone=True), nullable=False)
    used_status = Column(Integer, default=0)  # 0=unused, 1=used, 2=expired
    expiry_time = Column(DateTime(timezone=True))
    ticket_type = Column(SQLEnum(QRTicketType), default=QRTicketType.SESSION)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Module 10: Carbon Credit ─────────────────────────────────────────────────

class CarbonCredit(Base):
    __tablename__ = "carbon_credits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(Integer, ForeignKey("parking_sessions.id"))
    co2_saved_grams = Column(Float, default=0.0)
    fuel_saved_ml = Column(Float, default=0.0)
    tree_equivalent = Column(Float, default=0.0)
    badge_awarded = Column(String)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())


# ─── Module 11: Voice Command ─────────────────────────────────────────────────

class VoiceCommand(Base):
    __tablename__ = "voice_commands"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    raw_text = Column(Text)
    intent = Column(String)
    confidence = Column(Float)
    response_text = Column(Text)
    success = Column(Boolean, default=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
