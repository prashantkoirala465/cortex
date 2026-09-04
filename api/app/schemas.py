import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NoteCreate(BaseModel):
    title: str = ""
    content: dict = {}


class NoteUpdate(BaseModel):
    title: str | None = None
    content: dict | None = None


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    content: dict
    created_at: datetime
    updated_at: datetime
