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


def test_chat_with_no_notes_does_not_call_the_llm(monkeypatch, authed_client):
    fake = FakeLLMProvider()
    monkeypatch.setattr("app.routers.chat.get_llm_provider", lambda: fake)

    resp = authed_client.post("/chat", json={"question": "anything?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["sources"] == []
    assert fake.chat_calls == []


def test_chat_answers_using_relevant_notes_and_cites_them(monkeypatch, authed_client, db_session):
    fake = FakeLLMProvider(embedding_fn=_embedding_for, chat_response="Postgres, based on your notes.")
    monkeypatch.setattr("app.routers.chat.get_llm_provider", lambda: fake)
    monkeypatch.setattr("app.tasks.get_llm_provider", lambda: fake)

    postgres_note = _create_and_process_note(
        authed_client, db_session, "DB notes", "Postgres is a relational database.", fake
    )
    _create_and_process_note(
        authed_client, db_session, "Pet notes", "Cats are independent animals.", fake
    )

    question = "tell me about postgres"
    resp = authed_client.post("/chat", json={"question": question})
    assert resp.status_code == 200
    body = resp.json()

    assert body["answer"] == "Postgres, based on your notes."
    assert [s["id"] for s in body["sources"]] == [postgres_note]

    assert len(fake.chat_calls) == 1
    sent_messages = fake.chat_calls[0]
    assert sent_messages[0]["role"] == "system"
    assert "Postgres is a relational database" in sent_messages[0]["content"]
    assert "Cats are independent" not in sent_messages[0]["content"]
    assert sent_messages[-1] == {"role": "user", "content": question}


def test_chat_includes_history_in_the_prompt(monkeypatch, authed_client, db_session):
    fake = FakeLLMProvider(embedding_fn=_embedding_for)
    monkeypatch.setattr("app.routers.chat.get_llm_provider", lambda: fake)
    monkeypatch.setattr("app.tasks.get_llm_provider", lambda: fake)

    _create_and_process_note(authed_client, db_session, "DB notes", "Postgres is great.", fake)

    resp = authed_client.post(
        "/chat",
        json={
            "question": "why is postgres a good choice?",
            "history": [
                {"role": "user", "content": "what database do I use?"},
                {"role": "assistant", "content": "Postgres."},
            ],
        },
    )
    assert resp.status_code == 200

    sent_messages = fake.chat_calls[0]
    assert {"role": "user", "content": "what database do I use?"} in sent_messages
    assert {"role": "assistant", "content": "Postgres."} in sent_messages
    assert sent_messages[-1] == {"role": "user", "content": "why is postgres a good choice?"}


def test_chat_is_scoped_per_user(monkeypatch, client, register, db_session):
    fake = FakeLLMProvider(embedding_fn=_embedding_for)
    monkeypatch.setattr("app.routers.chat.get_llm_provider", lambda: fake)
    monkeypatch.setattr("app.tasks.get_llm_provider", lambda: fake)

    alice = register()
    client.headers["Authorization"] = f"Bearer {alice['access_token']}"
    resp = client.post(
        "/notes",
        json={
            "title": "Alice's secret",
            "content": {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Postgres notes."}]}]},
        },
    )
    note_id = resp.json()["id"]
    job = db_session.scalar(select(ExtractionJob).where(ExtractionJob.note_id == note_id))
    process_note(note_id, str(job.id), db=db_session)

    bob = register()
    client.headers["Authorization"] = f"Bearer {bob['access_token']}"
    resp = client.post("/chat", json={"question": "what does alice use?"})
    assert resp.json()["sources"] == []
    assert fake.chat_calls == []


def test_chat_requires_nonempty_question(authed_client):
    resp = authed_client.post("/chat", json={"question": ""})
    assert resp.status_code == 422
