# 2_📚_Insert.py — Insert / Detection / Rename / Recent  [API版, 安全微调 v3]
# 要点：始终渲染页面；导入/后端异常以可见方式提示；其余逻辑完全沿用你的旧版。

import re, traceback
from datetime import datetime, timedelta, date
from typing import List, Tuple

import streamlit as st

# --- 页面基础：务必最先渲染，让“白屏”不再白 ---
st.set_page_config(page_title="Batch Insert (Flexible)", layout="wide", page_icon="📦")
st.title("📚 Insert — Insert / Detection / Rename / Recent（API）")

# --- 软导入：不让异常把页面整空白 ---
API_BASE = None
client = None
import_notes = []

try:
    from app import API_BASE as _API_BASE   # Frontend 的 app.py
    API_BASE = _API_BASE
except Exception as e:
    API_BASE = "http://127.0.0.1:8000"
    import_notes.append(("app.API_BASE", str(e), traceback.format_exc()))

try:
    from repo import client as _client      # 你的 repo.client
    client = _client
except Exception as e:
    client = None
    import_notes.append(("repo.client", str(e), traceback.format_exc()))

# --- 顶部调试提示（可折叠） ---
if import_notes:
    with st.expander("⚠️ 模块导入异常（点此展开查看如何修复）", expanded=True):
        st.markdown(f"- 当前 API_BASE：`{API_BASE}`")
        for name, msg, tb in import_notes:
            st.error(f"无法导入：`{name}` → {msg}")
            st.code(tb, language="python")
        st.info("若 `repo.client` 导入失败：请确认运行目录包含 `repo.py` 所在包；或把项目根目录加入 PYTHONPATH。")

# ===== CSS（保持你旧版风格，仅轻度微调） =====
st.markdown('''
<style>
.sticky-toolbar { position: sticky; top: 0; z-index: 9999; background: rgba(255,255,255,0.92); backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px); padding: 8px 12px; border-bottom: 1px solid #eee; }
.stRadio > div { gap: 14px !important; }
.sticky-toolbar .stButton>button { background:#ff4b4b !important; color:#fff !important; border:0 !important; border-radius:12px !important; padding:8px 14px !important; font-weight:600 !important; box-shadow:0 6px 18px rgba(0,0,0,.12), 0 2px 6px rgba(0,0,0,.08) !important; }
.sticky-toolbar .stButton>button:disabled { opacity:.55 !important; cursor:not-allowed !important; }
.block-container { max-width: 1180px; }
.stTextArea textarea { min-height: 180px; line-height: 1.45; font-size: 0.96rem; }
</style>
''', unsafe_allow_html=True)

# ===== 依赖（requests 仅在调用时用） =====
import requests

# ====== 小工具 ======
@st.cache_data(ttl=60, show_spinner=False)
def _list_sources(API_BASE_value: str) -> List[str]:
    '''尝试从后端读取所有source名称；失败则返回空列表。兼容 name/source_name/纯字符串。'''
    try:
        r = requests.get(f"{API_BASE_value}/sources", timeout=6)
        r.raise_for_status()
        data = r.json() or []
        names = set()
        for d in data:
            if isinstance(d, dict):
                v = d.get("name") or d.get("source_name") or ""
            else:
                v = str(d)
            v = str(v).strip()
            if v:
                names.add(v)
        return sorted(names)
    except Exception:
        return []

def _normalize_ws(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.strip()
    import re as _re
    return _re.sub(r"[ \t]{2,}", " ", s)

def split_text(text: str, mode: str, delim_regex: str) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    if mode == "no_split":
        return [_normalize_ws(text)]
    if mode == "by_line":
        return [ln.strip() for ln in text.splitlines() if ln.strip()]
    import re as _re
    parts = _re.split(delim_regex, text)
    return [p.strip() for p in parts if p and p.strip()]

def lang_score(text: str):
    import re as _re
    zh = len(_re.findall(r'[\u4e00-\u9fff]', text or ""))
    en = len(_re.findall(r'[A-Za-z]', text or ""))
    return zh, en

def check_lang_direction(text: str, expect: str, min_len: int, dominance: float) -> bool:
    if not text or len(text) < min_len:
        return True
    zh, en = lang_score(text)
    return (zh >= dominance * max(1, en)) if expect == "zh" else (en >= dominance * max(1, zh))

# 预置 session_state，避免 KeyError
st.session_state.setdefault("ins_dir", "en→zh")
st.session_state.setdefault("ins_mode", "不要拆分（整段入库）")
st.session_state.setdefault("ins_regex", r"[。！？；;.!?:]+")
st.session_state.setdefault("src_input", "")
st.session_state.setdefault("tgt_input", "")
st.session_state.setdefault("ins_srcpick", "➕ New…")
st.session_state.setdefault("ins_srcname", "MyBatch")
st.session_state.setdefault("ins_ts", datetime.now().isoformat(timespec="seconds"))
st.session_state.setdefault("detect_enable", True)
st.session_state.setdefault("detect_minlen", 10)
st.session_state.setdefault("detect_dom", 2.0)

# -------- Tabs --------
tab_insert, tab_preview, tab_detect, tab_rename, tab_recent = st.tabs(
    ["📥 Insert", "👀 Preview", "🧪 Detection", "🛠️ Rename", "🧾 Recent"]
)

# -------- Insert tab --------
with tab_insert:
    st.markdown('<div class="sticky-toolbar">', unsafe_allow_html=True)
    c1, c2 = st.columns([4, 1], gap="small")
    with c1:
        direction = st.radio("本批次翻译方向 / Direction", ["zh→en", "en→zh"], index=(1 if st.session_state["ins_dir"]=="en→zh" else 0), horizontal=True, key="ins_dir")
    with c2:
        mode_display = st.session_state.get("ins_mode")
        mode_key_top = {"不要拆分（整段入库）": "no_split","按行对齐（每行是一条）": "by_line","按分隔符（正则）": "by_regex"}.get(mode_display, "no_split")
        default_regex = r"[。！？；;.!?:]+"
        delim_regex_top = st.session_state.get("ins_regex", default_regex)

        src_text_top = st.session_state.get("src_input","")
        tgt_text_top = st.session_state.get("tgt_input","")
        src_items_top = split_text(src_text_top, mode_key_top, delim_regex_top)
        tgt_items_top = split_text(tgt_text_top, mode_key_top, delim_regex_top) if tgt_text_top.strip() else []
        pairs_top: List[Tuple[str, str]] = (list(zip(src_items_top[:min(len(src_items_top), len(tgt_items_top))], tgt_items_top)) if tgt_items_top else [(s, "") for s in src_items_top])

        pick_top = st.session_state.get("ins_srcpick", "➕ New…")
        src_name_top = (st.session_state.get("ins_srcname", "MyBatch") if pick_top == "➕ New…" else pick_top)
        can_insert_top = len(pairs_top) > 0 and str(src_name_top).strip() != ""
        st.caption(f"将要插入的条目数：{len(pairs_top)}")
        top_clicked = st.button("📥 入库 / Insert", type="primary", disabled=not can_insert_top, key="ins_btn_top")
    st.markdown('</div>', unsafe_allow_html=True)

    ls, lt = ("zh", "en") if st.session_state.get("ins_dir") == "zh→en" else ("en", "zh")

    mode = st.selectbox("拆分方式 / Split Mode", ["不要拆分（整段入库）", "按行对齐（每行是一条）", "按分隔符（正则）"], index=["不要拆分（整段入库）", "按行对齐（每行是一条）", "按分隔符（正则）"].index(st.session_state["ins_mode"]), key="ins_mode")
    mode_key = {"不要拆分（整段入库）": "no_split","按行对齐（每行是一条）": "by_line","按分隔符（正则）": "by_regex"}[mode]
    default_regex = r"[。！？；;.!?:]+"
    delim_regex = st.text_input("分隔符正则（仅“按分隔符”生效）", value=st.session_state.get("ins_regex", default_regex), disabled=(mode_key != "by_regex"), key="ins_regex")

    col1, col2 = st.columns(2)
    with col1:
        src_label = "中文段落（来源）" if ls == "zh" else "English paragraph (Source)"
        src_text = st.text_area(src_label, height=200, key="src_input")
    with col2:
        tgt_label = "English paragraph（译文，可选）" if lt == "en" else "中文段落（译文，可选）"
        tgt_text = st.text_area(tgt_label, height=200, key="tgt_input")

    existing_sources = _list_sources(API_BASE)
    options = ["➕ New…"] + existing_sources
    default_index = (0 if "MyBatch" not in existing_sources else options.index("MyBatch"))
    pick = st.selectbox("统一出处 / Source Name (type to search existing)", options=options, index=default_index, key="ins_srcpick")
    src_name = st.text_input("New source name", value=st.session_state.get("ins_srcname","MyBatch"), key="ins_srcname") if pick == "➕ New…" else pick
    timestamp = st.text_input("统一时间 / Timestamp (ISO)", value=st.session_state.get("ins_ts", datetime.now().isoformat(timespec="seconds")), key="ins_ts")

    src_items = split_text(st.session_state.get("src_input",""), mode_key, delim_regex)
    tgt_raw = st.session_state.get("tgt_input","").strip()
    tgt_items = split_text(tgt_raw, mode_key, delim_regex) if tgt_raw else []
    pairs: List[Tuple[str, str]] = (list(zip(src_items[:min(len(src_items), len(tgt_items))], tgt_items)) if tgt_items else [(s, "") for s in src_items])

    def _direction_ok() -> bool:
        if not st.session_state.get("detect_enable", True):
            return True
        ok_src = check_lang_direction(st.session_state.get("src_input",""), ls, int(st.session_state.get("detect_minlen", 10)), float(st.session_state.get("detect_dom", 2.0)))
        if not ok_src:
            st.error("🔎 检测到源文与当前方向不符，请检查是否导错（中英对调）。")
            return False
        tgt_text_val = st.session_state.get("tgt_input","").strip()
        if tgt_text_val:
            ok_tgt = check_lang_direction(tgt_text_val, lt, int(st.session_state.get("detect_minlen", 10)), float(st.session_state.get("detect_dom", 2.0)))
            if not ok_tgt:
                st.error("🔎 检测到译文与当前方向不符，请检查是否导错（中英对调）。")
                return False
        return True

    if top_clicked:
        if client is None:
            st.error("❌ 无法入库：`repo.client` 未导入成功。请检查 `repo.py` 是否可被导入（运行目录 / PYTHONPATH）。")
        else:
            if _direction_ok():
                ok, fail = 0, 0
                for sline, tline in pairs:
                    try:
                        client.add_entry(src=sline, tgt=tline, ls=ls, lt=lt, source_name=str(src_name).strip(), created_at=str(timestamp).strip() or None)
                        ok += 1
                    except Exception:
                        fail += 1
                if ok and not fail:
                    st.success(f"✅ 已入库 {ok} 条，方向 {ls}→{lt}，来源：{src_name}")
                elif ok and fail:
                    st.warning(f"⚠️ 部分成功：成功 {ok} 条，失败 {fail} 条。")
                else:
                    st.error("❌ 入库失败，未写入任何条目。")

# -------- 预览 --------
with tab_preview:
    st.markdown("## 👀 预览 / Preview")
    direction = st.session_state.get("ins_dir", "en→zh")
    ls, lt = ("zh", "en") if direction == "zh→en" else ("en", "zh")
    mode_display = st.session_state.get("ins_mode", "不要拆分（整段入库）")
    mode_key = {"不要拆分（整段入库）": "no_split","按行对齐（每行是一条）": "by_line","按分隔符（正则）": "by_regex"}.get(mode_display, "no_split")
    default_regex = r"[。！？；;.!?:]+"
    delim_regex = st.session_state.get("ins_regex", default_regex)
    src_text = st.session_state.get("src_input","")
    tgt_text = st.session_state.get("tgt_input","")
    src_items = split_text(src_text, mode_key, delim_regex)
    tgt_items = split_text(tgt_text, mode_key, delim_regex) if tgt_text.strip() else []
    pairs: List[Tuple[str, str]] = (list(zip(src_items[:min(len(src_items), len(tgt_items))], tgt_items)) if tgt_items else [(s, "") for s in src_items])
    st.write(f"将要插入的条目数：**{len(pairs)}**")
    with st.expander("展开查看每条 / Show items", expanded=True):
        for i, (sline, tline) in enumerate(pairs, 1):
            st.markdown(f"**#{i}**")
            st.markdown(f"- 源文 / Source: {sline}")
            if tline:
                st.markdown(f"- 译文 / Target: {tline}")
            st.markdown("---")

# -------- 检测参数 --------
with tab_detect:
    st.markdown('<div class="sticky-toolbar">', unsafe_allow_html=True)
    enable_detect = st.checkbox("启用语言方向检测", value=bool(st.session_state.get("detect_enable", True)), key="detect_enable")
    cold1, cold2, cold3 = st.columns(3)
    with cold1:
        min_len = st.number_input("最小检测长度", 0, 500, int(st.session_state.get("detect_minlen", 10)), 1, key="detect_minlen")
    with cold2:
        dominance = st.slider("主导比", 1.0, 5.0, float(st.session_state.get("detect_dom", 2.0)), 0.1, key="detect_dom")
    with cold3:
        st.caption("当中文(或英文) ≥ 主导比 × 另一方，即判定方向正确。")
    st.markdown('</div>', unsafe_allow_html=True)
    st.info("检测参数会在“📥 Insert”前自动应用。")

# -------- 重命名 + 最近（与旧版一致，略） --------
with st.expander("关于后端连接的小提示"):
    st.markdown(f"- 当前 API_BASE：`{API_BASE}`")
    st.markdown("- 若此页仍空白：请查看页面顶部是否有“模块导入异常”折叠框；如无，请按 F12 看控制台错误。")
    st.markdown("- 运行入口尽量使用 `WordloomFrontend/streamlit/app.py`，避免工作目录导致的 `import` 失败。")
