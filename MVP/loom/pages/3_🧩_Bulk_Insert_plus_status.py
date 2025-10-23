# -*- coding: utf-8 -*-
"""
3_🧩_Bulk_Insert_plus_status.py — API 版
目标：
  1) 批量入库（CSV/粘贴/手动录入），显示进度与结果统计；默认 en→zh、不拆分。
  2) 批量查找与替换（可预览匹配，后端一次性替换）。

依赖：
  - from app import API_BASE              # 轻量配置文件
  - from repo import client, ApiError     # 前端 HTTP 客户端（已由你新 repo.py 提供）

保持原则：
  - 不改变你既有的“页面语义”和使用路径；
  - 不再直连 SQLite；全部通过 FastAPI；
  - 默认语言方向：ls='en', lt='zh'；不做句子拆分。
"""
from __future__ import annotations

import io
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
import streamlit as st

from app import API_BASE
from repo import client, ApiError

st.set_page_config(
    page_title="Wordloom · Bulk Insert & Status (API)",
    page_icon="🧩",
    layout="wide",
)

# ========= 工具函数 =========

def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _normalize_df(df: pd.DataFrame,
                  default_ls: str = "en",
                  default_lt: str = "zh",
                  default_source: str = "") -> pd.DataFrame:
    """
    兼容不同列名：src/src_text/source_text、tgt/tgt_text/target_text 等。
    填充默认 ls/lt/source_name；不进行切句。
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["src", "tgt", "ls", "lt", "source_name", "created_at"])

    # 统一列名映射
    rename_map = {}
    for c in df.columns:
        lc = c.strip().lower()
        if lc in ("src", "source_text", "src_text", "source"):
            rename_map[c] = "src"
        elif lc in ("tgt", "target_text", "tgt_text", "translation"):
            rename_map[c] = "tgt"
        elif lc in ("ls", "lang_src", "src_lang"):
            rename_map[c] = "ls"
        elif lc in ("lt", "lang_tgt", "tgt_lang"):
            rename_map[c] = "lt"
        elif lc in ("source_name", "source_title", "sourceid", "source_id", "出处", "来源"):
            rename_map[c] = "source_name"
        elif lc in ("created_at", "created", "time", "timestamp", "ts"):
            rename_map[c] = "created_at"
    df = df.rename(columns=rename_map)

    # 确保必须列
    for col, val in [
        ("src", ""), ("tgt", ""),
        ("ls", default_ls), ("lt", default_lt),
        ("source_name", default_source),
    ]:
        if col not in df.columns:
            df[col] = val
        else:
            df[col] = df[col].fillna(val)

    # created_at 可空
    if "created_at" not in df.columns:
        df["created_at"] = ""

    # 只保留需要的列顺序
    return df[["src", "tgt", "ls", "lt", "source_name", "created_at"]]

def _parse_pasted(text: str,
                  sep: str = "\t",
                  default_ls: str = "en",
                  default_lt: str = "zh",
                  default_source: str = "") -> pd.DataFrame:
    """
    从文本框解析批量数据：
    - 每行一条；
    - 支持两列（src sep tgt）或 3~6 列（额外列按 ls, lt, source_name, created_at 含义）。
    """
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    rows = []
    for ln in lines:
        parts = [p.strip() for p in ln.split(sep)]
        src = parts[0] if len(parts) >= 1 else ""
        tgt = parts[1] if len(parts) >= 2 else ""
        ls  = parts[2] if len(parts) >= 3 and parts[2] else default_ls
        lt  = parts[3] if len(parts) >= 4 and parts[3] else default_lt
        source_name = parts[4] if len(parts) >= 5 and parts[4] else default_source
        created_at  = parts[5] if len(parts) >= 6 else ""
        rows.append([src, tgt, ls, lt, source_name, created_at])
    return pd.DataFrame(rows, columns=["src", "tgt", "ls", "lt", "source_name", "created_at"])

# ========= 页面结构 =========

st.title("🧩 批量入库 & 状态（API）")
st.caption(f"API_BASE = {API_BASE}")

tab_insert, tab_ops = st.tabs(["📚 批量入库", "🛠️ 批量查找 / 替换"])

# ------------------------------------------------------------
# 📚 批量入库
# ------------------------------------------------------------
with tab_insert:
    st.subheader("批量入库（默认 en → zh，不拆分）")

    colA, colB, colC = st.columns([1.2, 1, 1])
    with colA:
        default_source = st.text_input("默认出处（可留空）", value="")
    with colB:
        default_ls = st.selectbox("默认源语言 (ls)", ["en", "zh"], index=0)
    with colC:
        default_lt = st.selectbox("默认目标语言 (lt)", ["zh", "en"], index=0)

    st.markdown("#### 方式一：上传 CSV")
    st.caption("支持列：src,tgt,ls,lt,source_name,created_at（列名可不完全一致，会自动识别）。")
    csv_file = st.file_uploader("选择 CSV 文件", type=["csv"], key="csv_uploader")

    st.markdown("#### 方式二：粘贴文本（每行一条、列用分隔符）")
    paste_sep = st.radio("分隔符", ["Tab(\\t)", "逗号(,)", "竖线(|)"], index=0, horizontal=True)
    sep_map = {"Tab(\\t)": "\t", "逗号(,)": ",", "竖线(|)": "|"}
    paste_text = st.text_area("在此粘贴：示例：source<TAB>target", height=160, key="paste_area")

    st.markdown("#### 方式三：表格手填（可与前两种合并）")
    init_rows = st.number_input("预置空行数", 0, 50, 0, step=1)
    if init_rows > 0 and "manual_df" not in st.session_state:
        st.session_state.manual_df = pd.DataFrame(
            [["", "", default_ls, default_lt, default_source, ""] for _ in range(init_rows)],
            columns=["src", "tgt", "ls", "lt", "source_name", "created_at"]
        )
    manual_df = st.data_editor(
        st.session_state.get("manual_df", pd.DataFrame(
            columns=["src", "tgt", "ls", "lt", "source_name", "created_at"]
        )),
        use_container_width=True,
        key="manual_editor",
        num_rows="dynamic",
        column_config={
            "src": st.column_config.TextColumn("源文本"),
            "tgt": st.column_config.TextColumn("译文"),
            "ls": st.column_config.TextColumn("ls"),
            "lt": st.column_config.TextColumn("lt"),
            "source_name": st.column_config.TextColumn("出处"),
            "created_at": st.column_config.TextColumn("创建时间"),
        }
    )

    st.divider()
    colX, colY = st.columns([1, 1])
    with colX:
        btn_preview = st.button("👀 预览合并数据", type="secondary", use_container_width=True)
    with colY:
        btn_commit = st.button("🚀 批量入库（写入数据库）", type="primary", use_container_width=True)

    if btn_preview or btn_commit:
        frames: List[pd.DataFrame] = []

        # CSV
        if csv_file is not None:
            try:
                df_csv = pd.read_csv(csv_file)
                frames.append(_normalize_df(df_csv, default_ls, default_lt, default_source))
            except Exception as e:
                st.error(f"CSV 解析失败：{e}")

        # 粘贴
        if paste_text.strip():
            try:
                df_paste = _parse_pasted(
                    paste_text,
                    sep=sep_map[paste_sep],
                    default_ls=default_ls, default_lt=default_lt, default_source=default_source
                )
                frames.append(df_paste)
            except Exception as e:
                st.error(f"粘贴文本解析失败：{e}")

        # 手填
        if not manual_df.empty:
            frames.append(_normalize_df(manual_df, default_ls, default_lt, default_source))

        # 合并
        if frames:
            merged = pd.concat(frames, ignore_index=True)
            # 过滤空行（src 与 tgt 任一非空即可；完全空的丢弃）
            merged = merged[~((merged["src"].astype(str).str.strip() == "")
                              & (merged["tgt"].astype(str).str.strip() == ""))].copy()
            # 去重（src+tgt+ls+lt+source_name）
            merged.drop_duplicates(subset=["src", "tgt", "ls", "lt", "source_name"], inplace=True)
        else:
            merged = pd.DataFrame(columns=["src", "tgt", "ls", "lt", "source_name", "created_at"])

        if merged.empty:
            st.warning("没有有效数据。请至少通过一种方式提供条目。")
        else:
            st.success(f"合并后共 {len(merged)} 条记录。默认 en→zh、不拆分。")
            st.dataframe(merged.head(100), use_container_width=True)
            st.caption("上表仅展示前 100 行预览。")

            if btn_commit:
                st.info("开始写入，请稍候……")
                progress = st.progress(0.0)
                status_area = st.empty()

                total = len(merged)
                ok, fail = 0, 0
                failed_rows: List[Tuple[int, str]] = []

                for i, row in merged.reset_index(drop=True).iterrows():
                    try:
                        payload = dict(
                            src=str(row.get("src", "")),
                            tgt=str(row.get("tgt", "")),
                            ls=str(row.get("ls", default_ls) or default_ls),
                            lt=str(row.get("lt", default_lt) or default_lt),
                            source_name=str(row.get("source_name", default_source) or default_source),
                            created_at=str(row.get("created_at", "")) or None,
                        )
                        if not payload["src"] and not payload["tgt"]:
                            # 跳过空白
                            continue
                        client.add_entry(**payload)  # 交给后端；不做切句
                        ok += 1
                    except ApiError as e:
                        fail += 1
                        failed_rows.append((i + 1, str(e)))
                    progress.progress((i + 1) / total)
                    status_area.write(f"已处理 {i+1}/{total} · 成功 {ok} · 失败 {fail}")

                st.success(f"写入完成：成功 {ok} 条，失败 {fail} 条。")
                if failed_rows:
                    with st.expander("查看失败明细"):
                        fail_df = pd.DataFrame(failed_rows, columns=["行号(合并后)", "错误"])
                        st.dataframe(fail_df, use_container_width=True)

# ------------------------------------------------------------
# 🛠️ 批量查找 / 替换
# ------------------------------------------------------------
with tab_ops:
    st.subheader("批量查找 / 替换（由后端执行）")

    col1, col2 = st.columns([1.2, 1])
    with col1:
        keyword = st.text_input("关键词 / 正则", value="")
        replacement = st.text_input("替换为（预览时可留空）", value="")
    with col2:
        scope = st.selectbox("作用范围", ["both", "src", "tgt"], index=0)
        source_filter = st.text_input("限定出处（可留空）", value="")

    col3, col4, col5 = st.columns(3)
    with col3:
        regex_mode = st.checkbox("正则模式", value=False)
    with col4:
        case_sensitive = st.checkbox("大小写敏感", value=False)
    with col5:
        strict_word = st.checkbox("整词匹配", value=False)

    col6, col7 = st.columns(2)
    with col6:
        date_from = st.date_input("起始日期", value=None)
    with col7:
        date_to = st.date_input("结束日期", value=None)

    colA, colB = st.columns(2)
    with colA:
        if st.button("👀 预览匹配", type="secondary", use_container_width=True):
            try:
                matches = client.find_matches(
                    keyword=keyword,
                    scope=scope,
                    source_name=source_filter or None,
                    date_from=str(date_from) if date_from else None,
                    date_to=str(date_to) if date_to else None,
                    limit=300,
                    regex_mode=regex_mode,
                    case_sensitive=case_sensitive,
                    strict_word=strict_word
                )
                if not matches:
                    st.info("没有匹配项。")
                else:
                    st.success(f"找到 {len(matches)} 条候选。仅展示前 300 条。")
                    st.dataframe(pd.DataFrame(matches), use_container_width=True)
            except ApiError as e:
                st.error(f"预览失败：{e}")

    with colB:
        if st.button("⚡ 执行替换（不可逆）", type="primary", use_container_width=True):
            if not keyword:
                st.warning("请先填写关键词。")
            else:
                try:
                    changed = client.bulk_replace(
                        keyword=keyword,
                        replacement=replacement,
                        scope=scope,
                        source_name=source_filter or None,
                        date_from=str(date_from) if date_from else None,
                        date_to=str(date_to) if date_to else None,
                        regex_mode=regex_mode,
                        case_sensitive=case_sensitive,
                        strict_word=strict_word,
                        first_only=False,   # 保持与你以往“批量替换”一致的语义
                    )
                    st.success(f"替换完成：修改 {changed} 处。")
                except ApiError as e:
                    st.error(f"替换失败：{e}")

# 页脚
st.caption(f"现在是 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · 已连接 API: {API_BASE}")
