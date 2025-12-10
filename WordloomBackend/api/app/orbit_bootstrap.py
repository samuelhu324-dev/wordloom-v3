from sqlalchemy import text
from app.database_orbit import engine_orbit, ensure_orbit_extensions, ensure_orbit_dirs
from app.models.orbit.notes import OrbitBase  # 导入以注册元数据

DROP_OLD = [
    "activity",
    "bookmarks",
    "memos",
]

def reset_orbit_schema():
    ensure_orbit_extensions()
    ensure_orbit_dirs()
    with engine_orbit.begin() as conn:
        # 先尝试删除旧表（忽略不存在）
        for t in DROP_OLD:
            conn.execute(text(f"DROP TABLE IF EXISTS {t} CASCADE;"))
        # 删除本次新表（幂等重置）
        for t in ["attachments", "bookmarks", "note_links", "note_tags", "tags", "notes"]:
            conn.execute(text(f"DROP TABLE IF EXISTS {t} CASCADE;"))
    # 用 ORM 一次性建表与索引
    OrbitBase.metadata.create_all(engine_orbit)

if __name__ == "__main__":
    reset_orbit_schema()
    print("Orbit schema reset OK.")