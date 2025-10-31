# app/routers/orbit/stats.py
# Orbit 模块 - 统计信息接口（当前返回占位数据）

from fastapi import APIRouter
router = APIRouter(tags=["Orbit:Stats"])

@router.get("/stats")
def get_stats():
    return {"status": "ok", "message": "Orbit stats endpoint placeholder"}
