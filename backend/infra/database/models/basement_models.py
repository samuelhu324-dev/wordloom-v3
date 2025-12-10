"""SQLAlchemy model for basement_entries table."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from infra.database.base import Base


class BasementEntryModel(Base):
    """ORM model for basement_entries table.

    Stores a snapshot of each book when it enters the Basement,
    enabling fast queries without scanning the books table.
    """

    __tablename__ = "basement_entries"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    book_id = Column(PG_UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    library_id = Column(PG_UUID(as_uuid=True), ForeignKey("libraries.id", ondelete="CASCADE"), nullable=False, index=True)
    bookshelf_id = Column(PG_UUID(as_uuid=True), ForeignKey("bookshelves.id", ondelete="SET NULL"), nullable=True)
    previous_bookshelf_id = Column(PG_UUID(as_uuid=True), nullable=True, comment="Last active bookshelf before Basement")

    title_snapshot = Column(String(255), nullable=False)
    summary_snapshot = Column(Text, nullable=True)
    status_snapshot = Column(String(50), nullable=False)
    block_count_snapshot = Column(Integer, nullable=False, default=0)

    moved_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<BasementEntryModel(id={self.id}, book_id={self.book_id}, title={self.title_snapshot})>"
