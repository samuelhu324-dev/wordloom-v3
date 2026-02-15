from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple


def _parse_todo_list_items(content: Optional[str]) -> Optional[Dict[str, Dict[str, Any]]]:
    if content is None:
        return None
    if not isinstance(content, str) or not content.strip():
        return None

    try:
        data = json.loads(content)
    except Exception:
        return None

    items: Any = None
    if isinstance(data, dict):
        items = data.get("items")
    elif isinstance(data, list):
        items = data

    if not isinstance(items, list):
        return None

    normalized: Dict[str, Dict[str, Any]] = {}
    for index, raw in enumerate(items):
        if not isinstance(raw, dict):
            continue
        todo_id = raw.get("id")
        todo_id_str = str(todo_id) if todo_id is not None else ""
        text = raw.get("text")
        text_str = str(text) if text is not None else None
        checked = bool(raw.get("checked"))
        promoted = bool(raw.get("isPromoted"))

        key = todo_id_str or f"{index}:{text_str or ''}"
        normalized[key] = {
            "todo_id": todo_id_str or None,
            "text": text_str,
            "checked": checked,
            "promoted": promoted,
        }

    return normalized


def diff_todo_list_facts(
    *,
    old_content: Optional[str],
    new_content: Optional[str],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Compute stable TODO facts from a todo_list block content change.

    Returns:
        (promoted_events, completed_events)

    promoted_events items: {todo_id, text, is_urgent}
    completed_events items: {todo_id, text, promoted}

    Notes:
        - Only emits transitions to promoted/checked.
        - Ignores uncheck/unpromote transitions for now (can be added later).
        - If parsing fails, returns empty lists.
    """

    old_items = _parse_todo_list_items(old_content) or {}
    new_items = _parse_todo_list_items(new_content) or {}

    promoted: List[Dict[str, Any]] = []
    completed: List[Dict[str, Any]] = []

    for key, new_item in new_items.items():
        old_item = old_items.get(key)
        old_promoted = bool(old_item.get("promoted")) if old_item else False
        old_checked = bool(old_item.get("checked")) if old_item else False

        if not old_promoted and bool(new_item.get("promoted")):
            promoted.append(
                {
                    "todo_id": new_item.get("todo_id"),
                    "text": new_item.get("text"),
                    "is_urgent": None,
                }
            )

        if not old_checked and bool(new_item.get("checked")):
            completed.append(
                {
                    "todo_id": new_item.get("todo_id"),
                    "text": new_item.get("text"),
                    "promoted": bool(new_item.get("promoted")),
                }
            )

    return promoted, completed
