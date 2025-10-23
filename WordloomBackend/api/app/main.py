# ---- app/main.py
import os
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal

app = FastAPI(title="Wordloom API")

# CORS：全量放开（开发期最省心；要收紧可改 allow_origins）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 你原有的路由保持不变
from app.routers.loom import entries as loom_entries, sources as loom_sources, auth as loom_auth
app.include_router(loom_entries.router, prefix="/api/common", tags=["Common"])
app.include_router(loom_sources.router, prefix="/api/common", tags=["Common"])
app.include_router(loom_auth.router,    prefix="/api/common", tags=["Common"])

ORBIT_ENABLED = os.getenv("ORBIT_ENABLED", "false").lower() == "true"
if ORBIT_ENABLED:
    from app.routers.orbit import tasks as orbit_tasks, memos as orbit_memos, stats as orbit_stats
    app.include_router(orbit_tasks.router, prefix="/api/orbit", tags=["Orbit"])
    app.include_router(orbit_memos.router, prefix="/api/orbit", tags=["Orbit"])
    app.include_router(orbit_stats.router, prefix="/api/orbit", tags=["Orbit"])


# -------------------------------
# 辅助：批量插入所需的 Pydantic 模型
# -------------------------------
class EntryIn(BaseModel):
    src: str
    tgt: str
    lang_src: str
    lang_tgt: str
    article_id: Optional[int] = None
    position: Optional[int] = 0
    created_at: Optional[str] = None      # ISO 字符串，可选
    source_name: Optional[str] = None     # “来源”名称，可选


class EntryBatchIn(BaseModel):
    items: List[EntryIn]


# -------------------------------
# 工具：确保 source 存在，返回 source_id
# -------------------------------
def ensure_source_id(session, source_name: str) -> Optional[int]:
    if not source_name:
        return None
    # name 唯一：优先插入，不存在则创建；存在则返回 id
    # Postgres UPSERT
    sql = text("""
        INSERT INTO sources(name) VALUES (:name)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
    """)
    sid = session.execute(sql, {"name": source_name}).scalar_one()
    return sid


# -------------------------------
# 新增：批量插入端点（幂等、一次提交）
# POST /api/common/entries/batch
# -------------------------------
@app.post("/api/common/entries/batch")
def create_entries_batch(payload: EntryBatchIn):
    """
    允许前端一次插入多条 entry。
    对于每条：
      - 插入 entries，返回 id
      - 若带 source_name：确保 sources 存在，并写入 entry_sources（去重）
    """
    out: List[dict] = []
    if not payload.items:
        return out

    try:
        with SessionLocal() as s:
            for it in payload.items:
                # created_at：尽量使用传入；缺省用当前 UTC
                created_at = None
                if it.created_at:
                    try:
                        created_at = datetime.fromisoformat(
                            it.created_at.replace("Z", "+00:00")
                        )
                    except Exception:
                        created_at = None
                if created_at is None:
                    created_at = datetime.utcnow()

                # 1) 插入 entries
                insert_entry = text("""
                    INSERT INTO entries
                      (src_text, tgt_text, lang_src, lang_tgt, article_id, position, created_at)
                    VALUES
                      (:src, :tgt, :lang_src, :lang_tgt, :article_id, :position, :created_at)
                    RETURNING id
                """)
                eid = s.execute(
                    insert_entry,
                    {
                        "src": it.src,
                        "tgt": it.tgt,
                        "lang_src": it.lang_src,
                        "lang_tgt": it.lang_tgt,
                        "article_id": it.article_id,
                        "position": it.position or 0,
                        "created_at": created_at,
                    },
                ).scalar_one()

                # 2) 处理来源（可选）
                if it.source_name:
                    sid = ensure_source_id(s, it.source_name)
                    if sid:
                        link_sql = text("""
                            INSERT INTO entry_sources(entry_id, source_id)
                            VALUES (:eid, :sid)
                            ON CONFLICT DO NOTHING
                        """)
                        s.execute(link_sql, {"eid": eid, "sid": sid})

                out.append({"id": eid})

            s.commit()
    except SQLAlchemyError as e:
        # 统一抛出错误细节，前端能看到 500 + 文本
        msg = str(e.__cause__ or e)
        return {"error": msg}

    return out


# -------------------------------
# 调试：数据库探针（保持）
# GET /debug/dbinfo
# -------------------------------
from sqlalchemy import text as _text  # 避免上面的 text 覆盖
@app.get("/debug/dbinfo")
def dbinfo():
    info = {}
    try:
        with SessionLocal() as s:
            db = s.execute(_text("SELECT current_database()")).scalar()
            sp = s.execute(_text("SHOW search_path")).scalar()
            exists = s.execute(_text("SELECT to_regclass('public.entries') IS NOT NULL")).scalar()
            info["current_database"] = db
            info["search_path"] = sp
            info["has_public_entries"] = bool(exists)
    except Exception as e:
        info["error"] = str(e)

    # 显示有效 DATABASE_URL（脱敏）
    eff = os.getenv("DATABASE_URL", "")
    try:
        u = urlparse(eff)
        if u.scheme:
            masked = f"{u.scheme}://{u.username or ''}:****@{u.hostname or ''}:{u.port or ''}{u.path or ''}"
        else:
            masked = eff
    except Exception:
        masked = eff
    info["effective_DATABASE_URL"] = masked
    return info
