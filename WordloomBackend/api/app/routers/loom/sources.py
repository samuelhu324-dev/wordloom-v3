from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.loom.sources import Source      # ← common 改为 loom
from app.models.loom.articles import Article    # ← common 改为 loom

router = APIRouter(prefix="/sources", tags=["sources"])

@router.get("/", response_model=list[str])
def list_sources(db: Session = Depends(get_db)):
    sources = db.query(Source).order_by(Source.name.asc()).all()
    return [s.name for s in sources]

@router.patch("/rename")
def rename_source(old: str, new: str, db: Session = Depends(get_db)):
    """重命名或合并来源"""
    src_old = db.query(Source).filter_by(name=old).first()
    if not src_old:
        raise HTTPException(status_code=404, detail=f"Source '{old}' not found")

    src_new = db.query(Source).filter_by(name=new).first()

    try:
        if src_new:
            db.query(Article).filter(Article.source_id == src_old.id).update(
                { "source_id": src_new.id }
            )
            db.execute(
                "UPDATE entry_sources SET source_id = :new_id WHERE source_id = :old_id",
                {"new_id": src_new.id, "old_id": src_old.id},
            )
            db.delete(src_old)
            db.commit()
            return {"status": "merged", "from": old, "to": new}
        else:
            src_old.name = new
            db.commit()
            return {"status": "renamed", "from": old, "to": new}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Source name '{new}' already exists")
