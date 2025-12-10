from __future__ import annotations
import json
from datetime import datetime
from sqlalchemy import select
from db import session_scope
from models import Memo, Task

def to_dict_memo(m:Memo):
    return dict(id=m.id, ts=m.ts.isoformat(), text=m.text, tags=m.tags.split(",") if m.tags else [],
                source=m.source, links=m.links.split(",") if m.links else [], status=m.status.value)

def to_dict_task(t:Task):
    return dict(id=t.id, title=t.title, created_at=t.created_at.isoformat(),
                due_at=t.due_at.isoformat() if t.due_at else None,
                status=t.status.value, effort=t.effort, memo_id=t.memo_id)

with session_scope() as s:
    memos = [to_dict_memo(m) for m in s.scalars(select(Memo)).all()]
    tasks = [to_dict_task(t) for t in s.scalars(select(Task)).all()]

payload = {
    "version":"0.1.0",
    "exported_at": datetime.utcnow().isoformat(timespec="seconds")+"Z",
    "memos": memos,
    "tasks": tasks
}
with open("orbit_export.json","w",encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print("已导出 -> orbit_export.json")
