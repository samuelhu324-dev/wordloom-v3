
import streamlit as st
from repo import list_memos, update_memo
from models import MemoStatus
from repo import get_stats

st.set_page_config(page_title="Orbit Hub", page_icon="🛰️", layout="wide")

# ---------------- Top Navigation (horizontal) ----------------
st.title("🛰️ Orbit · Hub")
mode = st.radio("导航", ["Memos", "Stats"], horizontal=True, label_visibility="collapsed")

# Keep selection in session
if "active_memo_id" not in st.session_state:
    st.session_state["active_memo_id"] = None

# ---------------- Layout: Left list (mini cards) + Right detail ----------------
left, right = st.columns([2, 3])

# ----- Left: tiny list always visible -----
with left:
    st.subheader("卡片列表", divider=True)
    q = st.text_input("关键词（左侧筛选）", placeholder="全文模糊匹配", key="q_left")
    tag = st.text_input("标签（模糊匹配）", placeholder="如：orbit,plan", key="tag_left")
    memos = list_memos(q=q, tag=tag, status="")

    if not memos:
        st.info("暂无记录。")
    else:
        for m in memos:
            with st.container(border=True):
                # first line content preview (short)
                preview = (m.text or "").strip().splitlines()
                first = preview[0] if preview else "（无内容）"
                if len(first) > 48:
                    first = first[:48] + "…"

                st.markdown(f"**#{m.id}** · {m.ts:%Y-%m-%d %H:%M}")
                st.caption(first)
                # select button
                if st.button("查看", key=f"sel_{m.id}"):
                    st.session_state["active_memo_id"] = m.id

with right:
    if mode == "Memos":
        st.subheader("详细 · Memos", divider=True)
        mid = st.session_state.get("active_memo_id")
        if not mid:
            st.info("在左侧选择一条记录以显示详情。")
        else:
            # Find the selected memo (fresh query to avoid detached session)
            ms = [m for m in list_memos(q="", tag="", status="") if m.id == mid]
            if not ms:
                st.warning("未找到所选记录，可能已被删除。")
            else:
                m = ms[0]
                st.markdown(f"**#{m.id}** · {m.ts:%Y-%m-%d %H:%M}")
                text_key = f"dt_text_{m.id}"
                tags_key = f"dt_tags_{m.id}"
                src_key = f"dt_src_{m.id}"
                lnk_key = f"dt_lnk_{m.id}"
                status_key = f"dt_status_{m.id}"

                st.text_area("内容", value=m.text, key=text_key, height=240)
                st.text_input("标签（逗号分隔）", value=m.tags, key=tags_key)
                st.text_input("来源", value=m.source, key=src_key)
                st.text_input("链接（逗号分隔）", value=m.links, key=lnk_key)
                status2 = st.selectbox(
                    "状态", ["draft", "done"],
                    index=0 if m.status.value == "draft" else 1,
                    key=status_key,
                )
                if st.button("保存修改", type="primary"):
                    update_memo(
                        m.id,
                        text=st.session_state[text_key],
                        tags=st.session_state[tags_key],
                        source=st.session_state[src_key],
                        links=st.session_state[lnk_key],
                        status=MemoStatus(status2),
                    )
                    st.success("已保存")
                    st.rerun()

                # Quick actions
                st.write("")
                col1, col2 = st.columns(2)
                if col1.button("设为 draft"):
                    update_memo(m.id, status=MemoStatus("draft")); st.rerun()
                if col2.button("设为 done"):
                    update_memo(m.id, status=MemoStatus("done")); st.rerun()

    elif mode == "Stats":
        st.subheader("统计 · 最近 7/30 天", divider=True)
        days = st.radio("范围", [7, 30], horizontal=True)
        s = get_stats(days=days)
        c1, c2, c3 = st.columns(3)
        c1.metric("Memos 数量", s["memos_count"])
        c2.metric("Tasks 完成数", s["tasks_done_count"])
        c3.metric("平均 Effort", round(s["avg_effort"], 2))
        st.caption("（注意：此 MVP 中 Tasks 暂未启用，完成数可能为 0）")
