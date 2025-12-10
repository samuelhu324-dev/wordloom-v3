"""Chronicle Module - 事件时间线系统 (最小可用版)

目的 (Plan40 / ADR-093 草稿要点):
---------------------------------
Chronicle 仅负责记录**离散领域事件**，不做聚合统计字段；统计与汇总在读侧或后续投影表完成。
最小业务单元：Book；Block 事件可附带 block_id；不在事件里直接写 Bookshelf/Library 聚合值。

首批事件类型 (ChronicleEventType):
  - BOOK_CREATED (跨域事件总线)
  - BLOCK_STATUS_CHANGED (跨域事件总线)
  - BOOK_OPENED (直接 API 记录 - 点击/查看次数)
  - (预留) FOCUS_STARTED / FOCUS_ENDED (专注时段，后续实现)

核心设计原则:
  1. 写侧极简：单表 chronicle_events + 通用 payload(JSON)。
  2. 读侧聚合：Bookshelf/Library 时间/次数统计通过 join books/blocks → group by。
  3. 可演进性：后续添加投影/汇总表 (book_stats) 不破坏已有事件结构。
  4. 解耦：跨域事件通过 event_bus handler 转写为 ChronicleEvent，不直接耦合其它聚合仓储。

导出内容: 领域模型、枚举、服务、异常与 Pydantic DTO。
"""

from .domain.event_types import ChronicleEventType
from .domain.models import ChronicleEvent
from .application.services import ChronicleRecorderService, ChronicleQueryService
from .schemas import ChronicleEventRead, ChronicleBookOpenedRequest
from .exceptions import ChronicleException

__all__ = [
    "ChronicleEventType",
    "ChronicleEvent",
    "ChronicleRecorderService",
    "ChronicleQueryService",
    "ChronicleEventRead",
    "ChronicleBookOpenedRequest",
    "ChronicleException",
]
