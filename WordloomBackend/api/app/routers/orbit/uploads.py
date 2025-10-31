# app/routers/orbit/uploads.py
from __future__ import annotations
from uuid import uuid4
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from app.database_orbit import ORBIT_UPLOAD_DIR
from app.core.image_manager import ImageManager

# 初始化图片管理器
image_manager = ImageManager(ORBIT_UPLOAD_DIR)

router = APIRouter(prefix="/orbit", tags=["Orbit-Uploads"])


@router.post("/uploads")
async def upload_image(file: UploadFile = File(...), note_id: str = Query(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="missing filename")
    if not note_id:
        raise HTTPException(status_code=400, detail="missing note_id")
    ext = Path(file.filename).suffix.lower() or ".bin"
    if ext not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
        raise HTTPException(status_code=400, detail=f"unsupported file type: {ext}")

    # 确保 note_id 对应的文件夹存在（如果不存在则创建）
    note_dir = image_manager.create_note_folder(note_id)

    name = f"{uuid4().hex}{ext}"
    dest = note_dir / name
    dest.write_bytes(await file.read())

    # 返回相对路径：/uploads/{noteId}/{filename}
    return {"url": f"/uploads/{note_id}/{name}"}


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
    查询 note 的图片信息

    Args:
        note_id: note 的 ID
        content_md: note 的 markdown 内容（可选，用于分析哪些图片被引用）

    Returns:
        包含所有图片、被引用图片、未被引用图片的信息
    """
    if not note_id:
        raise HTTPException(status_code=400, detail="missing note_id")

    # 获取文件夹中所有存在的文件
    note_folder = Path(ORBIT_UPLOAD_DIR) / note_id
    all_images = []
    if note_folder.exists():
        try:
            all_images = [f.name for f in note_folder.iterdir() if f.is_file()]
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
