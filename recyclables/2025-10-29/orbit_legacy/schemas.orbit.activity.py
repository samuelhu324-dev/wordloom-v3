# WordloomBackend/api/app/schemas/orbit/activity.py
import uuid
from typing import Optional
from pydantic import BaseModel

class ActivityRead(BaseModel):
    id: uuid.UUID
    bookmark_id: uuid.UUID
    action: str
    meta: Optional[dict] = None
    ts: str

    class Config:
        from_attributes = True
