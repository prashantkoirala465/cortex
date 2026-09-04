import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.extraction import enqueue_extraction
from app.models import ExtractionJob, Note, User
from app.schemas import ExtractionJobRead, NoteCreate, NoteRead, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=list[NoteRead])
def list_notes(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Note]:
    stmt = (
        select(Note)
        .where(Note.user_id == current_user.id)
        .order_by(Note.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt))


@router.post("", response_model=NoteRead, status_code=201)
def create_note(
    body: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Note:
    note = Note(title=body.title, content=body.content, user_id=current_user.id)
    db.add(note)
    db.commit()
    db.refresh(note)
    enqueue_extraction(db, note)
    return note


def _get_owned_note_or_404(note_id: uuid.UUID, current_user: User, db: Session) -> Note:
    note = db.get(Note, note_id)
    # 404 (not 403) for notes owned by someone else, so we don't leak which ids exist
    if note is None or note.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="note not found")
    return note


@router.get("/{note_id}", response_model=NoteRead)
def get_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Note:
    return _get_owned_note_or_404(note_id, current_user, db)


@router.patch("/{note_id}", response_model=NoteRead)
def update_note(
    note_id: uuid.UUID,
    body: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Note:
    note = _get_owned_note_or_404(note_id, current_user, db)
    changed = body.title is not None or body.content is not None
    if body.title is not None:
        note.title = body.title
    if body.content is not None:
        note.content = body.content
    db.commit()
    db.refresh(note)
    if changed:
        enqueue_extraction(db, note)
    return note


@router.delete("/{note_id}", status_code=204)
def delete_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    note = _get_owned_note_or_404(note_id, current_user, db)
    db.delete(note)
    db.commit()


@router.post("/{note_id}/process", response_model=ExtractionJobRead, status_code=202)
def trigger_processing(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExtractionJob:
    note = _get_owned_note_or_404(note_id, current_user, db)
    return enqueue_extraction(db, note)


@router.get("/{note_id}/job", response_model=ExtractionJobRead | None)
def get_latest_job(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExtractionJob | None:
    note = _get_owned_note_or_404(note_id, current_user, db)
    return db.scalar(
        select(ExtractionJob)
        .where(ExtractionJob.note_id == note.id)
        .order_by(ExtractionJob.created_at.desc())
    )
