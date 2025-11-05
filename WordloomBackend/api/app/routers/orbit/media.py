"""
Media Resource 的 API 端点 - 统一的媒体管理接口
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pathlib import Path
import hashlib
import shutil
from uuid import UUID
from datetime import datetime

from app.database_orbit import get_orbit_db, ORBIT_UPLOAD_DIR
from app.models.orbit.media import OrbitMediaResource, MediaEntityType
from app.schemas.orbit.media import (
    MediaResourceCreate,
    MediaResourceUpdate,
    MediaResourceResponse,
    MediaResourceReorderRequest,
)

router = APIRouter(prefix="/orbit", tags=["orbit-media"])


# ============================================================================
# 工具函数
# ============================================================================

def calculate_file_hash(file_content: bytes) -> str:
    """计算文件的 SHA256 哈希"""
    return hashlib.sha256(file_content).hexdigest()


def get_media_directory(workspace_id: str, entity_type: str, entity_id: str) -> Path:
    """获取媒体资源的存储目录"""
    return Path(ORBIT_UPLOAD_DIR) / "media" / "workspaces" / entity_type / entity_id


def parse_entity_type(entity_type_str: str) -> MediaEntityType:
    """
    从字符串解析 MediaEntityType 枚举
    支持大小写不敏感的匹配
    """
    for member in MediaEntityType:
        if member.value == entity_type_str.lower():
            return member
    raise ValueError(f"Invalid entity_type: {entity_type_str}")


# ============================================================================
# 上传端点
# ============================================================================

@router.post("/media/upload", response_model=MediaResourceResponse)
async def upload_media(
    file: UploadFile = File(...),
    workspace_id: str = Query(...),
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    display_order: int = Query(default=0),
    db: Session = Depends(get_orbit_db),
):
    """
    上传媒体资源到任何实体

    Args:
        file: 上传的文件
        workspace_id: 工作区 ID
        entity_type: 实体类型 (bookshelf_cover, note_cover, checkpoint_marker, image_block, etc)
        entity_id: 实体 ID
        display_order: 显示顺序

    Returns:
        MediaResourceResponse
    """
    print(f"[MEDIA_UPLOAD] 收到上传请求: file={file.filename}, entity_type={entity_type}, entity_id={entity_id}, workspace_id={workspace_id}")

    if not file.filename:
        raise HTTPException(status_code=400, detail="missing filename")

    try:
        workspace_uuid = UUID(workspace_id)
        entity_uuid = UUID(entity_id)
        print(f"[MEDIA_UPLOAD] UUID 解析成功")
    except ValueError as e:
        print(f"[MEDIA_UPLOAD] UUID 解析失败: {e}")
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # 验证 entity_type
    try:
        entity_type_enum = parse_entity_type(entity_type)
        print(f"[MEDIA_UPLOAD] entity_type 匹配成功: {entity_type_enum}")
    except ValueError as e:
        print(f"[MEDIA_UPLOAD] entity_type 匹配失败: {entity_type}, 错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # 验证文件类型
    ext = Path(file.filename).suffix.lower() or ".bin"
    if ext not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".mp4", ".webm"}:
        raise HTTPException(status_code=400, detail=f"unsupported file type: {ext}")

    try:
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        print(f"[MEDIA_UPLOAD] 文件读取成功: 大小={file_size}")

        # 计算哈希值（防止重复上传）
        file_hash = calculate_file_hash(file_content)
        print(f"[MEDIA_UPLOAD] 文件 hash 计算成功: {file_hash[:16]}...")

        # 检查是否已经存在相同文件（对于当前实体）
        existing = db.query(OrbitMediaResource).filter(
            OrbitMediaResource.file_hash == file_hash,
            OrbitMediaResource.entity_id == entity_uuid,
            OrbitMediaResource.deleted_at.is_(None)
        ).first()

        if existing:
            print(f"[MEDIA_UPLOAD] 文件已存在，跳过重复上传: {existing.id}")
            return MediaResourceResponse.from_orm(existing)

        # 检查是否存在相同 hash 的文件（来自其他实体）
        # 如果存在，复用物理文件但创建新的 media 记录
        existing_shared = db.query(OrbitMediaResource).filter(
            OrbitMediaResource.file_hash == file_hash,
            OrbitMediaResource.deleted_at.is_(None)
        ).first()

        if existing_shared:
            print(f"[MEDIA_UPLOAD] 文件已在其他地方存在，复用物理文件但创建新记录: {existing_shared.id}")
            # 使用相同的 file_path（指向相同的物理文件）
            relative_path = existing_shared.file_path
        else:
            # 创建目录
            media_dir = get_media_directory(str(workspace_uuid), entity_type_enum.value, str(entity_uuid))
            print(f"[MEDIA_UPLOAD] 创建目录: {media_dir}")
            media_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名（包含哈希前缀以避免碰撞）
            file_name = f"{file_hash[:8]}{ext}"
            file_path = media_dir / file_name
            print(f"[MEDIA_UPLOAD] 保存文件位置: {file_path}")

            # 写入文件
            file_path.write_bytes(file_content)
            print(f"[MEDIA_UPLOAD] 文件保存成功")

            # 相对路径用于数据库存储
            relative_path = f"/media/workspaces/{entity_type_enum.value}/{entity_uuid}/{file_name}"
            print(f"[MEDIA_UPLOAD] 相对路径: {relative_path}")

        # 保存到数据库
        media_resource = OrbitMediaResource(
            workspace_id=workspace_uuid,
            entity_type=entity_type_enum,
            entity_id=entity_uuid,
            file_name=file.filename,
            file_path=relative_path,
            file_size=file_size,
            mime_type=file.content_type,
            file_hash=file_hash,
            display_order=display_order,
            is_thumbnail=False,
        )

        db.add(media_resource)
        db.commit()
        db.refresh(media_resource)

        print(f"[MEDIA_UPLOAD] ✅ 上传成功: media_id={media_resource.id}")

        return MediaResourceResponse.from_orm(media_resource)

    except Exception as e:
        db.rollback()
        print(f"[MEDIA_UPLOAD] ❌ 上传失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ============================================================================
# 获取端点
# ============================================================================

@router.get("/media", response_model=list[MediaResourceResponse])
async def get_media_by_entity(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    db: Session = Depends(get_orbit_db),
):
    """
    获取某个实体的所有媒体资源

    Args:
        entity_type: 实体类型
        entity_id: 实体 ID

    Returns:
        List[MediaResourceResponse]
    """
    try:
        entity_uuid = UUID(entity_id)
        entity_type_enum = parse_entity_type(entity_type)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    media_resources = db.query(OrbitMediaResource).filter(
        OrbitMediaResource.entity_type == entity_type_enum,
        OrbitMediaResource.entity_id == entity_uuid,
        OrbitMediaResource.deleted_at.is_(None)
    ).order_by(OrbitMediaResource.display_order).all()

    return [MediaResourceResponse.from_orm(m) for m in media_resources]


@router.get("/media/{media_id}", response_model=MediaResourceResponse)
async def get_media(
    media_id: str,
    db: Session = Depends(get_orbit_db),
):
    """获取单个媒体资源"""
    try:
        media_uuid = UUID(media_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid media_id format")

    media_resource = db.query(OrbitMediaResource).filter(
        OrbitMediaResource.id == media_uuid,
        OrbitMediaResource.deleted_at.is_(None)
    ).first()

    if not media_resource:
        raise HTTPException(status_code=404, detail="Media resource not found")

    return MediaResourceResponse.from_orm(media_resource)


# ============================================================================
# 删除端点（软删除）
# ============================================================================

@router.delete("/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    media_id: str,
    db: Session = Depends(get_orbit_db),
):
    """
    删除媒体资源（软删除）

    Args:
        media_id: 媒体资源 ID
    """
    try:
        media_uuid = UUID(media_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid media_id format")

    media_resource = db.query(OrbitMediaResource).filter(
        OrbitMediaResource.id == media_uuid
    ).first()

    if not media_resource:
        raise HTTPException(status_code=404, detail="Media resource not found")

    # 软删除
    media_resource.deleted_at = datetime.utcnow()
    db.commit()

    # TODO: 异步任务清理物理文件


# ============================================================================
# 排序端点
# ============================================================================

@router.put("/media/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_media(
    payload: MediaResourceReorderRequest,
    db: Session = Depends(get_orbit_db),
):
    """
    重新排列媒体资源的顺序

    Args:
        payload: 包含 entity_id, entity_type, order (UUID列表)
    """
    try:
        entity_uuid = UUID(str(payload.entity_id))
        entity_type_enum = parse_entity_type(payload.entity_type)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 获取所有媒体资源
    media_resources = db.query(OrbitMediaResource).filter(
        OrbitMediaResource.entity_type == entity_type_enum,
        OrbitMediaResource.entity_id == entity_uuid,
        OrbitMediaResource.deleted_at.is_(None)
    ).all()

    # 验证数量匹配
    if len(media_resources) != len(payload.order):
        raise HTTPException(status_code=400, detail="Order list size mismatch")

    # 更新排序
    media_by_id = {m.id: m for m in media_resources}

    for new_order, media_id in enumerate(payload.order):
        if media_id not in media_by_id:
            raise HTTPException(status_code=400, detail=f"Media resource not found: {media_id}")
        media_by_id[media_id].display_order = new_order

    db.commit()
