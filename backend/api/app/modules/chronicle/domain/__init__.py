"""Chronicle Domain Package

包含：
  - 事件类型枚举 ChronicleEventType
  - 领域对象 ChronicleEvent (不可变，创建后只读)
  - 仓储端口 ChronicleRepositoryPort 在 repository_port.py 中定义
"""

from .event_types import ChronicleEventType
from .models import ChronicleEvent
from .repository_port import ChronicleRepositoryPort

__all__ = ["ChronicleEventType", "ChronicleEvent", "ChronicleRepositoryPort"]
