from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.models.models import (
    UserRole, ParkingSlotStatus, TransactionStatus,
    EVSessionStatus, SecurityEventType, QRTicketType,
    ReservationStatus, VehicleType, PaymentMethod
)


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class VehicleBase(BaseModel):
    license_plate: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None


class VehicleCreate(VehicleBase):
    pass


class Vehicle(VehicleBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ParkingLotBase(BaseModel):
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    total_slots: int = 0
    price_per_hour: float = 10.0
    vehicle_types: Optional[List[str]] = None
    features: Optional[List[str]] = None
    rating: Optional[float] = None


class ParkingLotCreate(ParkingLotBase):
    pass


class ParkingLot(ParkingLotBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ParkingLotWithAvailability(ParkingLotBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    available_slots: int = 0
    distance: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ParkingSlotBase(BaseModel):
    slot_number: str
    status: ParkingSlotStatus = ParkingSlotStatus.AVAILABLE
    sensor_id: Optional[str] = None
    camera_id: Optional[str] = None


class ParkingSlotCreate(ParkingSlotBase):
    parking_lot_id: int


class ParkingSlot(ParkingSlotBase):
    id: int
    parking_lot_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ReservationBase(BaseModel):
    slot_id: int
    start_time: datetime
    end_time: datetime
    license_plate: Optional[str] = None
    vehicle_type: Optional[VehicleType] = VehicleType.CAR
    payment_method: Optional[PaymentMethod] = PaymentMethod.CARD
    amount: Optional[float] = 0.0


class ReservationCreate(ReservationBase):
    vehicle_id: Optional[int] = None


class ReservationUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[ReservationStatus] = None
    amount: Optional[float] = None
    license_plate: Optional[str] = None
    vehicle_type: Optional[VehicleType] = None
    payment_method: Optional[PaymentMethod] = None
    is_active: Optional[bool] = None


class Reservation(ReservationBase):
    id: int
    user_id: int
    vehicle_id: Optional[int] = None
    status: ReservationStatus
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReservationDetail(ReservationBase):
    id: int
    user_id: int
    vehicle_id: Optional[int] = None
    status: ReservationStatus
    is_active: bool
    created_at: datetime
    parking_lot_id: Optional[int] = None
    parking_lot_name: Optional[str] = None
    slot_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReservationCreateExtended(BaseModel):
    parking_lot_id: int
    start_time: datetime
    end_time: datetime
    license_plate: Optional[str] = None
    vehicle_type: Optional[VehicleType] = VehicleType.CAR
    payment_method: Optional[PaymentMethod] = PaymentMethod.CARD
    vehicle_id: Optional[int] = None
    amount: Optional[float] = None


class ReservationExtend(BaseModel):
    hours: float


class ParkingSessionBase(BaseModel):
    slot_id: int
    license_plate: Optional[str] = None


class ParkingSessionCreate(ParkingSessionBase):
    pass


class ParkingSession(ParkingSessionBase):
    id: int
    user_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    entry_time: datetime
    exit_time: Optional[datetime] = None
    amount: float
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    amount: float
    payment_method: Optional[str] = None


class TransactionCreate(TransactionBase):
    session_id: int


class Transaction(TransactionBase):
    id: int
    session_id: int
    status: TransactionStatus
    stripe_payment_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ANPRRequest(BaseModel):
    image: str
    camera_id: str


class ANPRResponse(BaseModel):
    license_plate: Optional[str] = None
    confidence: float
    success: bool


class SensorUpdate(BaseModel):
    sensor_id: str
    status: str
    occupied: bool


class DemandPredictionResponse(BaseModel):
    parking_lot_id: int
    prediction_time: datetime
    predicted_occupancy: float


class PricingRecommendation(BaseModel):
    parking_lot_id: int
    base_price: float
    surge_multiplier: float
    effective_price: float


class EVSessionBase(BaseModel):
    plate_number: Optional[str] = None
    charger_id: str
    charger_type: Optional[str] = None

class EVSessionCreate(EVSessionBase):
    pass

class EVSession(EVSessionBase):
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    kwh_consumed: float
    fee_amount: float
    rate_per_kwh: Optional[float] = None
    status: EVSessionStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SecurityEventBase(BaseModel):
    event_type: SecurityEventType
    camera_id: Optional[str] = None
    location_zone: Optional[str] = None
    notes: Optional[str] = None

class SecurityEventCreate(SecurityEventBase):
    clip_path: Optional[str] = None
    snapshot_path: Optional[str] = None

class SecurityEvent(SecurityEventBase):
    id: int
    timestamp: datetime
    clip_path: Optional[str] = None
    snapshot_path: Optional[str] = None
    resolved: bool
    notified: bool

    model_config = ConfigDict(from_attributes=True)


class QRTicketBase(BaseModel):
    plate_number: str
    slot_id: Optional[int] = None
    ticket_type: QRTicketType = QRTicketType.SESSION

class QRTicketCreate(QRTicketBase):
    entry_time: datetime
    expiry_time: Optional[datetime] = None

class QRTicket(QRTicketBase):
    id: int
    qr_code_hash: str
    entry_time: datetime
    used_status: int
    expiry_time: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CarbonCreditBase(BaseModel):
    user_id: Optional[int] = None
    session_id: Optional[int] = None
    co2_saved_grams: float = 0.0
    fuel_saved_ml: float = 0.0
    tree_equivalent: float = 0.0
    badge_awarded: Optional[str] = None

class CarbonCreditCreate(CarbonCreditBase):
    pass

class CarbonCredit(CarbonCreditBase):
    id: int
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VoiceCommandBase(BaseModel):
    user_id: Optional[int] = None
    raw_text: str

class VoiceCommandCreate(VoiceCommandBase):
    intent: Optional[str] = None
    confidence: Optional[float] = None

class VoiceCommand(VoiceCommandBase):
    id: int
    intent: Optional[str] = None
    confidence: Optional[float] = None
    response_text: Optional[str] = None
    success: bool
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)
