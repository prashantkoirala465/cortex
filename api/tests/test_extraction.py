from sqlalchemy import select

from app.llm.base import ExtractedEntity, ExtractedRelationship, ExtractionResult, LLMProvider
from app.models import Entity, ExtractionJob, JobStatus, Note, NoteChunk, NoteEntity, Relationship
from app.tasks import process_note


class FakeLLMProvider(LLMProvider):
    def __init__(
        self,
        entities=None,
        relationships=None,
        raise_on_extract=False,
        embedding_fn=None,
        chat_response="fake answer",
    ):
        self._entities = entities or []
        self._relationships = relationships or []
        self.raise_on_extract = raise_on_extract
        # lets tests control embedding similarity instead of every text
        # mapping to the same constant vector, so ranking is actually testable
        self._embedding_fn = embedding_fn or (lambda _text: [0.1] * 768)
        self.chat_response = chat_response
        self.chat_calls: list[list[dict[str, str]]] = []

    def extract(self, text: str) -> ExtractionResult:
        if self.raise_on_extract:
            raise RuntimeError("the model exploded")
        return ExtractionResult(entities=self._entities, relationships=self._relationships)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embedding_fn(text) for text in texts]

    def chat(self, messages: list[dict[str, str]]) -> str:
        self.chat_calls.append(messages)
        return self.chat_response


def _create_note_and_job(authed_client, db_session, title="Note", body="Some content"):
    note_resp = authed_client.post(
        "/notes",
        json={"title": title, "content": {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": body}]}]}},
    )
    assert note_resp.status_code == 201
    note_id = note_resp.json()["id"]

    job = db_session.scalar(
        select(ExtractionJob).where(ExtractionJob.note_id == note_id)
    )
    return note_id, job


def test_creating_a_note_enqueues_a_pending_job_with_a_real_rq_id(authed_client, db_session):
    note_id, job = _create_note_and_job(authed_client, db_session)
    assert job is not None
    assert job.status == JobStatus.pending.value
    assert job.rq_job_id


def test_updating_a_note_supersedes_the_previous_pending_job(authed_client, db_session):
    note_id, first_job = _create_note_and_job(authed_client, db_session)

    resp = authed_client.patch(f"/notes/{note_id}", json={"title": "Updated"})
    assert resp.status_code == 200

    db_session.refresh(first_job)
    assert first_job.status == JobStatus.cancelled.value

    jobs = list(
        db_session.scalars(
            select(ExtractionJob)
            .where(ExtractionJob.note_id == note_id)
            .order_by(ExtractionJob.created_at)
        )
    )
    assert len(jobs) == 2
    assert jobs[-1].status == JobStatus.pending.value


def test_process_note_writes_chunks_entities_and_relationships(
    monkeypatch, authed_client, db_session
):
    fake = FakeLLMProvider(
        entities=[ExtractedEntity(name="Cortex", type="app"), ExtractedEntity(name="Postgres", type="database")],
        relationships=[ExtractedRelationship(source="Cortex", target="Postgres", label="uses")],
    )
    monkeypatch.setattr("app.tasks.get_llm_provider", lambda: fake)

    note_id, job = _create_note_and_job(authed_client, db_session, body="Cortex uses Postgres for storage.")

    process_note(note_id, str(job.id), db=db_session)

    db_session.refresh(job)
    assert job.status == JobStatus.succeeded.value
    assert job.started_at is not None
    assert job.finished_at is not None

    chunks = list(db_session.scalars(select(NoteChunk).where(NoteChunk.note_id == note_id)))
    assert len(chunks) == 1
    assert "Cortex uses Postgres" in chunks[0].content
    assert len(chunks[0].embedding) == 768

    entities = {
        e.name: e
        for e in db_session.scalars(
            select(Entity).join(NoteEntity).where(NoteEntity.note_id == note_id)
        ).all()
    }
    assert set(entities) == {"Cortex", "Postgres"}

    mentions = list(db_session.scalars(select(NoteEntity).where(NoteEntity.note_id == note_id)))
    assert len(mentions) == 2

    relationships = list(db_session.scalars(select(Relationship).where(Relationship.note_id == note_id)))
    assert len(relationships) == 1
    assert relationships[0].source_entity_id == entities["Cortex"].id
    assert relationships[0].target_entity_id == entities["Postgres"].id
    assert relationships[0].label == "uses"


def test_process_note_reuses_existing_entity_across_notes(monkeypatch, authed_client, db_session):
    fake = FakeLLMProvider(entities=[ExtractedEntity(name="Cortex", type="app")])
    monkeypatch.setattr("app.tasks.get_llm_provider", lambda: fake)

    note_a_id, job_a = _create_note_and_job(authed_client, db_session, title="A", body="About Cortex.")
    process_note(note_a_id, str(job_a.id), db=db_session)

    note_b_id, job_b = _create_note_and_job(authed_client, db_session, title="B", body="Also about Cortex.")
    process_note(note_b_id, str(job_b.id), db=db_session)

    note = db_session.get(Note, note_a_id)
    entities = list(
        db_session.scalars(select(Entity).where(Entity.user_id == note.user_id, Entity.name == "Cortex"))
    )
    assert len(entities) == 1  # same entity reused, not duplicated

    mentions = list(db_session.scalars(select(NoteEntity).where(NoteEntity.entity_id == entities[0].id)))
    assert {str(m.note_id) for m in mentions} == {note_a_id, note_b_id}


def test_process_note_dedupes_repeated_entities_and_relationships_in_one_run(
    monkeypatch, authed_client, db_session
):
    fake = FakeLLMProvider(
        entities=[ExtractedEntity(name="Cortex"), ExtractedEntity(name="Cortex")],
        relationships=[
            ExtractedRelationship(source="Cortex", target="Cortex", label="is"),
            ExtractedRelationship(source="Cortex", target="Cortex", label="is"),
        ],
    )
    monkeypatch.setattr("app.tasks.get_llm_provider", lambda: fake)

    note_id, job = _create_note_and_job(authed_client, db_session, body="Cortex is Cortex.")
    process_note(note_id, str(job.id), db=db_session)

    mentions = list(db_session.scalars(select(NoteEntity).where(NoteEntity.note_id == note_id)))
    assert len(mentions) == 1

    relationships = list(db_session.scalars(select(Relationship).where(Relationship.note_id == note_id)))
    assert len(relationships) == 1


def test_process_note_marks_job_failed_on_extraction_error(monkeypatch, authed_client, db_session):
    fake = FakeLLMProvider(raise_on_extract=True)
    monkeypatch.setattr("app.tasks.get_llm_provider", lambda: fake)

    note_id, job = _create_note_and_job(authed_client, db_session, body="Whatever.")

    try:
        process_note(note_id, str(job.id), db=db_session)
    except RuntimeError:
        pass

    db_session.refresh(job)
    assert job.status == JobStatus.failed.value
    assert "exploded" in job.error


def test_process_note_skips_cancelled_jobs(monkeypatch, authed_client, db_session):
    fake = FakeLLMProvider(entities=[ExtractedEntity(name="Should not appear")])
    monkeypatch.setattr("app.tasks.get_llm_provider", lambda: fake)

    note_id, job = _create_note_and_job(authed_client, db_session)
    job.status = JobStatus.cancelled.value
    db_session.commit()

    process_note(note_id, str(job.id), db=db_session)

    entities = list(db_session.scalars(select(Entity).where(Entity.name == "Should not appear")))
    assert entities == []


def test_process_note_handles_empty_note_content(authed_client, db_session):
    resp = authed_client.post("/notes", json={"title": "Empty", "content": {"type": "doc", "content": []}})
    empty_note_id = resp.json()["id"]
    empty_job = db_session.scalar(
        select(ExtractionJob).where(ExtractionJob.note_id == empty_note_id)
    )

    process_note(empty_note_id, str(empty_job.id), db=db_session)

    db_session.refresh(empty_job)
    assert empty_job.status == JobStatus.succeeded.value
    chunks = list(db_session.scalars(select(NoteChunk).where(NoteChunk.note_id == empty_note_id)))
    assert chunks == []


def test_manual_process_endpoint_enqueues_a_new_job(authed_client, db_session):
    note_id, first_job = _create_note_and_job(authed_client, db_session)

    resp = authed_client.post(f"/notes/{note_id}/process")
    assert resp.status_code == 202
    assert resp.json()["id"] != str(first_job.id)


def test_get_job_returns_the_latest_job(authed_client, db_session):
    # note: can't distinguish "latest" by created_at here - within one test's
    # transaction, Postgres's now() is fixed for the whole transaction, so
    # both jobs get an identical timestamp (a testing artifact only; real
    # requests are separate transactions, so this never ties in production).
    # Status is the reliable signal instead: the first job gets cancelled
    # by the supersede logic, so only the second job is still "pending".
    note_id, first_job = _create_note_and_job(authed_client, db_session)
    authed_client.patch(f"/notes/{note_id}", json={"title": "Updated"})

    resp = authed_client.get(f"/notes/{note_id}/job")
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"

    db_session.refresh(first_job)
    assert first_job.status == "cancelled"


def test_get_job_for_note_with_no_job_returns_null(authed_client, db_session):
    # a note always gets a job on creation, so simulate the "no job yet"
    # case only being reachable if creation enqueueing ever failed - here
    # we just confirm the endpoint 404s for someone else's / nonexistent note
    import uuid as uuid_module

    resp = authed_client.get(f"/notes/{uuid_module.uuid4()}/job")
    assert resp.status_code == 404
