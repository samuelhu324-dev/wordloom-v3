"""
SQLAlchemy Base Model - Declarative Base

Centralized location for SQLAlchemy's declarative base.
This avoids circular imports when models import Base.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

__all__ = ["Base"]
