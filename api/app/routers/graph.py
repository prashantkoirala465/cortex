from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Entity, Note, NoteEntity, Relationship, User
from app.schemas import GraphEdge, GraphNode, GraphResponse, NoteRef

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("", response_model=GraphResponse)
def get_graph(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GraphResponse:
    entities = list(db.scalars(select(Entity).where(Entity.user_id == current_user.id)))
    entity_ids = [e.id for e in entities]

    notes_by_entity: dict[object, list[NoteRef]] = defaultdict(list)
    if entity_ids:
        mentions = db.execute(
            select(NoteEntity.entity_id, Note.id, Note.title)
            .join(Note, Note.id == NoteEntity.note_id)
            .where(NoteEntity.entity_id.in_(entity_ids))
        ).all()
        for entity_id, note_id, title in mentions:
            notes_by_entity[entity_id].append(NoteRef(id=note_id, title=title))

    relationships = list(
        db.scalars(select(Relationship).where(Relationship.user_id == current_user.id))
    )

    return GraphResponse(
        nodes=[
            GraphNode(id=e.id, name=e.name, type=e.type, notes=notes_by_entity.get(e.id, []))
            for e in entities
        ],
        edges=[
            GraphEdge(
                id=r.id,
                source=r.source_entity_id,
                target=r.target_entity_id,
                label=r.label,
                note_id=r.note_id,
            )
            for r in relationships
        ],
    )
