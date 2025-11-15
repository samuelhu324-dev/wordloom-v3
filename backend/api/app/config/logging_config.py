"""
Logging configuration

Provides:
- setup_logging: Configure logging at application startup
- get_logger: Get logger instance
"""

import logging
from .setting import get_settings


def setup_logging():
    """
    Configure application logging

    Features:
    - Configurable log level from settings
    - Standard Python logging format
    - JSON output ready for production

    Should be called at application startup (main.py)
    """
    settings = get_settings()

    # Configure basic logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format=log_format,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance by name

    Args:
        name: Logger name (typically __name__)

    Returns:
        logging.Logger: Configured logger
    """
    return logging.getLogger(name)
