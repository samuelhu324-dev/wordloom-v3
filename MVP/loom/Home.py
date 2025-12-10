# -*- coding: utf-8 -*-
"""
Home.py — 前端主页（检索 / 就地编辑 / 删除），框架无关写法
数据访问统一走 DataService（repo.get_data_service）
  - 默认模式：SQLite（WL_DATA_MODE=sqlite）
  - 切到 API ：设置 WL_DATA_MODE=api，并配置 WL_API_BASE、WL_API_TOKEN
"""

from __future__ import annotations
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
import streamlit as st

# ---------- DataService 入口（新） ----------
# 兼容：若新 repo 不可用，则回退到 legacy（仍可跑）
try:
    from repo import get_data_service          # 新实现优先
    _svc = get_data_service()
except Exception:
    # 回退到旧 repo 的适配器
    from repo_shim_legacy import get_data_service
    _svc = get_data_service()

st.set_page_config(
    page_title="Wordloom · Home",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- 小工具 ----------
def _normalize_rows(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    """把返回字段规范到统一列名，便于渲染/编辑。"""
    if not rows:
        return pd.DataFrame(columns=["id", "src", "tgt", "ls", "lt", "source_name", "created_at"])
    normed = []
    for r in rows:
        normed.append({
            "id": r.get("id") or r.get("entry_id"),
            "src": r.get("src") or r.get("src_text") or r.get("source_text"),
            "tgt": r.get("tgt") or r.get("tgt_text") or r.get("target_text"),
            "ls": r.get("ls") or r.get("lang_src") or r.get("src_lang") or "zh",
            "lt": r.get("lt") or r.get("lang_tgt") or r.get("tgt_lang") or "en",
            "source_name": r.get("source_name") or r.get("source") or "",
            "created_at": r.get("created_at") or r.get("ts") or "",
        })
    df = pd.DataFrame(normed)
    if "created_at" in df.columns and df["created_at"].notna().any():
        try:
            df["__dt"] = pd.to_datetime(df["created_at"], errors="coerce")
            df = df.sort_values("__dt", ascending=False).drop(columns=["__dt"])
        except Exception:
            pass
    return df

def _diff_updates(original: pd.DataFrame, edited: pd.DataFrame) -> List[Dict[str, Any]]:
    """找出被修改的行，用于批量 update。"""
    updates = []
    if original.empty and edited.empty:
        return updates
    orig = original.set_index("id")
    edt = edited.set_index("id")
    common_ids = orig.index.intersection(edt.index)
    for rid in common_ids:
        row_o, row_e = orig.loc[rid], edt.loc[rid]
        changed = {}
        for k in ["src", "tgt", "ls", "lt", "source_name"]:
            vo = "" if pd.isna(row_o.get(k)) else row_o.get(k)
            ve = "" if pd.isna(row_e.get(k)) else row_e.get(k)
            if vo != ve:
                changed[k] = ve
        if changed:
            updates.append({"id": int(rid), **changed})
    return updates

def _read_version() -> str:
    """优先读前端自己的 VERSION，读不到回退到仓库根。"""
    vf = Path(__file__).resolve().parent / "VERSION"
    if not vf.exists():
        vf = Path(__file__).resolve().parents[2] / "VERSION"
    try:
        return vf.read_text(encoding="utf-8").strip()
    except Exception:
        return "unknown"

# ---------- 侧边栏：检索条件 ----------
with st.sidebar:
    st.markdown("### ⚙️ 数据通道")
    st.code(
        f"WL_DATA_MODE={os.getenv('WL_DATA_MODE','sqlite')}\n"
        f"WL_SQLITE_PATH={os.getenv('WL_SQLITE_PATH','streamlit/app.db')}\n"
        f"WL_API_BASE={os.getenv('WL_API_BASE','http://localhost:8000')}",
        language="bash",
    )
    st.divider()
    st.markdown("### 🔎 检索条件")
    q = st.text_input("关键词 / 短语（必填）", value="协议")
    limit = st.slider("返回条数", 10, 200, 50)
    col_a, col_b = st.columns(2)
    with col_a:
        ls = st.selectbox("源语言(ls)", ["", "zh", "en"], index=1)
    with col_b:
        lt = st.selectbox("目标语言(lt)", ["", "en", "zh"], index=1)
    source_name = st.text_input("出处（可留空/多词请到 Bulk 页）", value="")
    col1, col2 = st.columns(2)
    with col1:
        date_from = st.date_input("起始日期", value=None)
    with col2:
        date_to = st.date_input("结束日期", value=None)
    btn_search = st.button("开始检索", use_container_width=True, type="primary")

# ---------- 主区 ----------
st.title("🔍 翻译语料检索")

if "search_df" not in st.session_state:
    st.session_state.search_df = pd.DataFrame()

if btn_search:
    try:
        rows = _svc.search(
            q=q.strip(),
            limit=int(limit),
            offset=0,
        ) if (not ls and not lt and not source_name and not date_from and not date_to) else _svc.search(
            q=q.strip(), limit=int(limit), offset=0
        )
        # 说明：不同 DataService 的筛选参数命名可能不同，这里先用最小公共子集；
        # 若你新 repo 已实现更丰富筛选，可在此直接传入相应 kwargs。
        st.session_state.search_df = _normalize_rows(rows)
        if st.session_state.search_df.empty:
            st.info("没有命中结果。你可以放宽条件或更换关键词。")
    except Exception as e:
        st.error(f"检索失败：{e}")

df = st.session_state.search_df.copy()

if not df.empty:
    st.caption("提示：双击单元格即可编辑；右侧可按 ID 批量删除。")
    # 保证列顺序 + 可编辑列
    show_cols = ["id", "src", "tgt", "ls", "lt", "source_name", "created_at"]
    for c in show_cols:
        if c not in df.columns:
            df[c] = ""
    df = df[show_cols]

    edited = st.data_editor(
        df,
        column_config={
            "id": st.column_config.NumberColumn("id", disabled=True),
            "src": st.column_config.TextColumn("源文本"),
            "tgt": st.column_config.TextColumn("译文"),
            "ls": st.column_config.TextColumn("ls"),
            "lt": st.column_config.TextColumn("lt"),
            "source_name": st.column_config.TextColumn("出处"),
            "created_at": st.column_config.TextColumn("创建时间", disabled=True),
        },
        disabled=["id", "created_at"],
        use_container_width=True,
        key="editor",
        num_rows="fixed",
        height=min(600, 120 + 38 * min(len(df), 12)),
    )

    st.divider()
    colL, colR = st.columns([2, 1])
    with colL:
        if st.button("💾 保存编辑变更", type="primary"):
            updates = _diff_updates(df, edited)
            if not updates:
                st.success("没有检测到修改。")
            else:
                ok, fail = 0, 0
                for u in updates:
                    try:
                        rid = u.pop("id")
                        _svc.update_item(rid, u)
                        ok += 1
                    except Exception as e:
                        fail += 1
                        st.error(f"更新失败（id={rid}）：{e}")
                st.success(f"更新完成：成功 {ok} 条，失败 {fail} 条。")
                st.session_state.search_df = edited
    with colR:
        del_ids_str = st.text_input("🗑️ 需删除的 ID（逗号分隔）", "")
        if st.button("删除所填 ID"):
            ids = [int(x.strip()) for x in del_ids_str.split(",") if x.strip().isdigit()]
            if not ids:
                st.warning("请填入要删除的数字 ID（支持多个，逗号分隔）。")
            else:
                ok, fail = 0, 0
                for rid in ids:
                    try:
                        _svc.delete_item(rid)
                        ok += 1
                    except Exception as e:
                        fail += 1
                        st.error(f"删除失败（id={rid}）：{e}")
                if ok:
                    st.session_state.search_df = st.session_state.search_df[~st.session_state.search_df["id"].isin(ids)]
                st.success(f"删除完成：成功 {ok} 条，失败 {fail} 条。")

else:
    st.info("左侧设置条件后点击"开始检索"。")

# ---------- 统一页脚 ----------
ver = _read_version()
st.markdown(
    f"""
    <style>
    .wl-footer {{
        position: fixed; left: 0; right: 0; bottom: 0;
        padding: 6px 12px; font-size: 12px; opacity: 0.75;
        border-top: 1px solid #e6e6e6; background: rgba(255,255,255,0.85);
        backdrop-filter: blur(6px);
    }}
    </style>
    <div class="wl-footer">
      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
      · Wordloom Frontend v<b>{ver}</b>
      · 通道: <code>{os.getenv('WL_DATA_MODE','sqlite')}</code>
    </div>
    """,
    unsafe_allow_html=True,
)
