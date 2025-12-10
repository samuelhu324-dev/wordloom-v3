# app/models/orbit/stats.py
# Orbit 模块 - 可扩展统计信息（目前占位）

from sqlalchemy import Column, Integer, String
from app.models.core import Base

class OrbitStat(Base):
    __tablename__ = "orbit_stats"
    id = Column(Integer, primary_key=True, index=True)
    metric = Column(String(100), nullable=False)
    value = Column(Integer, nullable=False, default=0)
