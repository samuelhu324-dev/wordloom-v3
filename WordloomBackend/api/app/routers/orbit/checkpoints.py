"""
Checkpoint 和 Marker 的 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List, Optional
import uuid
from uuid import UUID
from pathlib import Path
import shutil
import os

from app.database_orbit import get_orbit_db, ORBIT_UPLOAD_DIR
from app.models.orbit.checkpoints import OrbitNoteCheckpoint, OrbitNoteCheckpointMarker
from app.models.orbit.notes import OrbitNote
from app.schemas.orbit.checkpoints import (
    CheckpointCreate,
    CheckpointUpdate,
    CheckpointResponse,
    CheckpointMarkerCreate,
    CheckpointMarkerUpdate,
    CheckpointMarkerResponse,
    CheckpointDetailResponse,
)

router = APIRouter(prefix="/orbit", tags=["orbit-checkpoints"])


# ============================================================================
# CHECKPOINT CRUD 端点
# ============================================================================

@router.post("/checkpoints", response_model=CheckpointResponse)
async def create_checkpoint(
    note_id: str,
    payload: CheckpointCreate,
    db: Session = Depends(get_orbit_db),
):
    """创建新的检查点"""
    # 验证 note 存在
    try:
        note_uuid = UUID(note_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid note_id format")

    note = db.query(OrbitNote).filter(OrbitNote.id == note_uuid).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    checkpoint = OrbitNoteCheckpoint(
        note_id=note_uuid,
        title=payload.title,
        description=payload.description,
        status=payload.status or "pending",
        tags=payload.tags or [],
        order=payload.order or 0,
    )

    db.add(checkpoint)
    db.commit()
    db.refresh(checkpoint)

    return CheckpointResponse.from_orm(checkpoint)


@router.get("/checkpoints/{checkpoint_id}", response_model=CheckpointDetailResponse)
async def get_checkpoint(
    checkpoint_id: str,
    db: Session = Depends(get_orbit_db),
):
    """获取检查点详情（包括所有 marker）"""
    try:
        checkpoint_uuid = UUID(checkpoint_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid checkpoint_id format")

    checkpoint = db.query(OrbitNoteCheckpoint).filter(
        OrbitNoteCheckpoint.id == checkpoint_uuid
    ).first()

    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    return CheckpointDetailResponse.from_orm(checkpoint)


@router.patch("/checkpoints/{checkpoint_id}", response_model=CheckpointResponse)
async def update_checkpoint(
    checkpoint_id: str,
    payload: CheckpointUpdate,
    db: Session = Depends(get_orbit_db),
):
    """更新检查点"""
    try:
        checkpoint_uuid = UUID(checkpoint_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid checkpoint_id format")

    checkpoint = db.query(OrbitNoteCheckpoint).filter(
        OrbitNoteCheckpoint.id == checkpoint_uuid
    ).first()

    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    # 更新字段
    if payload.title is not None:
        checkpoint.title = payload.title
    if payload.description is not None:
        checkpoint.description = payload.description
    if payload.status is not None:
        checkpoint.status = payload.status
        # 自动更新时间戳
        if payload.status == "in_progress" and not checkpoint.started_at:
            checkpoint.started_at = datetime.utcnow()
        elif payload.status == "done" and not checkpoint.completed_at:
            checkpoint.completed_at = datetime.utcnow()
    if payload.tags is not None:
        checkpoint.tags = payload.tags
    if payload.order is not None:
        checkpoint.order = payload.order

    db.commit()
    db.refresh(checkpoint)

    return CheckpointResponse.from_orm(checkpoint)


@router.delete("/checkpoints/{checkpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checkpoint(
    checkpoint_id: str,
    db: Session = Depends(get_orbit_db),
):
    """删除检查点及其所有 marker，同时清理相关文件夹"""
    try:
        checkpoint_uuid = UUID(checkpoint_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid checkpoint_id format")

    checkpoint = db.query(OrbitNoteCheckpoint).filter(
        OrbitNoteCheckpoint.id == checkpoint_uuid
    ).first()

    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    # 获取 note_id 以便清理文件夹
    note_id = str(checkpoint.note_id)
    checkpoint_id_str = str(checkpoint_uuid)

    # 删除数据库记录
    db.delete(checkpoint)
    db.commit()

    # 清理文件夹：{upload_dir}/notes/{note_id}/checkpoints/{checkpoint_id}/
    checkpoint_dir = Path(ORBIT_UPLOAD_DIR) / "notes" / note_id / "checkpoints" / checkpoint_id_str
    if checkpoint_dir.exists():
        try:
            shutil.rmtree(checkpoint_dir)
            print(f"[CLEANUP] Deleted checkpoint directory: notes/{note_id}/checkpoints/{checkpoint_id_str}")
        except Exception as e:
            print(f"[ERROR] Failed to delete checkpoint directory {checkpoint_dir}: {e}")


@router.get("/checkpoints/note/{note_id}/all", response_model=List[CheckpointDetailResponse])
async def list_checkpoints_for_note(
    note_id: str,
    db: Session = Depends(get_orbit_db),
):
    """获取某个 note 的所有检查点"""
    # 验证 note 存在
    try:
        note_uuid = UUID(note_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid note_id format")

    note = db.query(OrbitNote).filter(OrbitNote.id == note_uuid).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    checkpoints = db.query(OrbitNoteCheckpoint).filter(
        OrbitNoteCheckpoint.note_id == note_uuid
    ).order_by(OrbitNoteCheckpoint.order).all()

    return [CheckpointDetailResponse.from_orm(c) for c in checkpoints]


# ============================================================================
# MARKER CRUD 端点
# ============================================================================

@router.post("/checkpoints/{checkpoint_id}/markers", response_model=CheckpointMarkerResponse)
async def create_marker(
    checkpoint_id: str,
    payload: CheckpointMarkerCreate,
    db: Session = Depends(get_orbit_db),
):
    """为检查点添加标记"""
    try:
        checkpoint_uuid = UUID(checkpoint_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid checkpoint_id format")

    checkpoint = db.query(OrbitNoteCheckpoint).filter(
        OrbitNoteCheckpoint.id == checkpoint_uuid
    ).first()

    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    # 自动分配 order：在已有 marker 的最大 order 基础上 +1
    max_order_result = db.query(func.max(OrbitNoteCheckpointMarker.order)).filter(
        OrbitNoteCheckpointMarker.checkpoint_id == checkpoint_uuid
    ).scalar()

    # 如果没有 marker，max_order_result 为 None，默认从 0 开始
    # 否则使用查询结果加 1
    if max_order_result is None:
        next_order = 0
    else:
        next_order = max_order_result + 1

    # 将 image_urls 转换为 JSONB 格式
    image_urls_data = []
    if payload.image_urls:
        image_urls_data = [{"url": img.url} for img in payload.image_urls]

    marker = OrbitNoteCheckpointMarker(
        checkpoint_id=checkpoint_uuid,
        title=payload.title,
        description=payload.description,
        started_at=payload.started_at,
        ended_at=payload.ended_at,
        category=payload.category or "work",
        tags=payload.tags or [],
        color=payload.color or "#3b82f6",
        emoji=payload.emoji or "✓",
        order=next_order,  # 使用自动分配的 order，而不是来自 payload 的值
        is_completed=payload.is_completed or False,
        image_urls=image_urls_data,  # 图片 URL 列表
    )

    db.add(marker)
    db.commit()
    db.refresh(marker)

    return CheckpointMarkerResponse.from_orm(marker)


@router.get("/checkpoints/{checkpoint_id}/markers", response_model=List[CheckpointMarkerResponse])
async def list_markers(
    checkpoint_id: str,
    db: Session = Depends(get_orbit_db),
):
    """获取检查点的所有标记"""
    try:
        checkpoint_uuid = UUID(checkpoint_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid checkpoint_id format")

    checkpoint = db.query(OrbitNoteCheckpoint).filter(
        OrbitNoteCheckpoint.id == checkpoint_uuid
    ).first()

    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    markers = db.query(OrbitNoteCheckpointMarker).filter(
        OrbitNoteCheckpointMarker.checkpoint_id == checkpoint_uuid
    ).order_by(OrbitNoteCheckpointMarker.order).all()

    return [CheckpointMarkerResponse.from_orm(m) for m in markers]


@router.patch("/checkpoints/{checkpoint_id}/markers/{marker_id}", response_model=CheckpointMarkerResponse)
async def update_marker(
    checkpoint_id: str,
    marker_id: str,
    payload: CheckpointMarkerUpdate,
    db: Session = Depends(get_orbit_db),
):
    """更新标记"""
    try:
        checkpoint_uuid = UUID(checkpoint_id)
        marker_uuid = UUID(marker_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid checkpoint_id or marker_id format")

    marker = db.query(OrbitNoteCheckpointMarker).filter(
        OrbitNoteCheckpointMarker.id == marker_uuid,
        OrbitNoteCheckpointMarker.checkpoint_id == checkpoint_uuid,
    ).first()

    if not marker:
        raise HTTPException(status_code=404, detail="Marker not found")

    if payload.title is not None:
        marker.title = payload.title
    if payload.description is not None:
        marker.description = payload.description
    if payload.started_at is not None:
        marker.started_at = payload.started_at
    if payload.ended_at is not None:
        marker.ended_at = payload.ended_at
    if payload.category is not None:
        marker.category = payload.category
    if payload.tags is not None:
        marker.tags = payload.tags
    if payload.color is not None:
        marker.color = payload.color
    if payload.emoji is not None:
        marker.emoji = payload.emoji
    if payload.order is not None:
        marker.order = payload.order
    if payload.is_completed is not None:
        marker.is_completed = payload.is_completed
    if payload.image_urls is not None:
        # 转换 image_urls 列表为字典列表格式以存储到 JSONB
        marker.image_urls = [img.dict() if hasattr(img, 'dict') else {'url': img['url']} for img in payload.image_urls] if payload.image_urls else []

    # 重新计算 duration_seconds
    if marker.started_at and marker.ended_at:
        marker.duration_seconds = int((marker.ended_at - marker.started_at).total_seconds())

    db.commit()
    db.refresh(marker)

    return CheckpointMarkerResponse.from_orm(marker)


@router.delete("/checkpoints/{checkpoint_id}/markers/{marker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_marker(
    checkpoint_id: str,
    marker_id: str,
    db: Session = Depends(get_orbit_db),
):
    """删除标记，重新排序后续的 marker，并清理相关文件夹"""
    try:
        checkpoint_uuid = UUID(checkpoint_id)
        marker_uuid = UUID(marker_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid checkpoint_id or marker_id format")

    marker = db.query(OrbitNoteCheckpointMarker).filter(
        OrbitNoteCheckpointMarker.id == marker_uuid,
        OrbitNoteCheckpointMarker.checkpoint_id == checkpoint_uuid,
    ).first()

    if not marker:
        raise HTTPException(status_code=404, detail="Marker not found")

    deleted_order = marker.order

    # 获取信息以便清理文件夹
    checkpoint = db.query(OrbitNoteCheckpoint).filter(
        OrbitNoteCheckpoint.id == checkpoint_uuid
    ).first()
    note_id = str(checkpoint.note_id) if checkpoint else None

    # 删除该 marker
    db.delete(marker)
    db.flush()

    # 重新排序：将所有 order > deleted_order 的 marker 的 order 减 1
    markers_to_reorder = db.query(OrbitNoteCheckpointMarker).filter(
        OrbitNoteCheckpointMarker.checkpoint_id == checkpoint_uuid,
        OrbitNoteCheckpointMarker.order > deleted_order,
    ).all()

    for m in markers_to_reorder:
        m.order = m.order - 1

    db.commit()

    # 清理文件夹：{upload_dir}/notes/{note_id}/checkpoints/{checkpoint_id}/markers/{marker_id_short}/
    # 使用 marker_id 的前 8 个字符作为目录名
    if note_id:
        marker_id_short = marker_id[:8]
        marker_dir = Path(ORBIT_UPLOAD_DIR) / "notes" / note_id / "checkpoints" / checkpoint_id / "markers" / marker_id_short
        if marker_dir.exists():
            try:
                shutil.rmtree(marker_dir)
                print(f"[CLEANUP] Deleted marker directory: notes/{note_id}/checkpoints/{checkpoint_id}/markers/{marker_id_short}")
            except Exception as e:
                print(f"[ERROR] Failed to delete marker directory {marker_dir}: {e}")


# ============================================================================
# 统计端点
# ============================================================================

@router.get("/checkpoints/{checkpoint_id}/stats")
async def get_checkpoint_stats(
    checkpoint_id: str,
    db: Session = Depends(get_orbit_db),
):
    """获取检查点的时间统计"""
    try:
        checkpoint_uuid = UUID(checkpoint_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid checkpoint_id format")

    checkpoint = db.query(OrbitNoteCheckpoint).filter(
        OrbitNoteCheckpoint.id == checkpoint_uuid
    ).first()

    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    return {
        "checkpoint_id": str(checkpoint.id),
        "duration_seconds": checkpoint.duration_seconds,
        "actual_work_seconds": checkpoint.actual_work_seconds,
        "marker_count": len(checkpoint.markers),
        "completion_percentage": checkpoint.completion_percentage,
        "status": checkpoint.status,
    }
