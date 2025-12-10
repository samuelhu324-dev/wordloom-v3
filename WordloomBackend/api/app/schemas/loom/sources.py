from __future__ import annotations
from pydantic import BaseModel

class SourceOut(BaseModel):
    id: int
    name: str

class RenameSourceIn(BaseModel):
    old: str
    new: str

class RenameReq(BaseModel):
    from_name: str
    to_name: str
    preview: bool = True
