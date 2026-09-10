"""
ParkPilot — Central Configuration Module
Reads all settings from environment variables with defaults.
Used by all 12 modules.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ─── General ────────────────────────────────────────────────────────────
    PROJECT_NAME: str = "ParkPilot"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "parkpilot-secret-key-change-in-production")

    # ─── Database ────────────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///database/parkpilot.db")

    # ─── Camera / Video ──────────────────────────────────────────────────────
    CAMERA_INDEX: int = int(os.getenv("CAMERA_INDEX", "0"))
    ENTRY_CAM_URL: str = os.getenv("ENTRY_CAM_URL", "0")       # RTSP or index
    EXIT_CAM_URL: str = os.getenv("EXIT_CAM_URL", "1")
    SURV_CAM_URL: str = os.getenv("SURV_CAM_URL", "2")
    FRAME_WIDTH: int = int(os.getenv("FRAME_WIDTH", "1280"))
    FRAME_HEIGHT: int = int(os.getenv("FRAME_HEIGHT", "720"))
    FPS: int = int(os.getenv("FPS", "30"))

    # ─── Parking Slot Detection ──────────────────────────────────────────────
    MODEL_PATH: str = os.getenv("MODEL_PATH", "module1_parking_detection/model.h5")
    SLOT_POSITIONS_PATH: str = os.getenv("SLOT_POSITIONS_PATH", "module1_parking_detection/slot_positions.pkl")
    DETECTION_CONFIDENCE: float = float(os.getenv("DETECTION_CONFIDENCE", "0.7"))
    TOTAL_SLOTS: int = int(os.getenv("TOTAL_SLOTS", "50"))

    # ─── ANPR ────────────────────────────────────────────────────────────────
    ANPR_MODEL_PATH: str = os.getenv("ANPR_MODEL_PATH", "module2_anpr/")
    OCR_LANGUAGES: list = ["en"]
    PLATE_MIN_CONFIDENCE: float = float(os.getenv("PLATE_MIN_CONFIDENCE", "0.6"))

    # ─── Fee Calculation ─────────────────────────────────────────────────────
    BASE_RATE_PER_HOUR: float = float(os.getenv("BASE_RATE_PER_HOUR", "30.0"))
    ADDITIONAL_HOUR_RATE: float = float(os.getenv("ADDITIONAL_HOUR_RATE", "20.0"))
    OVERNIGHT_FLAT_RATE: float = float(os.getenv("OVERNIGHT_FLAT_RATE", "200.0"))
    HANDICAP_DISCOUNT: float = float(os.getenv("HANDICAP_DISCOUNT", "0.5"))
    EV_DISCOUNT: float = float(os.getenv("EV_DISCOUNT", "0.10"))

    # ─── EV Charging ─────────────────────────────────────────────────────────
    EV_TYPE1_RATE: float = float(os.getenv("EV_TYPE1_RATE", "8.0"))    # Rs/kWh
    EV_TYPE2_RATE: float = float(os.getenv("EV_TYPE2_RATE", "12.0"))
    EV_CCS2_RATE: float = float(os.getenv("EV_CCS2_RATE", "18.0"))
    EV_TOTAL_CHARGERS: int = int(os.getenv("EV_TOTAL_CHARGERS", "10"))

    # ─── Surveillance ────────────────────────────────────────────────────────
    LOITERING_THRESHOLD_SECONDS: int = int(os.getenv("LOITERING_THRESHOLD_SECONDS", "120"))
    RESTRICTED_ZONES: list = []   # List of polygon coordinates
    CLIPS_SAVE_PATH: str = os.getenv("CLIPS_SAVE_PATH", "module3_surveillance/saved_clips/")

    # ─── QR Code ─────────────────────────────────────────────────────────────
    QR_EXPIRY_MINUTES: int = int(os.getenv("QR_EXPIRY_MINUTES", "15"))
    QR_SECRET: str = os.getenv("QR_SECRET", "qr-secret-key")

    # ─── Dynamic Pricing ─────────────────────────────────────────────────────
    PRICING_UPDATE_INTERVAL_SECONDS: int = int(os.getenv("PRICING_UPDATE_INTERVAL_SECONDS", "300"))
    MIN_PRICE_CAP: float = float(os.getenv("MIN_PRICE_CAP", "20.0"))
    MAX_PRICE_CAP: float = float(os.getenv("MAX_PRICE_CAP", "100.0"))

    # ─── CO2 Calculation ─────────────────────────────────────────────────────
    CO2_PER_KM_GRAMS: float = float(os.getenv("CO2_PER_KM_GRAMS", "120.0"))
    AVG_SEARCH_DISTANCE_KM: float = float(os.getenv("AVG_SEARCH_DISTANCE_KM", "4.0"))
    WITH_PARKPILOT_DISTANCE_KM: float = float(os.getenv("WITH_PARKPILOT_DISTANCE_KM", "0.2"))

    # ─── Notifications ───────────────────────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    FCM_SERVER_KEY: str = os.getenv("FCM_SERVER_KEY", "")
    EMAIL_SMTP_HOST: str = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
    EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    EMAIL_USERNAME: str = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")

    # ─── External APIs ───────────────────────────────────────────────────────
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
    WEATHER_API_URL: str = "https://api.openweathermap.org/data/2.5/weather"
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")

    # ─── Voice Assistant ─────────────────────────────────────────────────────
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "base")
    TTS_LANGUAGE: str = os.getenv("TTS_LANGUAGE", "en")
    SUPPORTED_LANGUAGES: list = ["en", "hi"]

    # ─── LSTM Prediction ─────────────────────────────────────────────────────
    LSTM_MODEL_PATH: str = os.getenv("LSTM_MODEL_PATH", "module7_demand_prediction/lstm_model.h5")
    PREDICTION_HORIZON_HOURS: int = int(os.getenv("PREDICTION_HORIZON_HOURS", "24"))
    RETRAIN_INTERVAL_DAYS: int = int(os.getenv("RETRAIN_INTERVAL_DAYS", "30"))

    # ─── Navigation ──────────────────────────────────────────────────────────
    BLE_SCAN_INTERVAL_SECONDS: int = int(os.getenv("BLE_SCAN_INTERVAL_SECONDS", "5"))
    NAV_ACCURACY_CM: int = 50
    INDOOR_MAP_PATH: str = os.getenv("INDOOR_MAP_PATH", "module9_navigation/maps/")

    # ─── Flask Dashboard ─────────────────────────────────────────────────────
    FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))

    # ─── Logging ─────────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/parkpilot.log")


settings = Config()
