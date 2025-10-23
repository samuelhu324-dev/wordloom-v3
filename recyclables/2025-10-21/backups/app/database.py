# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 自动加载 .env（避免只依赖系统环境变量）
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# 统一默认：没配环境变量也走 PG（避免又回到 sqlite）
DEFAULT_URL = "postgresql+psycopg2://postgres:pgpass@localhost:5444/wordloom"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_URL)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
