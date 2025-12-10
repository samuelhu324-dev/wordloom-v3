# app/routers/orbit_stats.py  (fixed import path)
from __future__ import annotations
from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database import get_db
from app.models_orbit import Task

router = APIRouter(tags=["Orbit:Stats"])

class SeriesPoint(BaseModel):
  date: date
  created: int = 0
  completed: int = 0

@router.get("/stats/tasks/completions", response_model=List[SeriesPoint])
def get_task_series(
    range: Optional[str] = Query(None, description="7d|30d|custom"),
    start: Optional[date] = None,
    end: Optional[date] = None,
    db: Session = Depends(get_db),
):
    if range in {"7d", "30d"}:
        days = 7 if range == "7d" else 30
        end_dt = datetime.utcnow().date()
        start_dt = end_dt - timedelta(days=days - 1)
    else:
        end_dt = end or datetime.utcnow().date()
        start_dt = start or (end_dt - timedelta(days=6))

    Created = (
        db.execute(
            select(func.date(Task.created_at), func.count())
            .where(func.date(Task.created_at) >= start_dt)
            .where(func.date(Task.created_at) <= end_dt)
            .group_by(func.date(Task.created_at))
        ).all()
    )
    created_map = {d: c for d, c in Created}

    Completed = (
        db.execute(
            select(func.date(Task.completed_at), func.count())
            .where(Task.completed_at.isnot(None))
            .where(func.date(Task.completed_at) >= start_dt)
            .where(func.date(Task.completed_at) <= end_dt)
            .group_by(func.date(Task.completed_at))
        ).all()
    )
    completed_map = {d: c for d, c in Completed}

    series: List[SeriesPoint] = []
    cur = start_dt
    while cur <= end_dt:
        series.append(SeriesPoint(date=cur, created=int(created_map.get(cur, 0)), completed=int(completed_map.get(cur, 0))))
        cur = cur + timedelta(days=1)
    return series
