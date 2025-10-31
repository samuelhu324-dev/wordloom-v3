# migrate_sqlite_to_pg_orm.py - copy data from SQLite to Postgres (no Alembic)
import os, sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from app.models import Base, Entry, Source, Article  # adjust if different
import app.models_orbit as mo

pg_url = os.getenv("DATABASE_URL")
sqlite_url = os.getenv("DATABASE_URL_SQLITE", "sqlite:///app.db")
if not pg_url:
    raise SystemExit("Set DATABASE_URL (Postgres) and optionally DATABASE_URL_SQLITE (SQLite).")

src_engine = create_engine(sqlite_url, future=True)
dst_engine = create_engine(pg_url, future=True)

Src = sessionmaker(bind=src_engine)
Dst = sessionmaker(bind=dst_engine)

def copy_table(src, dst, model, name):
    rows = src.query(model).all()
    if not rows:
        print(f"[{name}] nothing to copy")
        return 0
    count = 0
    for obj in rows:
        data = {c.key: getattr(obj, c.key) for c in model.__table__.columns}
        dst.merge(model(**data))
        count += 1
    dst.commit()
    print(f"[{name}] copied {count} rows")
    return count

with Src() as ssrc, Dst() as sdst:
    total = 0
    total += copy_table(ssrc, sdst, Source, "sources")
    total += copy_table(ssrc, sdst, Article, "articles")
    total += copy_table(ssrc, sdst, Entry, "entries")
    total += copy_table(ssrc, sdst, mo.Task, "tasks")
    total += copy_table(ssrc, sdst, mo.Memo, "memos")
    total += copy_table(ssrc, sdst, mo.TaskEvent, "task_events")
print("✅ Migration done.")
