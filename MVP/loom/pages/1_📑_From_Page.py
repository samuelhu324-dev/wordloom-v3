# -*- coding: utf-8 -*-
"""
From Page — v3 微调：修复右侧 ✏️/➕/🗑 按钮点了没反应的问题
做法：
- 用 session_state 记录当前激活的 entry（edit_id / ins_id / del_id）
- 使用 st.form + form_submit_button，避免半提交时页面重算丢状态
- 操作成功后 st.experimental_rerun()，保证列表立即刷新
"""
import os, re, base64, pathlib, traceback, requests
from typing import Any, Dict, List, Optional
import streamlit as st

API_BASE = os.getenv("WL_API_BASE", "http://127.0.0.1:8000")

# ---------------------- HTTP 适配器 ----------------------
class _HttpClient:
    def __init__(self, api_base: str) -> None:
        self.api_base = api_base.rstrip("/")
    def _get_json(self, path: str, params: Optional[dict] = None):
        r = requests.get(f"{self.api_base}{path}", params=params or {}, timeout=12)
        r.raise_for_status()
        return r.json()
    def list_sources(self) -> List[str]:
        try:
            data = self._get_json("/sources", {})
            if isinstance(data, list):
                if data and isinstance(data[0], dict):
                    return sorted({d.get("name","") for d in data if d.get("name")})
                return sorted({str(x) for x in data if x})
            return []
        except Exception:
            return []
    def sentences_by_source(self, source_name: str) -> List[Dict[str, Any]]:
        st.session_state.setdefault("_probe", [])
        candidates = [
            ("/entries", {"source_name": source_name}),
            ("/entries/search", {"q": source_name}),
            ("/entries/search", {"source_name": source_name}),
            ("/entries", {"source": source_name}),
            ("/entries/by_source", {"name": source_name}),
        ]
        for path, params in candidates:
            url = f"{self.api_base}{path}"
            try:
                r = requests.get(url, params=params, timeout=10)
                st.session_state["_probe"].append({"url": r.url, "status": r.status_code})
                if 200 <= r.status_code < 300:
                    j = r.json()
                    if isinstance(j, dict):
                        j = j.get("items") or j.get("data") or j.get("rows") or []
                    if isinstance(j, list) and len(j) > 0:
                        return j
            except Exception as e:
                st.session_state["_probe"].append({"url": url, "error": str(e)})
        return []
    def update_entry(self, entry_id: int, payload: Dict[str, Any]) -> Any:
        r = requests.put(f"{self.api_base}/entries/{int(entry_id)}", json=payload, timeout=12)
        r.raise_for_status()
        return r.json() if r.content else True
    def delete_entry(self, entry_id: int) -> Any:
        r = requests.delete(f"{self.api_base}/entries/{int(entry_id)}", timeout=12)
        r.raise_for_status()
        return r.json() if r.content else True

client = _HttpClient(API_BASE)

# ---------------------- 样式（简化版，保持 Home_Admin 观感） ----------------------
def _emit_font_css():
    css = """:root { --font-en-serif:"Constantia","Palatino Linotype","Palatino","Georgia",serif; --font-zh-serif:"Noto Serif SC","Source Han Serif SC","SimSun","霞鹜文楷","KaiTi",serif; --num-col-width:2.4rem; --num-gap:0.5rem; }
    .highlight{background-color:#007BFF;color:#fff;padding:0 2px;border-radius:3px;}
    .brk{color:#007BFF;}
    .row{display:grid;grid-template-columns:var(--num-col-width) 1fr;column-gap:var(--num-gap);align-items:start;}
    .num{color:#9ca3af;font-weight:400;font-size:1.25rem;font-family:"Palatino Linotype","Palatino","Georgia",serif;justify-self:end;}
    .num.ghost{visibility:hidden;}
    .source{margin-left:calc(var(--num-col-width) + var(--num-gap));color:#6b7280;display:block;}
    .ts{margin-left:calc(var(--num-col-width) + var(--num-gap));color:#6b7280;font-size:0.9rem;display:block;}
    .src{font-size:1.1rem;line-height:1.6;font-family:var(--font-en-serif);font-weight:500;margin-bottom:14px;display:block;}
    .tgt{font-size:1.05rem;line-height:1.65;font-family:var(--font-zh-serif);font-weight:400;margin-bottom:18px;display:block;}
    .toolbar button{padding:.15rem .35rem;margin-left:.2rem;border-radius:.4rem;}
    .toolbar{text-align:right;margin-top:2px;}"""
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def _highlight_keywords(text, keywords):
    if not keywords or not text: return text or ""
    try:
        pat = re.compile("(" + "|".join([re.escape(k) for k in keywords.split() if k]) + ")", re.IGNORECASE)
    except re.error:
        return text
    parts = re.split(r'(<[^>]+>)', text)
    for i, p in enumerate(parts):
        if not p or p.startswith("<"): continue
        parts[i] = pat.sub(lambda m: f"<span class='highlight'>{m.group(0)}</span>", p)
    return "".join(parts)

def _colorize_brackets(text): return re.sub(r'\[([^\[\]]+)\]', r"[<span class='brk'>\1</span>]", text or "")
def _render_text(text, keywords): return _highlight_keywords(_colorize_brackets(text), keywords)

# ---------------------- 页面 ----------------------
st.set_page_config(page_title='From • Source Article View', page_icon='📑', layout='wide')
_emit_font_css()

st.title("📑 From • Source Article View")

colL, colR = st.columns([5,1])
with colL:
    sources = client.list_sources()
    source_name = st.selectbox("Select a source", options=(sources or ["(No source found)"]))
with colR:
    st.button("⟲ Undo", key="undo_btn", disabled=True)
    st.button("⟳ Redo", key="redo_btn", disabled=True)

# 确保状态键存在
st.session_state.setdefault("edit_id", None)
st.session_state.setdefault("ins_id", None)
st.session_state.setdefault("del_id", None)

if source_name and not source_name.startswith("("):
    st.header(f"Sentences for: {source_name}")
    seq = client.sentences_by_source(source_name)
    if not seq:
        st.info("No sentences found for this source yet.")
    shown = 0
    for e in seq:
        if isinstance(e, dict):
            _id = e.get("id") or e.get("entry_id")
            src = e.get("src") or e.get("src_text") or e.get("source_text") or ""
            tgt = e.get("tgt") or e.get("tgt_text") or e.get("target_text") or ""
            sname = e.get("source_name") or e.get("source") or source_name
            ts = e.get("created_at") or e.get("ts") or ""
        else:
            _id = e[0] if len(e) > 0 else None
            src = e[1] if len(e) > 1 else ""
            tgt = e[2] if len(e) > 2 else ""
            sname = e[3] if len(e) > 3 else source_name
            ts = e[4] if len(e) > 4 else ""

        shown += 1
        src_h = _render_text(src, "")
        tgt_h = _render_text(tgt, "")

        c_text, c_tools = st.columns([10,2])
        with c_text:
            st.markdown(f"<div class='row'><span class='num'>{shown}.</span><span class='src'>{src_h}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='row'><span class='num ghost'>{shown}.</span><span class='tgt'>{tgt_h}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<span class='source'>{sname or ''}</span>", unsafe_allow_html=True)
            st.markdown(f"<span class='ts'>ID: {_id}</span>", unsafe_allow_html=True)

        with c_tools:
            st.markdown("<div class='toolbar'>", unsafe_allow_html=True)
            if st.button("✏️", key=f"btn_edit_{_id}"):
                st.session_state["edit_id"] = _id
                st.session_state["ins_id"] = None
                st.session_state["del_id"] = None
                st.experimental_rerun()
            if st.button("➕", key=f"btn_ins_{_id}"):
                st.session_state["ins_id"] = _id
                st.session_state["edit_id"] = None
                st.session_state["del_id"] = None
                st.experimental_rerun()
            if st.button("🗑", key=f"btn_del_{_id}"):
                st.session_state["del_id"] = _id
                st.session_state["edit_id"] = None
                st.session_state["ins_id"] = None
                st.experimental_rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # ---- 编辑区（使用 form 保留状态） ----
        if st.session_state.get("edit_id") == _id:
            with st.expander("Edit / Move", expanded=True):
                with st.form(key=f"edit_form_{_id}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_src = st.text_area("中文 / Source text", value=src, height=120)
                        new_tgt = st.text_area("English / Target text", value=tgt, height=120)
                    with c2:
                        new_source_name = st.text_input("Source name", value=sname or "")
                        move_pos = st.number_input("Move to position", min_value=0, value=shown, step=1)
                    c3, c4 = st.columns(2)
                    submitted = c3.form_submit_button("Save text")
                    cancel = c4.form_submit_button("Close")
                    if submitted:
                        payload = {"src": new_src.strip() or src, "tgt": new_tgt.strip() or tgt, "source_name": (new_source_name or '').strip(), "position": int(move_pos)}
                        try:
                            client.update_entry(int(_id), payload)
                            st.session_state["edit_id"] = None
                            st.success("Saved.")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Save failed: {e}")
                    if cancel:
                        st.session_state["edit_id"] = None
                        st.experimental_rerun()

        # ---- 插入 AFTER（使用 form） ----
        if st.session_state.get("ins_id") == _id:
            with st.expander("Insert AFTER", expanded=True):
                with st.form(key=f"ins_form_{_id}"):
                    zh_new = st.text_area("中文 / Source text", height=100)
                    en_new = st.text_area("English / Target text", height=100)
                    pos = st.number_input("Move to position", min_value=shown, value=shown, step=1)
                    c1, c2 = st.columns(2)
                    go = c1.form_submit_button("Insert AFTER")
                    cancel = c2.form_submit_button("Close")
                    if go:
                        try:
                            r = requests.post(f"{API_BASE}/entries", json={
                                "src": (zh_new or "").strip(), "tgt": (en_new or "").strip(),
                                "source_name": sname, "position": int(pos)
                            }, timeout=12)
                            r.raise_for_status()
                            st.session_state["ins_id"] = None
                            st.success("Inserted.")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Insert failed: {e}")
                    if cancel:
                        st.session_state["ins_id"] = None
                        st.experimental_rerun()

        # ---- 删除确认（使用 form） ----
        if st.session_state.get("del_id") == _id:
            with st.expander("Confirm delete?", expanded=True):
                with st.form(key=f"del_form_{_id}"):
                    st.warning("This will delete the entry permanently.")
                    c1, c2 = st.columns(2)
                    yes = c1.form_submit_button("Delete")
                    cancel = c2.form_submit_button("Cancel")
                    if yes:
                        try:
                            client.delete_entry(int(_id))
                            st.session_state["del_id"] = None
                            st.success(f"Deleted #{_id}.")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Delete failed: {e}")
                    if cancel:
                        st.session_state["del_id"] = None
                        st.experimental_rerun()

        st.markdown('---')

with st.expander("🔎 Probe（接口调试信息）", expanded=False):
    probes = st.session_state.get("_probe", [])
    st.write(probes if probes else "No records.")
    st.caption(f"API_BASE = {API_BASE}")
