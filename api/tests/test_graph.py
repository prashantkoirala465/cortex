from sqlalchemy import select

from app.llm.base import ExtractedEntity, ExtractedRelationship
from app.models import ExtractionJob
from app.tasks import process_note
from tests.test_extraction import FakeLLMProvider


def _process(monkeypatch, db_session, authed_client, entities, relationships, body="content"):
    fake = FakeLLMProvider(entities=entities, relationships=relationships)
    monkeypatch.setattr("app.tasks.get_llm_provider", lambda: fake)

    resp = authed_client.post(
        "/notes",
        json={
            "title": "Note",
            "content": {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": body}]}]},
        },
    )
    note_id = resp.json()["id"]
    job = db_session.scalar(select(ExtractionJob).where(ExtractionJob.note_id == note_id))
    process_note(note_id, str(job.id), db=db_session)
    return note_id


def test_empty_graph_for_fresh_account(authed_client):
    resp = authed_client.get("/graph")
    assert resp.status_code == 200
    assert resp.json() == {"nodes": [], "edges": []}


def test_graph_reflects_extracted_entities_and_relationships(monkeypatch, authed_client, db_session):
    note_id = _process(
        monkeypatch,
        db_session,
        authed_client,
        entities=[ExtractedEntity(name="Cortex", type="app"), ExtractedEntity(name="Postgres", type="db")],
        relationships=[ExtractedRelationship(source="Cortex", target="Postgres", label="uses")],
    )

    resp = authed_client.get("/graph")
    assert resp.status_code == 200
    body = resp.json()

    names = {n["name"] for n in body["nodes"]}
    assert names == {"Cortex", "Postgres"}

    cortex_node = next(n for n in body["nodes"] if n["name"] == "Cortex")
    assert cortex_node["note_ids"] == [note_id]

    assert len(body["edges"]) == 1
    assert body["edges"][0]["label"] == "uses"
    assert body["edges"][0]["note_id"] == note_id


def test_entity_mentioned_in_two_notes_lists_both(monkeypatch, authed_client, db_session):
    note_a = _process(monkeypatch, db_session, authed_client, entities=[ExtractedEntity(name="Cortex")], relationships=[], body="a")
    note_b = _process(monkeypatch, db_session, authed_client, entities=[ExtractedEntity(name="Cortex")], relationships=[], body="b")

    resp = authed_client.get("/graph")
    cortex_node = next(n for n in resp.json()["nodes"] if n["name"] == "Cortex")
    assert set(cortex_node["note_ids"]) == {note_a, note_b}


def test_graph_is_scoped_per_user(monkeypatch, client, register, db_session):
    alice = register()
    client.headers["Authorization"] = f"Bearer {alice['access_token']}"

    fake = FakeLLMProvider(entities=[ExtractedEntity(name="Alice's Secret")])
    monkeypatch.setattr("app.tasks.get_llm_provider", lambda: fake)
    resp = client.post("/notes", json={"title": "n", "content": {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "x"}]}]}})
    note_id = resp.json()["id"]
    job = db_session.scalar(select(ExtractionJob).where(ExtractionJob.note_id == note_id))
    process_note(note_id, str(job.id), db=db_session)

    bob = register()
    client.headers["Authorization"] = f"Bearer {bob['access_token']}"
    resp = client.get("/graph")
    assert resp.json() == {"nodes": [], "edges": []}
