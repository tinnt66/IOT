"""
Configuration Module for REST API
Loads settings from environment variables
"""

import os
from pathlib import Path
from dataclasses import dataclass

from dotenv import load_dotenv


_ROOT_DIR = Path(__file__).resolve().parents[2]
_ENV_FILE = _ROOT_DIR / ".env"
load_dotenv(_ENV_FILE, override=False)


def _get_str(key: str, default: str) -> str:
    value = os.getenv(key)
    return default if value is None else value


def _get_int(key: str, default: int) -> int:
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value.strip())
    except Exception:
        return default


def _get_bool(key: str, default: bool) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables (.env optional)."""

    # API Configuration
    api_title: str = _get_str("API_TITLE", "IoT Sensor Data API")
    api_version: str = _get_str("API_VERSION", "2.0.0")
    api_description: str = _get_str("API_DESCRIPTION", "REST API for receiving sensor data from IoT devices")

    # Security
    api_key: str = _get_str("API_KEY", "iotserver")

    # Server Configuration
    api_host: str = _get_str("API_HOST", "127.0.0.1")
    api_port: int = _get_int("API_PORT", 8080)
    api_reload: bool = _get_bool("API_RELOAD", False)

    # Database (relative to project root)
    db_path: str = _get_str("DB_PATH", "checkpoint/sensors.db")

    # CORS - String value from .env (use * for all origins)
    allow_origins: str = _get_str("ALLOW_ORIGINS", "*")

    # Application
    log_level: str = _get_str("LOG_LEVEL", "INFO")
    timezone: str = _get_str("TIMEZONE", "Asia/Ho_Chi_Minh")



# Global settings instance
settings = Settings()
