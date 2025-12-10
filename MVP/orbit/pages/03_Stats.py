import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import select, func
from db import session_scope
from models import Memo, Task, TaskStatus
from repo import get_stats

st.set_page_config(page_title="Stats", page_icon="📈", layout="wide")
st.title("📈 Stats")

range_days = st.radio("范围", [7, 30], horizontal=True, format_func=lambda x: f"{x} 天")
summary = get_stats(days=range_days)

st.metric("Memos 数量", summary["memos_count"])
st.metric("Tasks 完成数", summary["tasks_done_count"])
st.metric("平均 Effort", round(summary["avg_effort"],2))

st.subheader("按日聚合")
with session_scope() as s:
    cutoff = datetime.utcnow() - timedelta(days=range_days)
    # 每日 memos 数
    memo_rows = s.execute(
        select(func.date(Memo.ts), func.count()).where(Memo.ts>=cutoff).group_by(func.date(Memo.ts)).order_by(func.date(Memo.ts))
    ).all()
    # 每日完成 tasks 数
    done_rows = s.execute(
        select(func.date(Task.created_at), func.count()).where(Task.status==TaskStatus.done, Task.created_at>=cutoff).group_by(func.date(Task.created_at)).order_by(func.date(Task.created_at))
    ).all()

df = pd.DataFrame({
    "date": [r[0] for r in memo_rows or []] or [],
    "memos": [r[1] for r in memo_rows or []] or []
})
df2 = pd.DataFrame({
    "date": [r[0] for r in done_rows or []] or [],
    "tasks_done": [r[1] for r in done_rows or []] or []
})

st.line_chart(df.set_index("date"))  # 不指定颜色/样式
st.line_chart(df2.set_index("date"))
