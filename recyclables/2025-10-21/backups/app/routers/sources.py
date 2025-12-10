# sources.py —— 无破坏式微调版
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Source, Article
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/sources", tags=["sources"])

@router.get("/", response_model=list[str])
def list_sources(db: Session = Depends(get_db)):
    """返回所有来源名（按字母序）"""
    sources = db.query(Source).order_by(Source.name.asc()).all()
    return [s.name for s in sources]

@router.patch("/rename")
def rename_source(old: str, new: str, db: Session = Depends(get_db)):
    """
    改名或合并来源：
    - 若新名不存在：直接改名；
    - 若新名已存在：合并引用后删除旧名；
    - 不再修改 Article.title。
    """
    src_old = db.query(Source).filter_by(name=old).first()
    if not src_old:
        raise HTTPException(status_code=404, detail=f"Source '{old}' not found")

    src_new = db.query(Source).filter_by(name=new).first()

    try:
        if src_new:
            # ✅ 合并逻辑
            # 将旧来源下的文章、条目全部指向新来源
            db.query(Article).filter(Article.source_id == src_old.id).update(
                {"source_id": src_new.id}
            )
            db.execute(
                "UPDATE entry_sources SET source_id = :new_id WHERE source_id = :old_id",
                {"new_id": src_new.id, "old_id": src_old.id},
            )
            db.delete(src_old)
            db.commit()
            return {"status": "merged", "from": old, "to": new}
        else:
            # ✅ 改名逻辑
            src_old.name = new
            db.commit()
            return {"status": "renamed", "from": old, "to": new}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Source name '{new}' already exists")
