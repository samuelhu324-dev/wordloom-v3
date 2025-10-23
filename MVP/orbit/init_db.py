from __future__ import annotations
from datetime import datetime, timedelta
from db import engine
from models import Base, Memo, Task, MemoStatus, TaskStatus
from repo import create_memo, create_task

print("创建表...")
Base.metadata.create_all(bind=engine)

# 插入示例数据（仅当空库时）
from sqlalchemy import inspect
insp = inspect(engine)
has_data = any(insp.get_table_names())

from db import session_scope
with session_scope() as s:
    memo_count = s.query(Memo).count()
    if memo_count == 0:
        print("插入示例数据...")
        m1 = create_memo("把 Orbit MVP 落地：Memos/Tasks/Stats", tags="orbit,plan", source="notebook", status=MemoStatus.draft)
        m2 = create_memo("把 Streamlit 原型跑起来，今天就能用", tags="streamlit", source="idea", status=MemoStatus.done)
        now = datetime.utcnow()
        create_task("实现 Memos 列表/筛选/编辑", due_at=now+timedelta(days=1), effort=3, memo_id=m1.id)
        create_task("实现 Tasks 看板与状态切换", due_at=now+timedelta(days=2), effort=4, memo_id=m1.id)
        create_task("实现 Stats 聚合与折线", due_at=now+timedelta(days=3), effort=2, memo_id=m2.id, status=TaskStatus.doing)
        print("完成。")
    else:
        print("已存在数据，跳过示例插入。")
print("OK")
