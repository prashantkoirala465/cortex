from fastapi import APIRouter, Depends, Query
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.llm import get_llm_provider
from app.models import Note, NoteChunk, User
from app.schemas import SearchResult

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[SearchResult])
def search_notes(
    q: str = Query(min_length=1),
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SearchResult]:
    has_chunks = db.scalar(
        select(
            exists().where(NoteChunk.note_id == Note.id, Note.user_id == current_user.id)
        )
    )
    if not has_chunks:
        return []

    query_embedding = get_llm_provider().embed([q])[0]
    distance = NoteChunk.embedding.cosine_distance(query_embedding).label("distance")

    stmt = (
        select(NoteChunk, Note.title, distance)
        .join(Note, Note.id == NoteChunk.note_id)
        .where(Note.user_id == current_user.id)
        .order_by(distance)
        .limit(limit * 3)  # over-fetch since multiple chunks can share a note
    )

    results: list[SearchResult] = []
    seen_notes: set = set()
    for chunk, title, dist in db.execute(stmt).all():
        if chunk.note_id in seen_notes:
            continue
        seen_notes.add(chunk.note_id)
        results.append(
            SearchResult(
                note_id=chunk.note_id,
                title=title,
                snippet=chunk.content[:280],
                score=round(1 - dist, 4),
            )
        )
        if len(results) >= limit:
            break

    return results
