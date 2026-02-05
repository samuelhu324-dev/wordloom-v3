"""Chronicle Models - SQLAlchemy ORM for chronicle_events 表

Schema 对齐 (Plan40 / 新设计):
  - id (UUID pk)
  - event_type (text)
  - book_id (UUID, 非空)
  - block_id (UUID, 可空)
  - actor_id (UUID, 可空)
  - payload (JSONB, 默认空对象)
  - occurred_at (timestamptz, 非空)
  - created_at (timestamptz, 默认 now())

索引策略:
  - idx chronicle_events_book_time: (book_id, occurred_at DESC)
  - idx chronicle_events_type_time: (event_type, occurred_at DESC)
  - idx chronicle_events_created_at: created_at DESC

兼容说明:
  如现有表结构存在 entity_type/entity_id/user_id 等旧字段，迁移脚本会重建至新结构。
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Integer, text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base


class ChronicleEventModel(Base):
    __tablename__ = "chronicle_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type = Column(String(64), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    block_id = Column(UUID(as_uuid=True), ForeignKey("blocks.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    payload = Column(JSONB, nullable=False, server_default="{}")

    # Phase C: promote durable envelope fields to columns for indexing.
    schema_version = Column(Integer, nullable=True, server_default=text("1"))
    provenance = Column(String(32), nullable=True, server_default=text("'unknown'"))
    source = Column(String(64), nullable=True, server_default=text("'unknown'"))
    actor_kind = Column(String(32), nullable=True, server_default=text("'unknown'"))
    correlation_id = Column(String(128), nullable=True)
    occurred_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


# 索引定义（DDL 由 Alembic 迁移生成，这里用于 SQLAlchemy 元数据）
Index("ix_chronicle_events_book_time", ChronicleEventModel.book_id, ChronicleEventModel.occurred_at.desc())
Index("ix_chronicle_events_type_time", ChronicleEventModel.event_type, ChronicleEventModel.occurred_at.desc())
Index("ix_chronicle_events_created", ChronicleEventModel.created_at.desc())
Index("ix_chronicle_events_correlation_id", ChronicleEventModel.correlation_id)
Index("ix_chronicle_events_source_time", ChronicleEventModel.source, ChronicleEventModel.occurred_at.desc())
