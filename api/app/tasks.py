import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.llm import get_llm_provider
from app.models import Entity, ExtractionJob, JobStatus, Note, NoteChunk, NoteEntity, Relationship
from app.text import chunk_text, render_plain_text

# small local models lose coherence on very long inputs, and this keeps
# each extraction call fast on constrained hardware
MAX_EXTRACTION_CHARS = 6000


def _now():
    return datetime.now(timezone.utc)


def process_note(note_id: str, job_id: str, db: Session | None = None) -> None:
    """The RQ worker calls this with no `db`, so it opens its own session
    (it runs in a separate process from the API). Tests pass one in so the
    whole run stays inside their transactional-savepoint isolation."""
    owns_session = db is None
    if db is None:
        db = SessionLocal()
    try:
        job = db.get(ExtractionJob, job_id)
        if job is None or job.status == JobStatus.cancelled.value:
            return

        job.status = JobStatus.running.value
        job.started_at = _now()
        db.commit()

        note = db.get(Note, note_id)
        if note is None:
            job.status = JobStatus.failed.value
            job.error = "note no longer exists"
            job.finished_at = _now()
            db.commit()
            return

        # this run replaces whatever the previous run for this note produced
        db.execute(delete(NoteChunk).where(NoteChunk.note_id == note.id))
        db.execute(delete(NoteEntity).where(NoteEntity.note_id == note.id))
        db.execute(delete(Relationship).where(Relationship.note_id == note.id))
        db.commit()

        text = render_plain_text(note.content)
        if not text.strip():
            job.status = JobStatus.succeeded.value
            job.finished_at = _now()
            db.commit()
            return

        provider = get_llm_provider()

        for index, chunk in enumerate(chunk_text(text)):
            embedding = provider.embed([chunk])[0]
            db.add(NoteChunk(note_id=note.id, chunk_index=index, content=chunk, embedding=embedding))

        result = provider.extract(text[:MAX_EXTRACTION_CHARS])

        entity_by_name: dict[str, Entity] = {}
        mentioned_entity_ids: set[uuid.UUID] = set()
        for extracted in result.entities:
            name = extracted.name.strip()
            if not name:
                continue

            entity = entity_by_name.get(name)
            if entity is None:
                entity = db.scalar(
                    select(Entity).where(Entity.user_id == note.user_id, Entity.name == name)
                )
                if entity is None:
                    entity = Entity(user_id=note.user_id, name=name, type=extracted.type)
                    db.add(entity)
                    db.flush()
                entity_by_name[name] = entity

            if entity.id not in mentioned_entity_ids:
                db.add(NoteEntity(note_id=note.id, entity_id=entity.id))
                mentioned_entity_ids.add(entity.id)

        seen_edges: set[tuple[uuid.UUID, uuid.UUID, str]] = set()
        for rel in result.relationships:
            source = entity_by_name.get(rel.source.strip())
            target = entity_by_name.get(rel.target.strip())
            if source is None or target is None:
                continue

            edge_key = (source.id, target.id, rel.label)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)

            db.add(
                Relationship(
                    user_id=note.user_id,
                    source_entity_id=source.id,
                    target_entity_id=target.id,
                    label=rel.label,
                    note_id=note.id,
                )
            )

        job.status = JobStatus.succeeded.value
        job.finished_at = _now()
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.get(ExtractionJob, job_id)
        if job is not None:
            job.status = JobStatus.failed.value
            job.error = str(exc)[:2000]
            job.finished_at = _now()
            db.commit()
        raise
    finally:
        if owns_session:
            db.close()
