"""
Environment and application settings

Loads configuration from environment variables (.env file)
Provides centralized access to all application settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application configuration from environment variables"""

    # Database - default to local PostgreSQL on port 5432
    database_url: str = "postgresql://postgres:pgpass@localhost:5432/wordloom"

    # API
    api_title: str = "Wordloom API"
    api_version: str = "3.0.0"

    # Debug & Environment
    debug: bool = False
    environment: str = "development"

    # CORS
    cors_origins: list = ["*"]

    # JWT Security (预留)
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Storage
    storage_backend: str = "local"  # local | s3
    storage_path: str = "./storage"

    # Logging
    log_level: str = "INFO"

    # Development flags
    allow_dev_library_owner_override: bool = True

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance

    Returns:
        Settings: Application settings singleton
    """
    return Settings()
