from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel

class EntryOut(BaseModel):
    id: int
    src: str = ""
    tgt: str = ""
    source_name: Optional[str] = None
    created_at: Optional[str] = None

class EntryCreate(BaseModel):
    src: str
    tgt: str
    source_name: Optional[str] = None
    created_at: Optional[str] = None

class EntryPatch(BaseModel):
    src: Optional[str] = None
    tgt: Optional[str] = None
    source_name: Optional[str] = None
    created_at: Optional[str] = None

class BatchItem(BaseModel):
    text: str
    translation: Optional[str] = None
    direction: str                # "en>zh" | "zh>en"
    source_name: Optional[str] = None
    ts_iso: Optional[str] = None

class BatchCreate(BaseModel):
    items: List[BatchItem]

class AssignSourceReq(BaseModel):
    source_name: str
    entry_ids: Optional[List[int]] = None
    only_unlinked: bool = True
