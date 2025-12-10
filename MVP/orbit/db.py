from __future__ import annotations
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

ENGINE_URL = "sqlite:///orbit.db"

engine = create_engine(ENGINE_URL, echo=False, future=True)
# 关键修复：expire_on_commit=False，避免提交后对象过期导致 DetachedInstanceError
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
