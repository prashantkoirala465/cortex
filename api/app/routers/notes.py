import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Note
from app.schemas import NoteCreate, NoteRead, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=list[NoteRead])
def list_notes(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)) -> list[Note]:
    stmt = select(Note).order_by(Note.updated_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.post("", response_model=NoteRead, status_code=201)
def create_note(body: NoteCreate, db: Session = Depends(get_db)) -> Note:
    note = Note(title=body.title, content=body.content)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def _get_note_or_404(note_id: uuid.UUID, db: Session) -> Note:
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="note not found")
    return note


@router.get("/{note_id}", response_model=NoteRead)
def get_note(note_id: uuid.UUID, db: Session = Depends(get_db)) -> Note:
    return _get_note_or_404(note_id, db)


@router.patch("/{note_id}", response_model=NoteRead)
def update_note(note_id: uuid.UUID, body: NoteUpdate, db: Session = Depends(get_db)) -> Note:
    note = _get_note_or_404(note_id, db)
    if body.title is not None:
        note.title = body.title
    if body.content is not None:
        note.content = body.content
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    note = _get_note_or_404(note_id, db)
    db.delete(note)
    db.commit()
