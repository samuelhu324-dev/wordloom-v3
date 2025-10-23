# models.py — Streamlit 过渡版 ORM（与 app.db 表结构一致）
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import os

from sqlalchemy import (
    Column, Integer, Text, String, DateTime, ForeignKey, UniqueConstraint, Index, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

# ---------- ORM 模型（严格按你 app.db 的 .schema） ----------
class Entry(Base):
    __tablename__ = "entries"
    id         = Column(Integer, primary_key=True)
    src_text   = Column(Text, nullable=False)
    tgt_text   = Column(Text, nullable=False)
    lang_src   = Column(String(8))
    lang_tgt   = Column(String(8))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # From_Page 用到的篇章定位
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=True, index=True)
    position   = Column(Integer, nullable=True)

    __table_args__ = (
        # 你前端库有 entries 索引：idx_entries_text, idx_entries_created_at
        Index("idx_entries_text", "src_text", "tgt_text"),
        Index("idx_entries_created_at", "created_at"),
    )

class Source(Base):
    __tablename__ = "sources"
    id   = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url  = Column(String(1024))
    __table_args__ = (UniqueConstraint("name", name="uq_sources_name"),)

class EntrySource(Base):
    __tablename__ = "entry_sources"
    entry_id  = Column(Integer, ForeignKey("entries.id"), primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"), primary_key=True)

class Article(Base):
    __tablename__ = "articles"
    id         = Column(Integer, primary_key=True)
    title      = Column(String(255), nullable=False)
    source_id  = Column(Integer, ForeignKey("sources.id"))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_articles_created_at", "created_at"),
    )

# ---------- DB 连接（过渡：仍直连 app.db） ----------
def _resolve_sqlite_url() -> str:
    """
    优先 .env 中的 WL_SQLITE_PATH，其次 STREAMLIT_DB；
    再否则：在当前/父目录及 storage/ 下寻找 app.db；都没有则在当前目录创建。
    """
    from pathlib import Path
    import os

    wl_path = os.getenv("WL_SQLITE_PATH")
    if wl_path:
        p = Path(wl_path).expanduser().resolve()
        return f"sqlite:///{p.as_posix()}"

    env_path = os.getenv("STREAMLIT_DB")
    if env_path:
        p = Path(env_path).expanduser().resolve()
        return f"sqlite:///{p.as_posix()}"

    cwd = Path.cwd()
    candidates = [cwd / "app.db", cwd.parent / "app.db", cwd / "storage" / "app.db"]
    for p in candidates:
        if p.exists():
            return f"sqlite:///{p.as_posix()}"
    return f"sqlite:///{(cwd / 'app.db').as_posix()}"


DATABASE_URL = _resolve_sqlite_url()

engine = create_engine(
    DATABASE_URL,
    future=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)

def init_db() -> None:
    """过渡期：确保本地有这些表（与 app.db 一致）。"""
    Base.metadata.create_all(bind=engine)
