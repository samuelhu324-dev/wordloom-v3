"""Base classes for DDD"""

from uuid import UUID
from datetime import datetime
from typing import Any, Dict
from pydantic import BaseModel

# ============================================
# Domain Base Classes
# ============================================

class DomainObject(BaseModel):
    """所有 Domain Objects 的基类"""

    class Config:
        arbitrary_types_allowed = True


class Entity(DomainObject):
    """有身份的对象（有 ID）"""
    id: UUID


class AggregateRoot(Entity):
    """聚合根基类"""
    created_at: datetime
    updated_at: datetime


class ValueObject(DomainObject):
    """值对象基类（无 ID，通过值比较）"""

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(tuple(self.__dict__.values()))


# ============================================
# Domain Events
# ============================================

class DomainEvent(DomainObject):
    """Domain Event 基类"""
    aggregate_id: UUID
    occurred_at: datetime = datetime.now()
    event_version: int = 1


# ============================================
# Repository 接口（Week 2 才用）
# ============================================

class Repository:
    """Repository 基类"""
    pass