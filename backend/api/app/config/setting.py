"""
Environment and application settings

Loads configuration from environment variables (.env file)
Provides centralized access to all application settings
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application configuration from environment variables"""

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/wordloom_v3"
    )

    # API
    api_title: str = "Wordloom API"
    api_version: str = "3.0.0"

    # Debug & Environment
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "development")

    # CORS
    cors_origins: list = ["*"]

    # JWT Security (预留)
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Storage
    storage_backend: str = os.getenv("STORAGE_BACKEND", "local")  # local | s3
    storage_path: str = os.getenv("STORAGE_PATH", "./storage")

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance

    Returns:
        Settings: Application settings singleton
    """
    return Settings()
