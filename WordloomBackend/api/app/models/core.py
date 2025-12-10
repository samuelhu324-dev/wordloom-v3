# app/models/core.py
# 统一模型基类与 metadata，作为所有模型的根基

from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData

# 元数据对象（用于统一管理表结构）
metadata = MetaData()

# 声明式基类
Base = declarative_base(metadata=metadata)
