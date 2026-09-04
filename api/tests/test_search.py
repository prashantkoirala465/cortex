from sqlalchemy import select

from app.models import ExtractionJob
from app.tasks import process_note
from tests.test_extraction import FakeLLMProvider

# two orthogonal-ish unit vectors so cosine distance clearly separates them
POSTGRES_VEC = [1.0] + [0.0] * 767
CATS_VEC = [0.0, 1.0] + [0.0] * 766


def _embedding_for(text: str) -> list[float]:
    return POSTGRES_VEC if "postgres" in text.lower() else CATS_VEC


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


def test_search_with_no_notes_returns_empty(authed_client):
    resp = authed_client.get("/search", params={"q": "anything"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_ranks_the_more_relevant_note_first(monkeypatch, authed_client, db_session):
    fake = FakeLLMProvider(embedding_fn=_embedding_for)
    monkeypatch.setattr("app.routers.search.get_llm_provider", lambda: fake)
    monkeypatch.setattr("app.tasks.get_llm_provider", lambda: fake)

    postgres_note = _create_and_process_note(
        authed_client, db_session, "DB notes", "Postgres is a relational database.", fake
    )
    cats_note = _create_and_process_note(
        authed_client, db_session, "Pet notes", "Cats are independent animals.", fake
    )

    resp = authed_client.get("/search", params={"q": "tell me about postgres"})
    assert resp.status_code == 200
    results = resp.json()

    assert len(results) == 2
    assert results[0]["note_id"] == postgres_note
    assert results[1]["note_id"] == cats_note
    assert results[0]["score"] > results[1]["score"]


def test_search_returns_one_result_per_note_even_with_multiple_matching_chunks(
    monkeypatch, authed_client, db_session
):
    fake = FakeLLMProvider(embedding_fn=_embedding_for)
    monkeypatch.setattr("app.routers.search.get_llm_provider", lambda: fake)
    monkeypatch.setattr("app.tasks.get_llm_provider", lambda: fake)

    # a long note gets split into multiple chunks - all about postgres
    long_body = "\n".join(["Postgres is great for relational data."] * 5)
    note_id = _create_and_process_note(authed_client, db_session, "Long note", long_body, fake)

    resp = authed_client.get("/search", params={"q": "postgres"})
    results = resp.json()
    assert len(results) == 1
    assert results[0]["note_id"] == note_id


def test_search_is_scoped_per_user(monkeypatch, client, register, db_session):
    fake = FakeLLMProvider(embedding_fn=_embedding_for)
    monkeypatch.setattr("app.routers.search.get_llm_provider", lambda: fake)
    monkeypatch.setattr("app.tasks.get_llm_provider", lambda: fake)

    alice = register()
    client.headers["Authorization"] = f"Bearer {alice['access_token']}"
    resp = client.post(
        "/notes",
        json={
            "title": "Alice's note",
            "content": {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Postgres notes."}]}]},
        },
    )
    note_id = resp.json()["id"]
    job = db_session.scalar(select(ExtractionJob).where(ExtractionJob.note_id == note_id))
    process_note(note_id, str(job.id), db=db_session)

    bob = register()
    client.headers["Authorization"] = f"Bearer {bob['access_token']}"
    resp = client.get("/search", params={"q": "postgres"})
    assert resp.json() == []


def test_search_requires_nonempty_query(authed_client):
    resp = authed_client.get("/search", params={"q": ""})
    assert resp.status_code == 422
