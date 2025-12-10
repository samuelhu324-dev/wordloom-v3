
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class EntryCreate(BaseModel):
    src: str = Field(..., description="source text")
    tgt: str = Field("", description="target text (optional)")
    ls: str = "zh"
    lt: str = "en"
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    created_at: Optional[str] = None  # ISO string

class EntryOut(BaseModel):
    id: int
    src_text: str
    tgt_text: str
    lang_src: str
    lang_tgt: str
    created_at: datetime
    source_name: Optional[str] = None

class SourceOut(BaseModel):
    id: int
    name: str

class RenameSourceIn(BaseModel):
    old: str
    new: str

class LoginIn(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
