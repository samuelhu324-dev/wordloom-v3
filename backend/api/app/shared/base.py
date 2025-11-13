"""Base classes for DDD"""

from uuid import UUID
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass

# ============================================
# Domain Base Classes
# ============================================

class DomainObject:
    """所有 Domain Objects 的基类"""
    pass


class Entity(DomainObject):
    """有身份的对象（有 ID）"""
    def __init__(self):
        self.id: Optional[UUID] = None


class AggregateRoot(Entity):
    """聚合根基类"""
    def __init__(self):
        super().__init__()
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
        self.events: list = []

    @property
    def domain_events(self) -> list:
        """Alias for events (backward compatibility)"""
        return self.events

    def emit(self, event):
        """Emit a domain event"""
        if not hasattr(self, 'events') or self.events is None:
            self.events = []
        self.events.append(event)


@dataclass(frozen=True)
class ValueObject(DomainObject):
    """值对象基类（无 ID，通过值比较）"""

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self):
        try:
            return hash(tuple(sorted(self.__dict__.items())))
        except TypeError:
            # 如果有不可哈希的值，使用 id
            return id(self)


# ============================================
# Domain Events
# ============================================

class DomainEvent(DomainObject):
    """Domain Event 基类"""
    pass


# ============================================
# Repository 接口（Week 2 才用）
# ============================================

class Repository:
    """Repository 基类"""
    pass