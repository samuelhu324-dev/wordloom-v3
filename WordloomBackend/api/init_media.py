#!/usr/bin/env python
"""
初始化统一媒体管理系统
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from app.database_orbit import engine_orbit, SessionOrbit, OrbitBase
from app.models.orbit.media import OrbitMediaResource

def init_media_system():
    """初始化媒体管理系统"""
    print("[Init] Starting media resources system initialization...")

    try:
        # 创建表
        print("[Init] Creating media resources table...")
        OrbitBase.metadata.create_all(bind=engine_orbit)
        print("[Init] ✓ Table created: media_resources")

        # 添加必要的列到其他表
        with engine_orbit.begin() as conn:
            print("[Init] Adding columns to existing tables...")

            # checkpoint_markers: image_urls (如果还没有)
            conn.execute(text("""
                ALTER TABLE orbit_note_checkpoint_markers
                ADD COLUMN IF NOT EXISTS image_urls JSONB DEFAULT '[]'::jsonb;
            """))
            print("[Init] ✓ Added image_urls to orbit_note_checkpoint_markers")

            # notes: cover_image_id (如果还没有)
            conn.execute(text("""
                ALTER TABLE orbit_notes
                ADD COLUMN IF NOT EXISTS cover_image_id UUID;
            """))
            print("[Init] ✓ Added cover_image_id to orbit_notes")

            # bookshelves: cover_image_id (如果还没有)
            conn.execute(text("""
                ALTER TABLE orbit_bookshelves
                ADD COLUMN IF NOT EXISTS cover_image_id UUID;
            """))
            print("[Init] ✓ Added cover_image_id to orbit_bookshelves")

            # 创建索引
            print("[Init] Creating indexes...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_media_entity
                ON media_resources(entity_type, entity_id);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_media_deleted
                ON media_resources(deleted_at);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_media_created
                ON media_resources(created_at);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_media_file_hash
                ON media_resources(file_hash);
            """))
            print("[Init] ✓ Indexes created")

        print("[Init] ✓ Media resources system initialized successfully!")
        return True

    except Exception as e:
        print(f"[Init] ✗ Error initializing media system: {e}")
        return False

if __name__ == "__main__":
    success = init_media_system()
    sys.exit(0 if success else 1)
