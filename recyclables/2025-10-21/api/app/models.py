# app/models.py
from sqlalchemy import (
    Column, Integer, Text, String, DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Entry(Base):
    __tablename__ = "entries"
    id = Column(Integer, primary_key=True)
    src_text = Column(Text, nullable=False)
    tgt_text = Column(Text, nullable=False)
    lang_src = Column(String(8), default="zh")
    lang_tgt = Column(String(8), default="en")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 篇章定位
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=True, index=True)
    position   = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint("article_id", "position", name="uq_article_position"),
    )

class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    url  = Column(String(1024))

class EntrySource(Base):
    __tablename__ = "entry_sources"
    entry_id  = Column(Integer, ForeignKey("entries.id"), primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"), primary_key=True)

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), unique=True, nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

# 组合索引
Index("idx_entries_text", Entry.src_text, Entry.tgt_text)
