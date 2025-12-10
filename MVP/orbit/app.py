import streamlit as st

st.set_page_config(page_title="Orbit · MVP", page_icon="🛰️", layout="wide")
st.title("🛰️ Orbit · MVP")
st.write("超轻量原型：Memos / Tasks / Stats —— 先跑起来，后续再扩。")
st.page_link("pages/01_Memos.py", label="进入 Memos", icon="📝")
st.page_link("pages/02_Tasks.py", label="进入 Tasks", icon="✅")
st.page_link("pages/03_Stats.py", label="进入 Stats", icon="📈")
st.divider()
st.caption("SQLite 本地存储 · 统一导入导出 JSON · 与 Wordloom 的 Loom 模块无冲突（独立命名空间）")
