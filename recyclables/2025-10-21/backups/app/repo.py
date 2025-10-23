# app/repo.py
from sqlalchemy import select, or_, delete, update, func
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
import re

from .database import SessionLocal
from .models import Entry, Source, EntrySource, Article

# ---------- helpers ----------
def _ensure_source(session, source_name: Optional[str], source_url: Optional[str] = None):
    if not source_name:
        return None
    obj = session.execute(select(Source).where(Source.name == source_name)).scalar_one_or_none()
    if not obj:
        obj = Source(name=source_name, url=source_url)
        session.add(obj)
        session.flush()
    return obj

def _link_source(session, entry_id: int, source_obj):
    session.execute(delete(EntrySource).where(EntrySource.entry_id == entry_id))
    if source_obj:
        session.add(EntrySource(entry_id=entry_id, source_id=source_obj.id))

def _next_position(session, article_id: int) -> int:
    max_pos = session.execute(select(func.max(Entry.position)).where(Entry.article_id == article_id)).scalar()
    return 1 if max_pos is None else max_pos + 1

# ---------- add / update / upsert / delete ----------
def add_entry(src: str, tgt: str, ls="zh", lt="en",
              source_name: Optional[str] = None,
              source_url: Optional[str] = None,
              created_at: Optional[str] = None) -> int:
    src = (src or "").strip(); tgt = (tgt or "").strip()
    if not src or not tgt:
        raise ValueError("src/tgt required")
    with SessionLocal() as s:
        if created_at:
            try:
                ts = datetime.fromisoformat(created_at)
            except Exception:
                raise ValueError("created_at must be ISO format string")
            e = Entry(src_text=src, tgt_text=tgt, lang_src=ls, lang_tgt=lt, created_at=ts)
        else:
            e = Entry(src_text=src, tgt_text=tgt, lang_src=ls, lang_tgt=lt)
        s.add(e); s.flush()
        src_obj = _ensure_source(s, source_name, source_url)
        _link_source(s, e.id, src_obj)
        s.commit()
        return e.id

def update_entry(entry_id: int, *, src: Optional[str] = None, tgt: Optional[str] = None,
                 ls: Optional[str] = None, lt: Optional[str] = None,
                 source_name: Optional[str] = None, source_url: Optional[str] = None,
                 created_at: Optional[str] = None) -> int:
    with SessionLocal() as s:
        e = s.get(Entry, entry_id)
        if not e:
            raise ValueError(f"entry {entry_id} not found")
        if src is not None: e.src_text = src.strip()
        if tgt is not None: e.tgt_text = tgt.strip()
        if ls  is not None: e.lang_src = ls
        if lt  is not None: e.lang_tgt = lt
        if created_at:
            try:
                e.created_at = datetime.fromisoformat(created_at)
            except Exception:
                raise ValueError("created_at must be ISO format string")
        if source_name is not None:
            src_obj = _ensure_source(s, source_name, source_url)
            _link_source(s, e.id, src_obj)
        s.commit()
        return e.id

def upsert_entry(entry_id: Optional[int], *, src: str, tgt: str,
                 ls: str = "zh", lt: str = "en",
                 source_name: Optional[str] = None, source_url: Optional[str] = None,
                 created_at: Optional[str] = None) -> int:
    if entry_id:
        return update_entry(entry_id, src=src, tgt=tgt, ls=ls, lt=lt,
                            source_name=source_name, source_url=source_url, created_at=created_at)
    return add_entry(src, tgt, ls, lt, source_name, source_url, created_at)

def delete_entry(entry_id: int) -> None:
    with SessionLocal() as s:
        e = s.get(Entry, entry_id)
        if not e:
            return
        s.execute(delete(EntrySource).where(EntrySource.entry_id == entry_id))
        s.delete(e)
        s.commit()

# ---------- article APIs ----------
def create_article(title: str, source_name: Optional[str] = None) -> int:
    if not title.strip():
        raise ValueError("title required")
    with SessionLocal() as s:
        src_obj = _ensure_source(s, source_name)
        art = Article(title=title.strip(), source_id=(src_obj.id if src_obj else None))
        s.add(art); s.commit()
        return art.id

def get_article_by_title(title: str):
    with SessionLocal() as s:
        return s.execute(select(Article).where(Article.title == title)).scalar_one_or_none()

def get_article_sentences(article_id: int):
    with SessionLocal() as s:
        stmt = (
            select(Entry.id, Entry.src_text, Entry.tgt_text, Entry.position, Entry.created_at)
            .where(Entry.article_id == article_id)
            .order_by(Entry.position.asc())
        )
        return s.execute(stmt).all()

def insert_sentence(article_id: int, after_position: int, src: str, tgt: str,
                    ls="zh", lt="en", source_name: Optional[str] = None,
                    created_at: Optional[str] = None) -> int:
    src = (src or "").strip(); tgt = (tgt or "").strip()
    if not src or not tgt:
        raise ValueError("src/tgt required")
    with SessionLocal() as s:
        s.execute(
            update(Entry)
            .where(Entry.article_id == article_id, Entry.position > after_position)
            .values(position=Entry.position + 1)
        )
        ts = datetime.fromisoformat(created_at) if created_at else datetime.utcnow()
        e = Entry(src_text=src, tgt_text=tgt, lang_src=ls, lang_tgt=lt,
                  created_at=ts, article_id=article_id, position=after_position + 1)
        s.add(e); s.flush()
        src_obj = _ensure_source(s, source_name)
        if src_obj:
            s.add(EntrySource(entry_id=e.id, source_id=src_obj.id))
        s.commit()
        return e.id

# ---------- search / find / replace ----------
def _build_pattern(keyword: str, *, regex_mode: bool, case_sensitive: bool, strict_word: bool) -> re.Pattern:
    if not keyword:
        raise ValueError("keyword required")
    pat = keyword if regex_mode else re.escape(keyword)
    if strict_word:
        pat = rf"\b(?:{pat})\b" if regex_mode else rf"\b{pat}\b"
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(pat, flags)

def find_matches(keyword: str,
                 scope: str = "both",
                 source_name: Optional[str] = None,
                 date_from: Optional[str] = None,
                 date_to: Optional[str] = None,
                 limit: int = 200,
                 regex_mode: bool = False,
                 case_sensitive: bool = False,
                 strict_word: bool = False) -> List[Tuple[int, str, str, Optional[str], datetime]]:
    key = (keyword or "").strip()
    if not key:
        return []
    with SessionLocal() as s:
        stmt = select(Entry.id, Entry.src_text, Entry.tgt_text, Source.name.label("source_name"), Entry.created_at)\
               .join(EntrySource, EntrySource.entry_id == Entry.id, isouter=True)\
               .join(Source, Source.id == EntrySource.source_id, isouter=True)
        if source_name:
            stmt = stmt.where(Source.name == source_name)
        if date_from:
            stmt = stmt.where(Entry.created_at >= datetime.fromisoformat(date_from))
        if date_to:
            stmt = stmt.where(Entry.created_at < datetime.fromisoformat(date_to) + timedelta(days=1))
        like_val = f"%{key}%"
        if scope == "src":
            stmt = stmt.where(Entry.src_text.like(like_val))
        elif scope == "tgt":
            stmt = stmt.where(Entry.tgt_text.like(like_val))
        else:
            stmt = stmt.where(or_(Entry.src_text.like(like_val), Entry.tgt_text.like(like_val)))
        stmt = stmt.order_by(Entry.created_at.desc()).limit(max(limit, 1))
        rows = s.execute(stmt).all()
    try:
        pat = _build_pattern(key, regex_mode=regex_mode or strict_word, case_sensitive=case_sensitive, strict_word=strict_word)
    except Exception:
        return []
    def hit(src: str, tgt: str) -> bool:
        if scope == "src": return bool(pat.search(src))
        if scope == "tgt": return bool(pat.search(tgt))
        return bool(pat.search(src) or pat.search(tgt))
    return [r for r in rows if hit(r[1], r[2])][:limit]

def bulk_replace(keyword: str, replacement: str,
                 scope: str = "both",
                 source_name: Optional[str] = None,
                 date_from: Optional[str] = None,
                 date_to: Optional[str] = None,
                 regex_mode: bool = False,
                 case_sensitive: bool = False,
                 strict_word: bool = False,
                 first_only: bool = False) -> int:
    key = (keyword or "").strip()
    if not key:
        raise ValueError("keyword required")
    candidates = find_matches(key, scope, source_name, date_from, date_to,
                              limit=10_000, regex_mode=regex_mode,
                              case_sensitive=case_sensitive, strict_word=strict_word)
    if not candidates:
        return 0
    pat = _build_pattern(key, regex_mode=regex_mode or strict_word,
                         case_sensitive=case_sensitive, strict_word=strict_word)
    count_param = 1 if first_only else 0
    changed = 0
    with SessionLocal() as s:
        ids = [r[0] for r in candidates]
        rows = s.execute(select(Entry).where(Entry.id.in_(ids))).scalars().all()
        for e in rows:
            modified = False
            if scope in ("src","both"):
                new_src = pat.sub(replacement, e.src_text, count=count_param)
                if new_src != e.src_text: e.src_text = new_src; modified = True
            if scope in ("tgt","both"):
                new_tgt = pat.sub(replacement, e.tgt_text, count=count_param)
                if new_tgt != e.tgt_text: e.tgt_text = new_tgt; modified = True
            if modified: changed += 1
        s.commit()
    return changed

def search(q: str, ls=None, lt=None,
           source_names: Optional[List[str]] = None,
           limit=50, offset=0,
           date_from: Optional[str] = None,
           date_to: Optional[str] = None
           ) -> List[Tuple[int, str, str, Optional[str], datetime]]:
    with SessionLocal() as s:
        stmt = select(Entry.id, Entry.src_text, Entry.tgt_text, Source.name.label("source_name"), Entry.created_at)\
               .join(EntrySource, EntrySource.entry_id == Entry.id, isouter=True)\
               .join(Source, Source.id == EntrySource.source_id, isouter=True)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(or_(Entry.src_text.like(like), Entry.tgt_text.like(like)))
        if ls: stmt = stmt.where(Entry.lang_src == ls)
        if lt: stmt = stmt.where(Entry.lang_tgt == lt)
        if source_names: stmt = stmt.where(Source.name.in_(source_names))
        if date_from: stmt = stmt.where(Entry.created_at >= datetime.fromisoformat(date_from))
        if date_to: stmt = stmt.where(Entry.created_at < datetime.fromisoformat(date_to) + timedelta(days=1))
        stmt = stmt.order_by(Entry.created_at.desc()).limit(limit).offset(offset)
        return s.execute(stmt).all()
