from fastapi import APIRouter, Depends
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.llm import get_llm_provider
from app.models import Note, NoteChunk, User
from app.relevance import MAX_RELEVANT_DISTANCE
from app.schemas import ChatRequest, ChatResponse, NoteRef

router = APIRouter(prefix="/chat", tags=["chat"])

CONTEXT_CHUNK_LIMIT = 8
HISTORY_TURN_LIMIT = 6

SYSTEM_PROMPT = """You are a helpful assistant answering questions using ONLY the user's own \
notes provided below as context. If the notes don't contain the answer, say so honestly instead \
of making something up. Keep answers concise and direct.

Notes:
{context}"""


@router.post("", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    has_chunks = db.scalar(
        select(exists().where(NoteChunk.note_id == Note.id, Note.user_id == current_user.id))
    )
    if not has_chunks:
        return ChatResponse(
            answer="You don't have any processed notes yet, so I have nothing to answer from.",
            sources=[],
        )

    provider = get_llm_provider()
    query_embedding = provider.embed([body.question])[0]
    distance = NoteChunk.embedding.cosine_distance(query_embedding).label("distance")

    stmt = (
        select(NoteChunk, Note.id, Note.title, distance)
        .join(Note, Note.id == NoteChunk.note_id)
        .where(Note.user_id == current_user.id)
        .order_by(distance)
        .limit(CONTEXT_CHUNK_LIMIT)
    )
    rows = [row for row in db.execute(stmt).all() if row.distance <= MAX_RELEVANT_DISTANCE]

    if not rows:
        return ChatResponse(answer="I couldn't find anything relevant in your notes.", sources=[])

    context = "\n\n---\n\n".join(f"[{title}]\n{chunk.content}" for chunk, _note_id, title, _dist in rows)

    sources: dict = {}
    for _chunk, note_id, title, _dist in rows:
        sources.setdefault(note_id, title)

    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(context=context)}]
    for turn in body.history[-HISTORY_TURN_LIMIT:]:
        messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": body.question})

    answer = provider.chat(messages)

    return ChatResponse(
        answer=answer,
        sources=[NoteRef(id=note_id, title=title) for note_id, title in sources.items()],
    )
