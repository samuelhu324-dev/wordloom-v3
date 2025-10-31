# repo.py — Frontend API Client (Streamlit 调用 FastAPI)
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import os, time
import requests

from app import API_BASE  # 使用你轻量 app.py 暴露的 API_BASE

# === 可按需微调：后端路由路径 ===
ENDPOINTS = {
    "search":        "/entries/search",
    "entries":       "/entries",
    "entry_id":      "/entries/{entry_id}",
    "articles":      "/articles",
    "article_sents": "/articles/{article_id}/sentences",
    "article_insert":"/articles/{article_id}/insert",
    "find_matches":  "/ops/find-matches",
    "bulk_replace":  "/ops/bulk-replace",
}

class ApiError(RuntimeError):
    pass

class ApiClient:
    def __init__(self, api_base: Optional[str] = None, token: Optional[str] = None, timeout: int = 20):
        self.base = (api_base or API_BASE).rstrip("/")
        # 支持在 .env 里注入 WORDLOOM_TOKEN（可选）
        self.token = token or os.getenv("WORDLOOM_TOKEN")
        self.timeout = timeout

    # ---------- low-level ----------
    def _headers(self) -> Dict[str, str]:
        h = {"Accept": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _url(self, key: str, **path_vars) -> str:
        path = ENDPOINTS[key].format(**path_vars)
        return f"{self.base}{path}"

    def _get(self, key: str, *, params: Dict[str, Any] | None = None, **path_vars):
        r = requests.get(self._url(key, **path_vars), params=params or {}, headers=self._headers(), timeout=self.timeout)
        if r.status_code >= 400:
            raise ApiError(f"GET {r.url} -> {r.status_code}: {r.text}")
        return r.json()

    def _post(self, key: str, json: Dict[str, Any], **path_vars):
        r = requests.post(self._url(key, **path_vars), json=json, headers=self._headers(), timeout=self.timeout)
        if r.status_code >= 400:
            raise ApiError(f"POST {r.url} -> {r.status_code}: {r.text}")
        return r.json()

    def _put(self, key: str, json: Dict[str, Any], **path_vars):
        r = requests.put(self._url(key, **path_vars), json=json, headers=self._headers(), timeout=self.timeout)
        if r.status_code >= 400:
            raise ApiError(f"PUT {r.url} -> {r.status_code}: {r.text}")
        return r.json()

    def _delete(self, key: str, **path_vars):
        r = requests.delete(self._url(key, **path_vars), headers=self._headers(), timeout=self.timeout)
        if r.status_code >= 400:
            raise ApiError(f"DELETE {r.url} -> {r.status_code}: {r.text}")
        # 兼容无返回体
        return r.json() if r.content else {"ok": True}

    # ---------- high-level: 与你原 repo.py 能力对齐 ----------
    # 基础检索
    def search(self, q: str, *, ls: Optional[str]=None, lt: Optional[str]=None,
               source_names: Optional[List[str]]=None,
               limit: int = 50, offset: int = 0,
               date_from: Optional[str]=None, date_to: Optional[str]=None) -> List[dict]:
        params = {
            "q": q, "ls": ls, "lt": lt, "limit": limit, "offset": offset,
            "date_from": date_from, "date_to": date_to
        }
        if source_names:
            # 常见写法：多值参数重复或逗号分隔。后端若用 Pydantic List[str]，重复参数更稳。
            for i, name in enumerate(source_names):
                params[f"source_names[{i}]"] = name
        return self._get("search", params=params)

    # 单条增删改
    def add_entry(self, *, src: str, tgt: str, ls="zh", lt="en",
                  source_name: Optional[str]=None, source_url: Optional[str]=None,
                  created_at: Optional[str]=None) -> int:
        payload = {"src": src, "tgt": tgt, "ls": ls, "lt": lt,
                   "source_name": source_name, "source_url": source_url, "created_at": created_at}
        data = self._post("entries", json=payload)
        return int(data.get("id") or data)

    def update_entry(self, entry_id: int, **fields) -> int:
        data = self._put("entry_id", json=fields, entry_id=entry_id)
        return int(data.get("id") or entry_id)

    def delete_entry(self, entry_id: int) -> bool:
        self._delete("entry_id", entry_id=entry_id)
        return True

    # 文章/句子相关
    def create_article(self, title: str, source_name: Optional[str]=None) -> int:
        data = self._post("articles", json={"title": title, "source_name": source_name})
        return int(data.get("id") or data)

    def get_article_sentences(self, article_id: int) -> List[dict]:
        return self._get("article_sents", article_id=article_id)

    def insert_sentence(self, article_id: int, after_position: int, src: str, tgt: str,
                        ls="zh", lt="en", source_name: Optional[str]=None,
                        created_at: Optional[str]=None) -> int:
        payload = {"after_position": after_position, "src": src, "tgt": tgt, "ls": ls, "lt": lt,
                   "source_name": source_name, "created_at": created_at}
        data = self._post("article_insert", json=payload, article_id=article_id)
        return int(data.get("id") or data)

    # 批量：查找与替换
    def find_matches(self, keyword: str, *, scope: str="both", source_name: Optional[str]=None,
                     date_from: Optional[str]=None, date_to: Optional[str]=None, limit: int=200,
                     regex_mode: bool=False, case_sensitive: bool=False, strict_word: bool=False) -> List[dict]:
        payload = {"keyword": keyword, "scope": scope, "source_name": source_name,
                   "date_from": date_from, "date_to": date_to, "limit": limit,
                   "regex_mode": regex_mode, "case_sensitive": case_sensitive, "strict_word": strict_word}
        return self._post("find_matches", json=payload)

    def bulk_replace(self, keyword: str, replacement: str, *, scope: str="both",
                     source_name: Optional[str]=None, date_from: Optional[str]=None, date_to: Optional[str]=None,
                     regex_mode: bool=False, case_sensitive: bool=False, strict_word: bool=False,
                     first_only: bool=False) -> int:
        payload = {"keyword": keyword, "replacement": replacement, "scope": scope,
                   "source_name": source_name, "date_from": date_from, "date_to": date_to,
                   "regex_mode": regex_mode, "case_sensitive": case_sensitive, "strict_word": strict_word,
                   "first_only": first_only}
        data = self._post("bulk_replace", json=payload)
        return int(data.get("changed") or data)

# 便捷单例（页面里直接用）
client = ApiClient()
