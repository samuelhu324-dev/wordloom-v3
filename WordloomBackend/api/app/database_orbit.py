from __future__ import annotations
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

ORBIT_DB_URL = os.getenv("ORBIT_DB_URL") or "postgresql+psycopg2://postgres:pgpass@127.0.0.1:5433/wordloomorbit"

engine_orbit = create_engine(ORBIT_DB_URL, future=True, pool_pre_ping=True)
SessionOrbit = sessionmaker(bind=engine_orbit, autoflush=False, autocommit=False)

OrbitBase = declarative_base()

def get_orbit_db():
    db = SessionOrbit()
    try:
        yield db
    finally:
        db.close()

ORBIT_UPLOAD_DIR = os.getenv("ORBIT_UPLOAD_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "storage", "orbit_uploads")
)

def ensure_orbit_dirs():
    Path(ORBIT_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

def ensure_orbit_extensions():
    with engine_orbit.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))

def ensure_orbit_tables():
    # 导入所有模型以确保它们被正确注册
    from app.models.orbit.notes import OrbitNote  # noqa: F401
    from app.models.orbit.tags import OrbitTag, OrbitNoteTag  # noqa: F401
    from app.models.orbit.bookshelves import OrbitBookshelf  # noqa: F401

    # 创建所有表
    OrbitBase.metadata.create_all(bind=engine_orbit)

    # 保障新增列（无 Alembic 的情况下）
    with engine_orbit.begin() as conn:
        # PostgreSQL 正确语法：ALTER TABLE <name> ADD COLUMN IF NOT EXISTS
        conn.execute(text("""
            ALTER TABLE orbit_notes
            ADD COLUMN IF NOT EXISTS urgency integer NOT NULL DEFAULT 3;
        """))
        conn.execute(text("""
            ALTER TABLE orbit_notes
            ADD COLUMN IF NOT EXISTS usage_level integer NOT NULL DEFAULT 3;
        """))
        conn.execute(text("""
            ALTER TABLE orbit_notes
            ADD COLUMN IF NOT EXISTS usage_count integer NOT NULL DEFAULT 0;
        """))
        conn.execute(text("""
            ALTER TABLE orbit_notes
            ADD COLUMN IF NOT EXISTS bookshelf_id uuid REFERENCES orbit_bookshelves(id) ON DELETE SET NULL;
        """))
        # orbit_tags: icon 列（Lucide 图标名）
        conn.execute(text("""
            ALTER TABLE orbit_tags
            ADD COLUMN IF NOT EXISTS icon text NULL;
        """))
    print("[Orbit] Tables ensured: orbit_notes (+ urgency, usage_level, usage_count, bookshelf_id)")
    print("[Orbit] Tables ensured: orbit_bookshelves (new)")
    print("[Orbit] Tags system initialized: orbit_tags, orbit_note_tags (+ icon)")

    # 初始化默认标签（20 个），仅在数据库中不存在任何标签时写入
    try:
        from app.models.orbit.tags import OrbitTag  # noqa: WPS433
        with SessionOrbit() as db:
            existing = db.query(OrbitTag).count()
            if existing == 0:
                default_tags = [
                    {"name": "Feature", "icon": "Zap", "color": "#3B82F6"},
                    {"name": "Bug", "icon": "Bug", "color": "#EF4444"},
                    {"name": "Enhancement", "icon": "TrendingUp", "color": "#22C55E"},
                    {"name": "In Progress", "icon": "Clock", "color": "#F97316"},
                    {"name": "Done", "icon": "CheckCircle2", "color": "#8B5CF6"},
                    {"name": "Documentation", "icon": "BookOpen", "color": "#06B6D4"},
                    {"name": "Reference", "icon": "Link2", "color": "#EC4899"},
                    {"name": "Note", "icon": "FileText", "color": "#6366F1"},
                    {"name": "Code", "icon": "Code2", "color": "#14B8A6"},
                    {"name": "Tutorial", "icon": "Lightbulb", "color": "#FBBF24"},
                    {"name": "Critical", "icon": "AlertTriangle", "color": "#DC2626"},
                    {"name": "Important", "icon": "Star", "color": "#F59E0B"},
                    {"name": "Nice-to-have", "icon": "Smile", "color": "#10B981"},
                    {"name": "On Hold", "icon": "Pause", "color": "#6B7280"},
                    {"name": "Urgent", "icon": "Flame", "color": "#FF4444"},
                    {"name": "Performance", "icon": "Zap", "color": "#7C3AED"},
                    {"name": "Design", "icon": "Palette", "color": "#A855F7"},
                    {"name": "Testing", "icon": "CheckCircle", "color": "#059669"},
                    {"name": "Security", "icon": "Lock", "color": "#DC2626"},
                    {"name": "Research", "icon": "Compass", "color": "#3B82F6"},
                ]
                for t in default_tags:
                    db.execute(text(
                        "INSERT INTO orbit_tags (name, color, icon) VALUES (:name, :color, :icon) ON CONFLICT (name) DO NOTHING"
                    ), t)
                db.commit()
                print("[Orbit] Seeded 20 default tags (name, color, icon)")
    except Exception as seed_err:  # pragma: no cover - 不影响主流程
        print(f"[Orbit] Default tags seeding skipped: {seed_err}")
