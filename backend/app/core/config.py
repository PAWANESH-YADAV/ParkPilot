from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    PROJECT_NAME: str = "ParkPilot"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./parkpilot.db"
    )

    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "parkpilot-secret-key-2024-change-in-production-please"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_TOPIC: str = "parkpilot/sensors"

    STRIPE_SECRET_KEY: str = "sk_test_your_stripe_key_here"
    STRIPE_PUBLISHABLE_KEY: str = "pk_test_your_stripe_key_here"

    AI_SERVICE_URL: str = "http://localhost:8001"

    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]


settings = Settings()
