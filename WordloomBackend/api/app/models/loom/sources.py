# app/models/loom/sources.py
from sqlalchemy import Column, Integer, String, UniqueConstraint
from app.models.core import Base

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    # 兼容旧 repo 的 _ensure_source(source_name, source_url)
    url = Column(String(1024), nullable=True)

    __table_args__ = (
        UniqueConstraint("name", name="uq_sources_name"),
    )

    def __repr__(self) -> str:
        return f"<Source id={self.id} name='{self.name}'>"
