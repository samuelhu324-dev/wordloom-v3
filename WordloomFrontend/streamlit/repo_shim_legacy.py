# repo_shim_legacy.py — 让旧 API 客户端适配到 DataService 接口
from __future__ import annotations
from typing import Iterable, List, Dict, Any, Tuple, Optional

# 旧 repo_legacy 里应该有 ApiClient 或 client 实例
from repo_legacy import client

class LegacyAdapter:
    """把旧 API 客户端包装成 DataService 接口。"""

    def search(self, q: str, limit: int = 50, offset: int = 0, **kwargs) -> List[Dict[str, Any]]:
        return client.search(
            q=q,
            limit=limit,
            offset=offset,
            ls=kwargs.get("ls"),
            lt=kwargs.get("lt"),
            source_names=kwargs.get("source_names"),
            date_from=kwargs.get("date_from"),
            date_to=kwargs.get("date_to"),
        )

    def list_sources(self) -> List[str]:
        try:
            return []
        except Exception:
            return []

    def get_source_items(self, source_name: str, limit: int = 200, offset: int = 0) -> List[Dict[str, Any]]:
        raise NotImplementedError("repo_legacy 暂未实现 get_source_items")

    def insert_item(self, item: Dict[str, Any]) -> int:
        return client.add_entry(
            src=item.get("src") or item.get("src_text", ""),
            tgt=item.get("tgt") or item.get("tgt_text", ""),
            ls=item.get("ls") or item.get("lang_src", "zh"),
            lt=item.get("lt") or item.get("lang_tgt", "en"),
            source_name=item.get("source_name"),
        )

    def update_item(self, item_id: int, patch: Dict[str, Any]) -> None:
        fields = {}
        if "src" in patch or "src_text" in patch:
            fields["src"] = patch.get("src") or patch.get("src_text")
        if "tgt" in patch or "tgt_text" in patch:
            fields["tgt"] = patch.get("tgt") or patch.get("tgt_text")
        if "ls" in patch or "lang_src" in patch:
            fields["ls"] = patch.get("ls") or patch.get("lang_src")
        if "lt" in patch or "lang_tgt" in patch:
            fields["lt"] = patch.get("lt") or patch.get("lang_tgt")
        if "source_name" in patch:
            fields["source_name"] = patch["source_name"]
        if fields:
            client.update_entry(item_id, **fields)

    def delete_item(self, item_id: int) -> None:
        client.delete_entry(item_id)

    def bulk_insert(self, rows: Iterable[Dict[str, Any]]) -> Tuple[int, List[str]]:
        ok, errs = 0, []
        for i, r in enumerate(rows, 1):
            try:
                self.insert_item(r)
                ok += 1
            except Exception as e:
                errs.append(f"row#{i}: {e}")
        return ok, errs


def get_data_service() -> LegacyAdapter:
    """统一导出接口"""
    return LegacyAdapter()
