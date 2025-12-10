"""
Shared fixtures for config layer tests.
"""

import pytest
from unittest.mock import Mock, patch
# from config.settings import Settings  # Will be imported by pytest


@pytest.fixture
def mock_settings():
    """Mock settings object for testing."""
    settings = Mock(spec=Settings)
    settings.ENV = "test"
    settings.DEBUG = True
    settings.LOG_LEVEL = "DEBUG"
    settings.DATABASE_URL = "postgresql://test:test@localhost/test_wordloom"
    settings.REDIS_URL = "redis://localhost:6379/1"
    settings.SECRET_KEY = "test-secret-key"
    settings.ALGORITHM = "HS256"
    settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    settings.CORS_ORIGINS = ["http://localhost:3000"]
    return settings


@pytest.fixture
def mock_db_config():
    """Mock database configuration."""
    return {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "echo": False,
    }


@pytest.fixture
def mock_logging_config():
    """Mock logging configuration."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            }
        },
        "handlers": {
            "default": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "standard",
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["default"]
        }
    }

