"""Compatibility shim for historical imports.

New modules live in ``infra.database.models.base`` but many older files still
import ``infra.database.base``. This module simply re-exports ``Base`` so those
imports continue to work without touching every caller.
"""

from .models.base import Base

__all__ = ["Base"]
