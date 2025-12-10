"""
text_utils.py — Unified sentence segmentation toolkit (local-model enabled)
"""

import os
import re
from typing import List

PROTECT_MARK = "<DOT>"
FILE_EXT = r"(jpg|jpeg|png|gif|bmp|webp|pdf|docx?|xlsx?|pptx?|zip|rar|7z|txt|html?)"
ABBR = r"(Mr|Ms|Mrs|Dr|Prof|Sr|Jr|vs|etc|e\.g|i\.e)"
NUM = r"\b\d+\.\d+\b"  # 小数

# ---------------------------------------------------------------------------
# 规则分句（基础可用，无依赖）
# ---------------------------------------------------------------------------

def _protect(text: str) -> str:
    text = re.sub(rf"\.({FILE_EXT})\b", rf"{PROTECT_MARK}\1", text, flags=re.I)
    text = re.sub(rf"\b{ABBR}", lambda m: m.group(0).replace(".", PROTECT_MARK), text, flags=re.I)
    text = re.sub(NUM, lambda m: m.group(0).replace(".", PROTECT_MARK), text)
    return text

def _unprotect(text: str) -> str:
    return text.replace(PROTECT_MARK, ".")

def rule_split_sentences(text: str) -> List[str]:
    if not text:
        return []
    t = _protect(text)
    parts = re.split(r"(?<=[。！？!?\.])\s*", t)
    parts = [_unprotect(p).strip() for p in parts if p and p.strip()]
    return parts

# ---------------------------------------------------------------------------
# Stanza 分句 — 支持本地模型目录 stanza_resources/
# ---------------------------------------------------------------------------

def stanza_split(text: str, lang: str = "auto") -> List[str]:
    try:
        import stanza
    except ImportError:
        print("[text_utils] stanza not installed, fallback to rule mode.")
        return rule_split_sentences(text)

    # 优先设置本地资源目录
    if os.path.isdir("stanza_resources"):
        os.environ["STANZA_RESOURCES_DIR"] = "stanza_resources"

    if lang == "auto":
        zh_ratio = sum("\u4e00" <= ch <= "\u9fff" for ch in text) / max(1, len(text))
        lang = "zh" if zh_ratio > 0.1 else "en"

    try:
        nlp = stanza.Pipeline(lang, processors="tokenize", tokenize_no_ssplit=False)
        doc = nlp(text)
        return ["".join(t.text for t in s.tokens).strip() for s in doc.sentences]
    except Exception as e:
        print(f"[text_utils] stanza error: {e}, fallback to rule mode.")
        return rule_split_sentences(text)

# ---------------------------------------------------------------------------
# spaCy 分句 — 支持本地模型目录 models/en_core_web_sm/
# ---------------------------------------------------------------------------

def spacy_split(text: str) -> List[str]:
    try:
        import spacy
    except ImportError:
        print("[text_utils] spacy not installed, fallback to rule mode.")
        return rule_split_sentences(text)

    from pathlib import Path
    nlp = None
    local_model_path = Path("models/en_core_web_sm")
    try:
        if local_model_path.exists():
            print("[text_utils] Loading spaCy model from local path:", local_model_path)
            nlp = spacy.util.load_model_from_path(local_model_path)
        else:
            print("[text_utils] Using system-installed spaCy model.")
            nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        print(f"[text_utils] spaCy model load failed: {e}")
        return rule_split_sentences(text)

    if "parser" in nlp.pipe_names:
        nlp.remove_pipe("parser")
    nlp.add_pipe("sentencizer")

    FILE_EXT_RE = re.compile(r"\.(jpg|jpeg|png|gif|pdf|docx|xls|zip|rar|txt)\b", re.I)

    def protect_file_ext(doc):
        prev = None
        for token in doc:
            if prev and prev.text == "." and FILE_EXT_RE.match(prev.text_with_ws + token.text):
                token.is_sent_start = False
            prev = token
        return doc

    nlp.add_pipe(protect_file_ext, name="protect_file_ext", last=True)
    return [s.text.strip() for s in nlp(text).sents]

# ---------------------------------------------------------------------------
# 统一接口
# ---------------------------------------------------------------------------

def segment_text(text: str, engine: str = "rule", lang: str = "auto") -> List[str]:
    """
    engine: 'rule' | 'stanza' | 'spacy'
    lang  : 'zh' | 'en' | 'auto'
    """
    text = text or ""
    engine = engine.lower()
    if engine == "stanza":
        return stanza_split(text, lang)
    elif engine == "spacy":
        return spacy_split(text)
    else:
        return rule_split_sentences(text)

if __name__ == "__main__":
    sample = "Dr. Smith loves cats. 文件 example.jpg 很漂亮。圆周率是3.14。U.S.A. 是国家。"
    for e in ["rule", "stanza", "spacy"]:
        print(f"\n[{e}] →", segment_text(sample, e))
