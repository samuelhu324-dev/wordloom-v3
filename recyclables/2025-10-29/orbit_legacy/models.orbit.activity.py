
from __future__ import annotations
import uuid
from sqlalchemy import Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database_orbit import OrbitBase

class Activity(OrbitBase):
    __tablename__ = "activity"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bookmark_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookmarks.id", ondelete="CASCADE"), index=True)
    action = mapped_column(Text)   # create/update/delete/status_change/tag_change
    meta = mapped_column(JSONB, nullable=True)
    ts = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
