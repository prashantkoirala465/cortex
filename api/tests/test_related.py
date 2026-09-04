from sqlalchemy import select

from app.models import ExtractionJob
from app.tasks import process_note
from tests.test_extraction import FakeLLMProvider
from tests.test_search import _embedding_for


def _create_and_process_note(authed_client, db_session, title, body, fake):
    resp = authed_client.post(
        "/notes",
        json={
            "title": title,
            "content": {
                "type": "doc",
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": body}]}],
            },
        },
    )
    note_id = resp.json()["id"]
    job = db_session.scalar(select(ExtractionJob).where(ExtractionJob.note_id == note_id))
    process_note(note_id, str(job.id), db=db_session)
    return note_id


def test_related_notes_empty_when_note_has_no_chunks(authed_client):
    resp = authed_client.post("/notes", json={"title": "Empty", "content": {"type": "doc", "content": []}})
    note_id = resp.json()["id"]

    resp = authed_client.get(f"/notes/{note_id}/related")
    assert resp.status_code == 200
    assert resp.json() == []


def test_related_notes_surfaces_similar_note_and_excludes_unrelated(
    monkeypatch, authed_client, db_session
):
    fake = FakeLLMProvider(embedding_fn=_embedding_for)
    monkeypatch.setattr("app.tasks.get_llm_provider", lambda: fake)

    postgres_a = _create_and_process_note(
        authed_client, db_session, "DB notes 1", "Postgres is a relational database.", fake
    )
    postgres_b = _create_and_process_note(
        authed_client, db_session, "DB notes 2", "Postgres supports JSON columns well.", fake
    )
    _create_and_process_note(
        authed_client, db_session, "Pet notes", "Cats are independent animals.", fake
    )

    resp = authed_client.get(f"/notes/{postgres_a}/related")
    assert resp.status_code == 200
    results = resp.json()

    related_ids = [r["note_id"] for r in results]
    assert postgres_b in related_ids
    assert postgres_a not in related_ids  # never relates a note to itself
    assert len(results) == 1  # the cat note is below the relevance threshold


def test_related_notes_is_scoped_per_user(monkeypatch, client, register, db_session):
    fake = FakeLLMProvider(embedding_fn=_embedding_for)
    monkeypatch.setattr("app.tasks.get_llm_provider", lambda: fake)

    alice = register()
    client.headers["Authorization"] = f"Bearer {alice['access_token']}"
    alice_note = _create_and_process_note(client, db_session, "Alice DB", "Postgres notes.", fake)

    bob = register()
    client.headers["Authorization"] = f"Bearer {bob['access_token']}"
    _create_and_process_note(client, db_session, "Bob DB", "Postgres notes too.", fake)

    # back to alice - bob's note must never appear as "related"
    client.headers["Authorization"] = f"Bearer {alice['access_token']}"
    resp = client.get(f"/notes/{alice_note}/related")
    assert resp.json() == []


def test_related_notes_requires_ownership(client, register):
    alice = register()
    client.headers["Authorization"] = f"Bearer {alice['access_token']}"
    resp = client.post("/notes", json={"title": "x", "content": {"type": "doc", "content": []}})
    note_id = resp.json()["id"]

    bob = register()
    client.headers["Authorization"] = f"Bearer {bob['access_token']}"
    resp = client.get(f"/notes/{note_id}/related")
    assert resp.status_code == 404
