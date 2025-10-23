# app/models/loom/entries.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from app.models.core import Base

class Entry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, index=True)
    # 翻译文本：源/目标
    src_text = Column(Text, nullable=False)
    tgt_text = Column(Text, nullable=False)
    # 语言（默认中→英，与历史一致）
    lang_src = Column(String(16), default="zh")
    lang_tgt = Column(String(16), default="en")
    # 文章归属与段落位置（可空，用于 From Page/文章内插入）
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=True)
    position = Column(Integer, nullable=True)
    # 时间戳（用于搜索排序/区间过滤）
    created_at = Column(DateTime, nullable=True)

    # 常用查询加速
    __table_args__ = (
        Index("ix_entries_created_at", "created_at"),
        Index("ix_entries_lang_pair", "lang_src", "lang_tgt"),
    )

    def __repr__(self) -> str:
        return f"<Entry id={self.id} ls={self.lang_src} lt={self.lang_tgt}>"
