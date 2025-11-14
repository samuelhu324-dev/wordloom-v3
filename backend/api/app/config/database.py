"""
Core Database Module - SQLAlchemy ORM Setup

Provides Base declarative class for all ORM models.
"""

from sqlalchemy.orm import declarative_base

# Declarative base for all ORM models
Base = declarative_base()
