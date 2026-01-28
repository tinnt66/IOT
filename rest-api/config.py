"""
Configuration Module for REST API
Loads settings from environment variables
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    api_title: str = "IoT Sensor Data API"
    api_version: str = "2.0.0"
    api_description: str = "REST API for receiving sensor data from IoT devices"
    
    # Security
    api_key: str = "iotserver"  # Default, should be overridden in .env
    
    # Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False
    
    # Database (relative to project root)
    db_path: str = "sensors.db"
    
    # CORS - String value from .env (use * for all origins)
    allow_origins: str = "*"
    
    # Application
    log_level: str = "INFO"
    timezone: str = "Asia/Ho_Chi_Minh"
    
    class Config:
        # Point to root .env file
        env_file = str(Path(__file__).parent.parent / ".env")
        env_file_encoding = "utf-8"



# Global settings instance
settings = Settings()

