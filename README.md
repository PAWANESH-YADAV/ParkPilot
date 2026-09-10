# ParkPilot — Autonomous Parking Lot System

ParkPilot is a comprehensive, 12-module autonomous parking lot management system utilizing AI, computer vision, IoT, and machine learning to optimize the parking experience for users and lot administrators.

## 🏗️ Architecture

```mermaid
graph TD
    subgraph Frontend
        A[Next.js Admin Dashboard]
        B[Flutter Mobile App]
    end

    subgraph Backend
        C[FastAPI Core API]
        D[(PostgreSQL)]
        E[AI Services / OpenCV / ML]
    end

    A <-->|REST| C
    B <-->|REST| C
    C <--> D
    C <--> E
```

## 🧩 The 12 Modules

1. **Parking Detection**: Real-time vehicle detection and counting using YOLOv8.
2. **ANPR**: Automatic Number Plate Recognition for seamless entry/exit tracking.
3. **Surveillance**: Intelligent activity monitoring, loitering detection, and automated alerts.
4. **Admin Dashboard**: Comprehensive Next.js interface for managing operations and viewing analytics.
5. **Mobile App**: Flutter application for users to book slots, view availability, and manage their profile.
6. **EV Charging**: Locating stations, starting/stopping sessions, and billing for electric vehicles.
7. **Demand Prediction**: Machine learning models for forecasting parking demand and occupancy.
8. **QR System**: Generating and validating QR code tickets for session access and visitors.
9. **Navigation**: Indoor routing and LED directional controller for finding slots easily.
10. **Carbon Tracker**: Gamified system tracking CO2 savings, awarding badges, and offering green reports.
11. **Voice Assistant**: Natural language processing kiosk for voice-driven user commands.
12. **Dynamic Pricing**: Algorithms to adjust pricing based on real-time occupancy, weather, and events.

## 🚀 Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 18+
- Flutter SDK (for mobile app)
- PostgreSQL
- Docker & Docker Compose (optional but recommended)

### 1. Database Setup
Ensure PostgreSQL is running and create a database named `parkpilot`.

### 2. Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations (if configured)
# alembic upgrade head

# Start FastAPI server
cd backend
uvicorn app.main:app --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. ML Models
Generate the dynamic pricing model:
```bash
python module12_dynamic_pricing/generate_model.py
```

## 📡 API Reference Overview

The FastAPI backend provides modular endpoints mapped to `/api/v1`. Visit `http://localhost:8000/docs` for the interactive Swagger UI.

- **`/ev`**: `POST /session/start`, `POST /session/{id}/stop`, `GET /queue`
- **`/qr`**: `POST /generate`, `POST /scan`, `GET /visitor`
- **`/carbon`**: `GET /user/{id}`, `GET /badges/{id}`, `GET /report/monthly`
- **`/voice`**: `POST /command`, `GET /history/{user_id}`
- **`/security`**: `GET /events`, `POST /events`, `PATCH /events/{id}/resolve`
- **`/pricing`**: `GET /current/{lot_id}`, `POST /update`, `GET /history/{lot_id}`

## 🔐 Environment Variables

Create a `.env` file in the `backend/` directory:
```ini
PROJECT_NAME="ParkPilot"
PROJECT_VERSION="1.0.0"
API_V1_STR="/api/v1"
DATABASE_URL="postgresql://user:password@localhost:5432/parkpilot"
SECRET_KEY="your_super_secret_key"
STRIPE_API_KEY="sk_test_..."
OPENAI_API_KEY="sk-..."
```

Create a `.env.local` in the `frontend/` directory:
```ini
NEXT_PUBLIC_API_URL="http://localhost:8000/api/v1"
```

## 🚢 Deployment Guide

### Using Docker Compose
The easiest way to deploy the entire stack is using Docker Compose:

```bash
docker-compose up -d --build
```

This will spin up:
- The Next.js frontend on `http://localhost:3000`
- The FastAPI backend on `http://localhost:8000`
- The PostgreSQL database on `localhost:5432`

## 🧪 Testing

Run the test suites to verify functionality:
```bash
# Run unit tests
python tests/unit_tests.py

# Run integration tests
python tests/integration_tests.py
```
