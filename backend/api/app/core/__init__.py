"""
Core Module - Database, security, and common utilities
"""

from .database import Base
from .security import get_current_user_id

__all__ = ["Base", "get_current_user_id"]
