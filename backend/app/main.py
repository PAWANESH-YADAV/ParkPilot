from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session import engine, Base
from app.api.v1 import (
    auth, parking, vehicles, reservations, anpr, sensors, ai, billing,
    ev_charging, qr_tickets, carbon, voice, security, pricing,
)
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="ParkPilot Autonomous Parking System — Complete 12-Module API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import APIRouter

api_router = APIRouter()

# ─── Core Modules ─────────────────────────────────────────────────────────────
api_router.include_router(auth.router)
api_router.include_router(parking.router)
api_router.include_router(vehicles.router)
api_router.include_router(reservations.router)
api_router.include_router(anpr.router)
api_router.include_router(sensors.router)
api_router.include_router(ai.router)
api_router.include_router(billing.router)

# ─── Extended Modules ─────────────────────────────────────────────────────────
api_router.include_router(ev_charging.router)    # Module 6
api_router.include_router(qr_tickets.router)     # Module 8
api_router.include_router(carbon.router)         # Module 10
api_router.include_router(voice.router)          # Module 11
api_router.include_router(security.router)       # Module 3
api_router.include_router(pricing.router)        # Module 12

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "message": "ParkPilot API",
        "version": settings.PROJECT_VERSION,
        "modules": 12,
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
