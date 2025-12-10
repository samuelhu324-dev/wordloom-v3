from __future__ import annotations
import sys, json
from datetime import datetime
from db import session_scope
from models import Memo, Task, MemoStatus, TaskStatus

def parse_ts(s):
    if not s: return None
    # 尝试多种格式
    try: return datetime.fromisoformat(s.replace("Z",""))
    except Exception: return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

def ensure_memo(d, s):
    m = s.get(Memo, d["id"])
    if not m:
        m = Memo(id=d["id"])
    m.ts = parse_ts(d.get("ts")) or m.ts
    m.text = d.get("text","")
    m.tags = ",".join(d.get("tags",[]))
    m.source = d.get("source","")
    m.links = ",".join(d.get("links",[]))
    m.status = MemoStatus(d.get("status","draft"))
    s.add(m)

def ensure_task(d, s):
    t = s.get(Task, d["id"])
    if not t:
        t = Task(id=d["id"])
    t.title = d.get("title","")
    t.created_at = parse_ts(d.get("created_at")) or t.created_at
    t.due_at = parse_ts(d.get("due_at"))
    t.status = TaskStatus(d.get("status","todo"))
    t.effort = int(d.get("effort",3))
    t.memo_id = d.get("memo_id")
    s.add(t)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python import_json.py orbit_export.json"); sys.exit(1)
    path = sys.argv[1]
    data = json.load(open(path, "r", encoding="utf-8"))
    with session_scope() as s:
        for m in data.get("memos",[]):
            ensure_memo(m, s)
        for t in data.get("tasks",[]):
            ensure_task(t, s)
    print("导入完成。")
