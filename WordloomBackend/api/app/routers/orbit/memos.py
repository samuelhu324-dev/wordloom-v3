# app/routers/orbit/memos.py
# Orbit 模块 - 备忘录接口

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from app.database import get_db
from app.models.orbit.memos import Memo

router = APIRouter(tags=["Orbit:Memos"])

class MemoIn(BaseModel):
    text: str
    tags: Optional[str] = None

class MemoOut(MemoIn):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

@router.get("/memos", response_model=List[MemoOut])
def list_memos(db: Session = Depends(get_db)):
    return db.query(Memo).order_by(Memo.created_at.desc()).all()

@router.post("/memos", response_model=MemoOut)
def create_memo(payload: MemoIn, db: Session = Depends(get_db)):
    memo = Memo(text=payload.text, tags=payload.tags, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    db.add(memo); db.commit(); db.refresh(memo)
    return memo
