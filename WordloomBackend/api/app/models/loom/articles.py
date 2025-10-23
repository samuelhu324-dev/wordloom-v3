from sqlalchemy import Column, Integer, String, ForeignKey
from app.models.core import Base

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
