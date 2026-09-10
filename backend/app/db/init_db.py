from app.db.session import Base, engine, SessionLocal
from app.models.models import (
    User, Vehicle, ParkingLot, ParkingSlot, Reservation,
    ParkingSession, Transaction, Sensor, CameraFeed,
    ANPRLog, OccupancyLog, DemandPrediction, DynamicPricing,
    UserRole, ParkingSlotStatus, VehicleType
)
from app.core.security import get_password_hash


PARKING_LOTS_DATA = [
    {
        "name": "Downtown Garage",
        "address": "123 Main St, Downtown",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "total_slots": 150,
        "price_per_hour": 15.0,
        "vehicle_types": ["car", "bike"],
        "features": ["24/7", "Security", "EV Charging"],
        "rating": 4.8,
    },
    {
        "name": "City Center Parking",
        "address": "456 Oak Ave, City Center",
        "latitude": 40.7580,
        "longitude": -73.9855,
        "total_slots": 100,
        "price_per_hour": 12.0,
        "vehicle_types": ["car"],
        "features": ["24/7", "Security"],
        "rating": 4.5,
    },
    {
        "name": "Waterfront Parking",
        "address": "789 River Rd, Waterfront",
        "latitude": 40.7061,
        "longitude": -74.0088,
        "total_slots": 200,
        "price_per_hour": 10.0,
        "vehicle_types": ["car", "bike", "suv"],
        "features": ["24/7", "Security", "EV Charging", "Wash"],
        "rating": 4.6,
    },
    {
        "name": "Uptown Plaza",
        "address": "321 Park Blvd, Uptown",
        "latitude": 40.7851,
        "longitude": -73.9683,
        "total_slots": 120,
        "price_per_hour": 18.0,
        "vehicle_types": ["car", "bike"],
        "features": ["24/7", "Security", "EV Charging", "Valet"],
        "rating": 4.9,
    },
    {
        "name": "Airport Long Stay",
        "address": "999 Airport Rd",
        "latitude": 40.6413,
        "longitude": -73.7781,
        "total_slots": 500,
        "price_per_hour": 8.0,
        "vehicle_types": ["car", "suv"],
        "features": ["24/7", "Shuttle", "Security", "Covered"],
        "rating": 4.3,
    },
    {
        "name": "Mall Parking",
        "address": "500 Shopping Ave",
        "latitude": 40.7484,
        "longitude": -73.9857,
        "total_slots": 350,
        "price_per_hour": 5.0,
        "vehicle_types": ["car", "bike"],
        "features": ["Security", "Covered", "Handicap Access"],
        "rating": 4.1,
    },
]


def _seed_parking_data(db):
    if db.query(ParkingLot).count() > 0:
        print("Parking data already seeded, skipping...")
        return

    print("Seeding parking lots and slots...")
    for idx, lot_data in enumerate(PARKING_LOTS_DATA):
        lot = ParkingLot(**lot_data)
        db.add(lot)
        db.flush()

        n = lot.total_slots
        rows = max(1, n // 10)
        letters = [chr(65 + i % 26) for i in range(rows)]
        for i in range(min(n, 50)):
            row_idx = i // 10
            col = (i % 10) + 1
            letter = letters[row_idx] if row_idx < len(letters) else "A"
            slot_num = f"{letter}-{col:02d}"
            available = i < int(n * 0.55)
            status = ParkingSlotStatus.AVAILABLE if available else ParkingSlotStatus.OCCUPIED
            slot = ParkingSlot(
                parking_lot_id=lot.id,
                slot_number=slot_num,
                status=status,
            )
            db.add(slot)

    db.commit()
    print(f"Seeded {len(PARKING_LOTS_DATA)} parking lots with slots.")


def _seed_admin_user(db):
    admin_email = "admin@parkpilot.com"
    existing = db.query(User).filter(User.email == admin_email).first()
    if existing:
        print("Admin user already exists, skipping...")
        return
    print("Seeding admin user...")
    admin = User(
        email=admin_email,
        full_name="ParkPilot Admin",
        hashed_password=get_password_hash("Admin@123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)

    user_email = "user@parkpilot.com"
    existing_user = db.query(User).filter(User.email == user_email).first()
    if not existing_user:
        normal_user = User(
            email=user_email,
            full_name="Test User",
            hashed_password=get_password_hash("User@123"),
            role=UserRole.DRIVER,
            is_active=True,
        )
        db.add(normal_user)

    db.commit()
    print("Admin user seeded (admin@parkpilot.com / Admin@123)")
    print("Test user seeded (user@parkpilot.com / User@123)")


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

    db = SessionLocal()
    try:
        _seed_admin_user(db)
        _seed_parking_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
