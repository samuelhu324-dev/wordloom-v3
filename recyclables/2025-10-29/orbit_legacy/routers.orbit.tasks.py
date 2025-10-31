from fastapi import APIRouter
router = APIRouter(prefix="/orbit/tasks", tags=["Orbit.Legacy"])
@router.get("/health")
def health(): return {"router": "orbit.tasks", "ok": True}