#!/usr/bin/env python
"""
迁移旧的 checkpoint marker 图片到新的统一媒体系统

旧系统：checkpoint_markers.image_urls (JSONB 数组)
新系统：media_resources 表

执行方式：
  python migrate_checkpoint_images.py
"""
import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from app.database_orbit import engine_orbit, SessionOrbit
from app.models.orbit.media import OrbitMediaResource, MediaEntityType
from app.models.orbit.checkpoints import OrbitNoteCheckpointMarker

def calculate_file_hash(file_path: str) -> str:
    """计算文件的 SHA256 哈希"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        print(f"[ERROR] Failed to read file {file_path}: {e}")
        return hashlib.sha256(f"error_{file_path}".encode()).hexdigest()

def migrate_checkpoint_images():
    """迁移 checkpoint marker 的图片到新系统"""
    print("[Migration] Starting checkpoint image migration...")

    try:
        with SessionOrbit() as db:
            # 查询所有有 image_urls 的 checkpoint markers
            markers_with_images = db.query(OrbitNoteCheckpointMarker).filter(
                OrbitNoteCheckpointMarker.image_urls.isnot(None)
            ).all()

            if not markers_with_images:
                print("[Migration] No checkpoint markers with images found. Migration skipped.")
                return True

            migrated_count = 0
            skipped_count = 0

            for marker in markers_with_images:
                # image_urls 是 JSONB 数组，格式: [{"url": "..."}, {"url": "..."}, ...]
                image_urls_list = marker.image_urls or []

                if not image_urls_list or len(image_urls_list) == 0:
                    print(f"[Migration] Marker {marker.id} has no image URLs. Skipping.")
                    skipped_count += 1
                    continue

                print(f"\n[Migration] Processing marker {marker.id} with {len(image_urls_list)} images...")

                # 检查该 marker 是否已在新系统中有图片
                existing = db.query(OrbitMediaResource).filter(
                    OrbitMediaResource.entity_id == marker.id,
                    OrbitMediaResource.entity_type == MediaEntityType.CHECKPOINT_MARKER,
                    OrbitMediaResource.deleted_at.is_(None)
                ).count()

                if existing > 0:
                    print(f"[Migration] Marker {marker.id} already has {existing} media in new system. Skipping.")
                    skipped_count += 1
                    continue

                # 处理每张图片
                for display_order, img_obj in enumerate(image_urls_list):
                    if not isinstance(img_obj, dict) or 'url' not in img_obj:
                        print(f"[Migration] Invalid image object format. Skipping.")
                        continue

                    image_url = img_obj['url']

                    # 尝试找到对应的物理文件
                    upload_dir = Path(os.getenv('ORBIT_UPLOAD_DIR', 'storage/orbit_uploads'))

                    # 尝试多种路径格式
                    possible_paths = [
                        upload_dir / image_url.lstrip('/'),
                        Path(image_url),
                    ]

                    file_path = None
                    for possible in possible_paths:
                        if possible.exists():
                            file_path = possible
                            break

                    if not file_path:
                        print(f"[Migration] File not found for {image_url}. Creating media record without file.")
                        # 即使文件不存在，也创建媒体记录
                        file_hash = hashlib.sha256(image_url.encode()).hexdigest()
                    else:
                        file_hash = calculate_file_hash(str(file_path))
                        print(f"[Migration] File found: {file_path}")

                    # 创建新的媒体资源
                    media = OrbitMediaResource(
                        file_name=Path(image_url).name if image_url else 'unknown',
                        file_path=image_url,  # 保存原始 URL
                        file_size=file_path.stat().st_size if file_path else 0,
                        mime_type='image/jpeg',  # 默认为 JPEG
                        file_hash=file_hash,
                        workspace_id=None,  # 如果可能，从关联的 note 获取
                        entity_type=MediaEntityType.CHECKPOINT_MARKER,
                        entity_id=marker.id,
                        display_order=display_order,
                        is_thumbnail=False,
                        created_at=marker.created_at if hasattr(marker, 'created_at') else datetime.utcnow(),
                    )

                    try:
                        db.add(media)
                        db.commit()
                        print(f"[Migration]   ✓ Migrated image {display_order + 1} for marker {marker.id}")
                        migrated_count += 1
                    except Exception as e:
                        db.rollback()
                        print(f"[Migration]   ✗ Failed to create media record: {e}")
                        skipped_count += 1

            print(f"\n[Migration] Complete!")
            print(f"[Migration] Migrated: {migrated_count}")
            print(f"[Migration] Skipped: {skipped_count}")
            return True

    except Exception as e:
        print(f"[Migration] ✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_checkpoint_images()
    sys.exit(0 if success else 1)
