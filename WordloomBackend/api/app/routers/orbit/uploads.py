# app/routers/orbit/uploads.py
from __future__ import annotations
from uuid import uuid4, UUID
from pathlib import Path
import os
import shutil
import time
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database_orbit import ORBIT_UPLOAD_DIR, get_orbit_db
from app.core.image_manager import ImageManager
from app.core.storage_manager import StorageManager
from app.models.orbit.checkpoints import OrbitNoteCheckpoint, OrbitNoteCheckpointMarker
from app.models.orbit.notes import OrbitNote

# 初始化图片管理器和存储管理器
image_manager = ImageManager(ORBIT_UPLOAD_DIR)
storage_manager = StorageManager(ORBIT_UPLOAD_DIR)

# 定义临时文件上传目录
TEMP_UPLOAD_DIR = os.path.join(ORBIT_UPLOAD_DIR, "temp")
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/orbit", tags=["Orbit-Uploads"])


@router.post("/uploads")
async def upload_image(file: UploadFile = File(...), note_id: str = Query(...)):
    """
    上传图片到特定笔记（业界标准固定路径）

    业界标准路径：storage/orbit_uploads/notes/{note_id}/images/{filename}

    Args:
        file: 上传的文件
        note_id: 笔记 ID

    Returns:
        相对 URL：/uploads/{note_id}/{filename}
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="missing filename")
    if not note_id:
        raise HTTPException(status_code=400, detail="missing note_id")
    ext = Path(file.filename).suffix.lower() or ".bin"
    if ext not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
        raise HTTPException(status_code=400, detail=f"unsupported file type: {ext}")

    # 确保 note_id 对应的图片文件夹存在（固定路径：notes/{note_id}/images/）
    # create_note_folder 返回 {upload_dir}/notes/{note_id}/images/
    images_dir = image_manager.create_note_folder(note_id)

    name = f"{uuid4().hex}{ext}"
    dest = images_dir / name
    dest.write_bytes(await file.read())

    print(f"[UPLOAD] File uploaded to notes/{note_id}/images/{name}")

    # 返回相对路径：/uploads/{note_id}/{filename}
    # 前端使用这个 URL 来访问图片
    return {"url": f"/uploads/{note_id}/{name}"}


@router.post("/uploads/note/{note_id}/cover")
async def upload_note_cover_image(
    note_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_orbit_db),
):
    """
    上传笔记的封面图到本地存储并更新数据库

    路径标准：storage/orbit_uploads/notes/{note_id}/cover/cover.{ext}

    Args:
        note_id: 笔记 ID
        file: 上传的文件
        db: 数据库连接

    Returns:
        上传成功后的图片 URL：/uploads/{note_id}/cover.{ext}
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="missing filename")
        if not note_id:
            raise HTTPException(status_code=400, detail="missing note_id")

        # 规范化 note_id
        note_id = str(note_id).strip()

        print(f"[UPLOAD_COVER] Starting cover image upload for note: {note_id}")
        print(f"[UPLOAD_COVER] Filename: {file.filename}")

        # 验证笔记是否存在于数据库
        try:
            note_uuid = UUID(note_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid UUID format: {str(e)}")

        note = db.query(OrbitNote).filter(OrbitNote.id == note_uuid).first()
        if not note:
            print(f"[ERROR] Note not found in DB: {note_id}")
            raise HTTPException(status_code=404, detail=f"Note not found: {note_id}")

        print(f"[UPLOAD_COVER] ✓ Note found in DB: {note.id}")

        # 验证文件类型
        ext = Path(file.filename).suffix.lower() or ".jpg"
        if ext not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
            raise HTTPException(status_code=400, detail=f"unsupported file type: {ext}")

        # 创建覆盖图文件夹
        cover_dir = Path(ORBIT_UPLOAD_DIR) / "notes" / note_id / "cover"
        print(f"[UPLOAD_COVER] Creating directory: {cover_dir}")

        try:
            cover_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"[ERROR] Failed to create directory: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create directory: {str(e)}")

        # 清除旧的封面图（保持只有一张）
        for existing_file in cover_dir.glob("cover.*"):
            try:
                existing_file.unlink()
                print(f"[UPLOAD_COVER] Removed old cover: {existing_file.name}")
            except OSError as e:
                print(f"[WARNING] Failed to remove old cover: {str(e)}")

        # 保存新的封面图，使用固定名称 "cover"
        filename = f"cover{ext}"
        dest = cover_dir / filename

        print(f"[UPLOAD_COVER] Writing file to: {dest}")

        try:
            file_content = await file.read()
            dest.write_bytes(file_content)
            print(f"[UPLOAD_COVER] File written successfully, size: {len(file_content)} bytes")
        except OSError as e:
            print(f"[ERROR] Failed to write file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")

        # 更新数据库中的 preview_image 字段
        preview_image_url = f"/uploads/notes/{note_id}/cover/cover{ext}"
        note.preview_image = preview_image_url
        db.commit()

        print(f"[UPLOAD_COVER] ✓ Note preview_image updated in DB: {preview_image_url}")
        print(f"[UPLOAD_COVER] ✓ Cover image uploaded to notes/{note_id}/cover/{filename}")

        # 返回相对路径
        return {"url": preview_image_url}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Cover upload failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Cover upload failed: {str(e)}")


@router.post("/uploads/checkpoint-marker")
async def upload_checkpoint_marker_image(
    file: UploadFile = File(...),
    note_id: str = Query(...),
    checkpoint_id: str = Query(...),
    marker_id: str = Query(...),
    db: Session = Depends(get_orbit_db),
):
    """
    上传 marker 图片到特定 checkpoint（新路径结构）

    新的标准路径：storage/orbit_uploads/notes/{note_id}/checkpoints/{checkpoint_id}/markers/{marker_id}/images/{marker_id}_{filename}

    Args:
        file: 上传的文件
        note_id: 笔记 ID
        checkpoint_id: checkpoint ID
        marker_id: marker ID

    Returns:
        相对 URL：/uploads/checkpoints/{note_id}/{checkpoint_id}/{marker_id}/{filename}
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="missing filename")
        if not note_id or not checkpoint_id or not marker_id:
            raise HTTPException(status_code=400, detail="missing note_id, checkpoint_id, or marker_id")

        # 规范化 ID（去除多余的空格）
        note_id = str(note_id).strip()
        checkpoint_id = str(checkpoint_id).strip()
        marker_id = str(marker_id).strip()

        print(f"[UPLOAD] Checkpoint marker upload started:")
        print(f"  note_id: '{note_id}'")
        print(f"  checkpoint_id: '{checkpoint_id}'")
        print(f"  marker_id: '{marker_id}'")
        print(f"  filename: {file.filename}")
        print(f"  ORBIT_UPLOAD_DIR: {ORBIT_UPLOAD_DIR}")

        # ✅ 验证 IDs 是否存在于数据库
        try:
            checkpoint_uuid = UUID(checkpoint_id)
            marker_uuid = UUID(marker_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid UUID format: {str(e)}")

        # 检查 checkpoint 是否存在
        checkpoint = db.query(OrbitNoteCheckpoint).filter(
            OrbitNoteCheckpoint.id == checkpoint_uuid
        ).first()

        if not checkpoint:
            print(f"[ERROR] Checkpoint not found in DB: {checkpoint_id}")
            raise HTTPException(status_code=404, detail=f"Checkpoint not found: {checkpoint_id}")

        print(f"[UPLOAD] ✓ Checkpoint found in DB: {checkpoint.id}")

        # 检查 marker 是否存在
        marker = db.query(OrbitNoteCheckpointMarker).filter(
            OrbitNoteCheckpointMarker.id == marker_uuid,
            OrbitNoteCheckpointMarker.checkpoint_id == checkpoint_uuid
        ).first()

        if not marker:
            print(f"[ERROR] Marker not found in DB: {marker_id}")
            raise HTTPException(status_code=404, detail=f"Marker not found: {marker_id}")

        print(f"[UPLOAD] ✓ Marker found in DB: {marker.id}")

        ext = Path(file.filename).suffix.lower() or ".bin"
        if ext not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
            raise HTTPException(status_code=400, detail=f"unsupported file type: {ext}")

        # 创建 marker 图片目录路径
        # 原路径太长，Windows 有 260 字符限制
        # 改用更简洁的路径：notes/{note_id}/checkpoints/{checkpoint_id}/markers/{marker_id_short}/images/
        # 其中 marker_id_short 是 marker_id 的前 8 个字符

        marker_id_short = marker_id[:8]
        marker_images_dir = Path(ORBIT_UPLOAD_DIR) / "notes" / note_id / "checkpoints" / checkpoint_id / "markers" / marker_id_short / "images"

        print(f"[UPLOAD] Creating directory: {marker_images_dir}")
        print(f"[UPLOAD] Directory path length: {len(str(marker_images_dir))}")

        try:
            marker_images_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"[ERROR] Failed to create directory: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create directory: {str(e)}")

        print(f"[UPLOAD] Directory created successfully")

        # 文件命名：{marker_id_short}_{uuid}{ext}
        name = f"{marker_id_short}_{uuid4().hex}{ext}"
        dest = marker_images_dir / name

        print(f"[UPLOAD] Writing file to: {dest}")
        print(f"[UPLOAD] File path length: {len(str(dest))}")

        # 检查文件路径长度
        if len(str(dest)) >= 260:
            print(f"[WARNING] Path length {len(str(dest))} is near Windows MAX_PATH limit (260)")

        try:
            file_content = await file.read()
            dest.write_bytes(file_content)
        except OSError as e:
            print(f"[ERROR] Failed to write file: {str(e)}")
            print(f"[ERROR] Destination path: {dest}")
            print(f"[ERROR] Path exists: {dest.parent.exists()}")
            print(f"[ERROR] Parent dir: {dest.parent}")
            raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")

        print(f"[UPLOAD] File written successfully, size: {len(file_content)} bytes")

        print(f"[UPLOAD] Marker image uploaded to notes/{note_id}/checkpoints/{checkpoint_id}/markers/{marker_id_short}/images/{name}")

        # 返回相对路径
        return {"url": f"/uploads/checkpoints/{note_id}/{checkpoint_id}/{marker_id_short}/{name}"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Upload failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/bookshelf-cover")
async def upload_bookshelf_cover(file: UploadFile = File(...), bookshelf_id: str = Query(...)):
    """
    上传书橱封面图（业界标准固定路径）

    业界标准路径：storage/orbit_uploads/bookshelves/{bookshelf_id}/cover.{ext}

    Args:
        file: 上传的文件
        bookshelf_id: 书橱 ID

    Returns:
        相对 URL：/uploads/bookshelf/{bookshelf_id}/cover.{ext}
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="missing filename")
    if not bookshelf_id:
        raise HTTPException(status_code=400, detail="missing bookshelf_id")

    ext = Path(file.filename).suffix.lower() or ".jpg"
    if ext not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
        raise HTTPException(status_code=400, detail=f"unsupported file type: {ext}")

    # 创建书橱存储目录
    bookshelf_dir = storage_manager.get_bookshelf_cover_path(bookshelf_id)

    # 清除旧的封面图（保持只有一张封面图）
    for existing_file in bookshelf_dir.glob("cover.*"):
        existing_file.unlink()
        print(f"[UPLOAD] Removed old cover: {existing_file.name}")

    # 保存新的封面图，使用固定名称 "cover"
    filename = f"cover{ext}"
    dest = bookshelf_dir / filename
    dest.write_bytes(await file.read())

    print(f"[UPLOAD] Bookshelf cover uploaded to bookshelves/{bookshelf_id}/{filename}")

    # 返回相对路径，带上时间戳强制浏览器刷新缓存
    # URL格式：/uploads/bookshelf/{bookshelf_id}/cover.{ext}?t={timestamp}
    import time
    timestamp = int(time.time() * 1000)  # 毫秒级时间戳
    return {"url": f"/uploads/bookshelf/{bookshelf_id}/{filename}?t={timestamp}"}


@router.post("/cleanup-images")
def cleanup_images(note_id: str = Query(...), content_md: str = Query("")):
    """
    清理 note 中未被引用的图片

    Args:
        note_id: note 的 ID
        content_md: note 的 markdown 内容（用于检测被引用的图片）

    Returns:
        被删除的图片文件列表
    """
    if not note_id:
        raise HTTPException(status_code=400, detail="missing note_id")

    deleted_files = image_manager.cleanup_unused_images(note_id, content_md or "")
    return {
        "note_id": note_id,
        "deleted_count": len(deleted_files),
        "deleted_files": deleted_files
    }


@router.get("/images/{note_id}")
def get_note_images(note_id: str, content_md: str = Query("", description="note 的 markdown 内容")):
    """
    查询笔记的图片信息（业界标准固定路径）

    业界标准路径：storage/orbit_uploads/notes/{note_id}/images/

    Args:
        note_id: note 的 ID
        content_md: note 的 markdown 内容（可选，用于分析哪些图片被引用）

    Returns:
        包含所有图片、被引用图片、未被引用图片的信息
    """
    if not note_id:
        raise HTTPException(status_code=400, detail="missing note_id")

    # 获取文件夹中所有存在的文件（固定路径：notes/{note_id}/images/）
    images_folder = Path(ORBIT_UPLOAD_DIR) / "notes" / note_id / "images"
    all_images = []
    if images_folder.exists():
        try:
            all_images = [f.name for f in images_folder.iterdir() if f.is_file()]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"读取图片文件夹失败: {e}")

    # 获取被引用的图片
    referenced_images = image_manager.extract_referenced_images(content_md or "")

    # 计算未被引用的图片
    unreferenced_images = set(all_images) - referenced_images

    return {
        "note_id": note_id,
        "total_images": len(all_images),
        "all_images": sorted(all_images),
        "referenced_count": len(referenced_images),
        "referenced_images": sorted(referenced_images),
        "unreferenced_count": len(unreferenced_images),
        "unreferenced_images": sorted(unreferenced_images)
    }


@router.delete("/uploads/checkpoint-marker/{marker_id}/image")
async def delete_checkpoint_marker_image(
    marker_id: str,
    db: Session = Depends(get_orbit_db),
):
    """
    删除 marker 的图片并清除数据库中的 image_url 字段

    Args:
        marker_id: marker 的 ID
        db: 数据库连接

    Returns:
        删除成功信息
    """
    try:
        # 规范化 marker ID
        marker_id = str(marker_id).strip()

        print(f"[DELETE_IMAGE] Starting deletion for marker: {marker_id}")

        # 验证 marker UUID 格式
        try:
            marker_uuid = UUID(marker_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid UUID format: {str(e)}")

        # 查询 marker
        marker = db.query(OrbitNoteCheckpointMarker).filter(
            OrbitNoteCheckpointMarker.id == marker_uuid
        ).first()

        if not marker:
            print(f"[ERROR] Marker not found in DB: {marker_id}")
            raise HTTPException(status_code=404, detail=f"Marker not found: {marker_id}")

        print(f"[DELETE_IMAGE] ✓ Marker found: {marker.id}")

        # 获取 marker 的图片 URL
        if not marker.image_url:
            print(f"[DELETE_IMAGE] No image_url found for marker: {marker_id}")
            raise HTTPException(status_code=404, detail="No image found for this marker")

        print(f"[DELETE_IMAGE] Image URL: {marker.image_url}")

        # 从 URL 提取文件路径
        # URL 格式: /uploads/checkpoints/{note_id}/{checkpoint_id}/{marker_id_short}/{filename}
        # 需要找到对应的文件并删除
        image_url = marker.image_url

        # 解析 URL 提取路径部分
        if image_url.startswith('/uploads/checkpoints/'):
            # 移除前缀并分解路径
            url_path = image_url.replace('/uploads/checkpoints/', '')
            path_parts = url_path.split('/')

            if len(path_parts) >= 4:
                note_id = path_parts[0]
                checkpoint_id = path_parts[1]
                marker_id_short = path_parts[2]
                filename = path_parts[3]

                # 构建完整的文件路径
                marker_images_dir = Path(ORBIT_UPLOAD_DIR) / "notes" / note_id / "checkpoints" / checkpoint_id / "markers" / marker_id_short / "images"
                file_path = marker_images_dir / filename

                print(f"[DELETE_IMAGE] File path to delete: {file_path}")

                # 删除文件
                if file_path.exists():
                    try:
                        file_path.unlink()
                        print(f"[DELETE_IMAGE] ✓ File deleted: {file_path}")
                    except OSError as e:
                        print(f"[ERROR] Failed to delete file: {str(e)}")
                        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
                else:
                    print(f"[WARNING] File not found on disk: {file_path}")

        # 清除数据库中的 image_url 和 image_display_width
        marker.image_url = None
        marker.image_display_width = 150  # 重置为默认宽度
        db.commit()

        print(f"[DELETE_IMAGE] ✓ Database updated for marker: {marker_id}")

        return {
            "success": True,
            "message": "Image deleted successfully",
            "marker_id": marker_id
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Delete image failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Delete image failed: {str(e)}")


# ==================== 临时文件上传端点 ====================
# 业界标准做法：先上传到临时目录，保存笔记后再 finalize

@router.post("/uploads/temp")
async def upload_temp_image(file: UploadFile = File(...)):
    """
    上传图片到临时目录（无需 note_id）

    业界标准流程：
    1. 用户上传图片 → 存储在 temp/ 目录 → 返回临时 URL
    2. 用户在编辑器中看到图片（立即显示）
    3. 用户保存笔记 → 调用 finalize 端点 → 文件移动到永久目录

    路径：storage/orbit_uploads/temp/{temp_id}.{ext}

    Args:
        file: 上传的文件

    Returns:
        {
            "url": "/uploads/temp/{temp_id}.ext",
            "temp_id": "{temp_id}",
            "size": file_size
        }
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="missing filename")

        ext = Path(file.filename).suffix.lower() or ".bin"
        if ext not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
            raise HTTPException(status_code=400, detail=f"unsupported file type: {ext}")

        # 生成唯一的临时文件名
        temp_id = uuid4().hex
        temp_filename = f"{temp_id}{ext}"
        temp_path = os.path.join(TEMP_UPLOAD_DIR, temp_filename)

        # 读取文件内容并保存
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        file_size = len(content)
        print(f"[TEMP_UPLOAD] ✓ File uploaded to temp: {temp_filename} ({file_size} bytes)")

        return {
            "url": f"/uploads/temp/{temp_filename}",
            "temp_id": temp_id,
            "size": file_size
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Temp file upload failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/uploads/finalize")
async def finalize_temp_images(
    note_id: str = Query(...),
    temp_urls: list[str] = Query(...),
    db: Session = Depends(get_orbit_db),
):
    """
    将临时图片文件移动到最终位置（在笔记保存后调用）

    业界标准流程的第二步：
    1. 用户保存笔记成功
    2. 调用此端点：传递 note_id 和 temp_urls 列表
    3. 服务器将 temp/ 中的文件移动到 notes/{note_id}/images/
    4. 返回旧URL→新URL的映射，前端更新图片块

    Args:
        note_id: 笔记 ID (UUID)
        temp_urls: 临时 URL 列表，例如 ["/uploads/temp/abc123.jpg", ...]
        db: 数据库连接

    Returns:
        {
            "status": "success",
            "finalized": {
                "/uploads/temp/abc123.jpg": "/uploads/{note_id}/image1.jpg",
                ...
            }
        }
    """
    try:
        if not note_id or not temp_urls:
            raise HTTPException(status_code=400, detail="missing note_id or temp_urls")

        # 验证笔记是否存在
        try:
            note_uuid = UUID(note_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid UUID format: {str(e)}")

        note = db.query(OrbitNote).filter(OrbitNote.id == note_uuid).first()
        if not note:
            raise HTTPException(status_code=404, detail=f"Note not found: {note_id}")

        print(f"[FINALIZE] Processing {len(temp_urls)} temp files for note: {note_id}")

        # 创建目标目录
        target_dir = image_manager.create_note_folder(note_id)

        finalized_map = {}

        # 逐个处理临时文件
        for temp_url in temp_urls:
            try:
                # 从 URL 中提取临时文件名
                # 例如：/uploads/temp/abc123def.jpg → abc123def.jpg
                if not temp_url.startswith("/uploads/temp/"):
                    print(f"[WARNING] Invalid temp URL format: {temp_url}")
                    continue

                temp_filename = temp_url.replace("/uploads/temp/", "")
                temp_path = os.path.join(TEMP_UPLOAD_DIR, temp_filename)

                if not os.path.exists(temp_path):
                    print(f"[WARNING] Temp file not found: {temp_path}")
                    continue

                # 移动文件到目标目录
                # 使用时间戳和随机字符串生成新文件名以避免冲突
                _, ext = os.path.splitext(temp_filename)
                final_filename = f"{uuid4().hex}{ext}"
                final_path = os.path.join(str(target_dir), final_filename)

                shutil.move(temp_path, final_path)
                final_url = f"/uploads/{note_id}/{final_filename}"
                finalized_map[temp_url] = final_url

                print(f"[FINALIZE] ✓ Moved {temp_filename} → {final_filename}")

            except Exception as e:
                print(f"[ERROR] Failed to finalize {temp_url}: {str(e)}")
                import traceback
                traceback.print_exc()

        print(f"[FINALIZE] ✓ Completed: {len(finalized_map)} files finalized")

        return {
            "status": "success",
            "finalized": finalized_map
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Finalize failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Finalize failed: {str(e)}")


@router.delete("/uploads/temp/cleanup")
async def cleanup_old_temp_files(hours: int = Query(24)):
    """
    清理旧的临时文件（超过指定小时数）

    业界标准：定期清理孤立的临时文件，防止存储空间浪费

    Args:
        hours: 保留多少小时内的临时文件（默认 24 小时）

    Returns:
        {
            "status": "success",
            "deleted": 5,
            "freed_bytes": 1024000
        }
    """
    try:
        if hours < 1:
            raise HTTPException(status_code=400, detail="hours must be >= 1")

        current_time = time.time()
        threshold_time = current_time - (hours * 3600)

        deleted_count = 0
        freed_bytes = 0

        if not os.path.exists(TEMP_UPLOAD_DIR):
            return {
                "status": "success",
                "deleted": 0,
                "freed_bytes": 0
            }

        print(f"[CLEANUP] Starting cleanup of temp files older than {hours} hours")

        for filename in os.listdir(TEMP_UPLOAD_DIR):
            file_path = os.path.join(TEMP_UPLOAD_DIR, filename)

            # 只处理文件，跳过目录
            if not os.path.isfile(file_path):
                continue

            file_time = os.path.getmtime(file_path)

            # 如果文件修改时间早于阈值，删除它
            if file_time < threshold_time:
                try:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted_count += 1
                    freed_bytes += file_size
                    print(f"[CLEANUP] ✓ Deleted: {filename} ({file_size} bytes)")
                except OSError as e:
                    print(f"[WARNING] Failed to delete {filename}: {str(e)}")

        print(f"[CLEANUP] ✓ Completed: Deleted {deleted_count} files, freed {freed_bytes} bytes")

        return {
            "status": "success",
            "deleted": deleted_count,
            "freed_bytes": freed_bytes
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Cleanup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


