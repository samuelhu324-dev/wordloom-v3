import os
API_BASE = os.getenv("WORDLOOM_API_BASE", "http://127.0.0.1:8000")

import streamlit as st
from pathlib import Path

# 自动找到 VERSION 文件位置（兼容你现在的结构）
version_file = Path(__file__).resolve().parent / "VERSION"
if not version_file.exists():
    version_file = Path(__file__).resolve().parents[1] / "VERSION"

try:
    version = version_file.read_text(encoding="utf-8").strip()
except Exception:
    version = "unknown"

st.markdown(
    f"<hr><div style='text-align:center;color:gray;font-size:12px;'>"
    f"<i>Wordloom Frontend v{version}</i></div>",
    unsafe_allow_html=True
)
