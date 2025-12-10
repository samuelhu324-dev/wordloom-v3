# app/models/loom/entry_sources.py
from sqlalchemy import Column, Integer, ForeignKey
from app.models.core import Base

class EntrySource(Base):
    __tablename__ = "entry_sources"

    # 复合主键：一条 entry 绑定一个来源（也允许后续扩展为多来源）
    entry_id  = Column(Integer, ForeignKey("entries.id"), primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"), primary_key=True)

    def __repr__(self) -> str:
        return f"<EntrySource entry_id={self.entry_id} source_id={self.source_id}>"
