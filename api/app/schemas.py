import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    created_at: datetime


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


class ExtractionJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class NoteRef(BaseModel):
    id: uuid.UUID
    title: str


class GraphNode(BaseModel):
    id: uuid.UUID
    name: str
    type: str | None
    notes: list[NoteRef]


class GraphEdge(BaseModel):
    id: uuid.UUID
    source: uuid.UUID
    target: uuid.UUID
    label: str
    note_id: uuid.UUID


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
