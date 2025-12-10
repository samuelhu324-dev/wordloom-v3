"""
Orbit Mermaid Diagram API Routes

包含：
- POST /orbit/notes/{note_id}/generate-diagram - 生成 Mermaid 结构图
"""

from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database_orbit import get_orbit_db
from app.models.orbit.notes import OrbitNote
from app.services.mermaid_service import mermaid_generator

router = APIRouter(prefix="/orbit", tags=["Orbit-Diagrams"])

# ============================================================================
# Schemas
# ============================================================================

class DiagramRequest(BaseModel):
    """生成图表请求"""
    chart_type: Optional[str] = "auto"  # auto, flowchart, mindmap, timeline, stateDiagram


class DiagramResponse(BaseModel):
    """生成图表响应"""
    mermaid_code: str
    status: str = "success"

    class Config:
        from_attributes = True


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/notes/{note_id}/generate-diagram", response_model=DiagramResponse)
async def generate_diagram(
    note_id: str,
    payload: DiagramRequest,
    db: Session = Depends(get_orbit_db),
):
    """
    AI 生成 Note 的 Mermaid 结构图

    参数:
    - chart_type: 图表类型
      - auto: 自动选择（推荐）
      - flowchart: 流程图
      - mindmap: 思维导图
      - timeline: 时间轴
      - stateDiagram: 状态图

    返回:
    - mermaid_code: Mermaid 代码
    """

    # 检查是否有 API Key
    if not mermaid_generator:
        raise HTTPException(
            status_code=503,
            detail="Mermaid generation service not available. Please configure ANTHROPIC_API_KEY."
        )

    # 获取 Note
    note = db.get(OrbitNote, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # 调用生成服务
    try:
        mermaid_code = await mermaid_generator.generate_mermaid(
            title=note.title,
            content=note.content_md or "",
            chart_type=payload.chart_type
        )

        return DiagramResponse(
            mermaid_code=mermaid_code,
            status="success"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating diagram: {str(e)}"
        )
