import uuid


def test_create_and_get_note(authed_client):
    resp = authed_client.post("/notes", json={"title": "Test note", "content": {"type": "doc"}})
    assert resp.status_code == 201
    note_id = resp.json()["id"]

    resp = authed_client.get(f"/notes/{note_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test note"


def test_list_notes_returns_created_notes(authed_client):
    authed_client.post("/notes", json={"title": "A", "content": {}})
    authed_client.post("/notes", json={"title": "B", "content": {}})

    resp = authed_client.get("/notes")
    assert resp.status_code == 200
    titles = {note["title"] for note in resp.json()}
    assert {"A", "B"} <= titles


def test_update_note_title(authed_client):
    created = authed_client.post("/notes", json={"title": "Old", "content": {}}).json()

    resp = authed_client.patch(f"/notes/{created['id']}", json={"title": "New"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "New"
    assert resp.json()["content"] == created["content"]


def test_delete_note(authed_client):
    created = authed_client.post("/notes", json={"title": "Bye", "content": {}}).json()

    resp = authed_client.delete(f"/notes/{created['id']}")
    assert resp.status_code == 204

    resp = authed_client.get(f"/notes/{created['id']}")
    assert resp.status_code == 404


def test_get_missing_note_returns_404(authed_client):
    resp = authed_client.get(f"/notes/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_notes_require_auth(client):
    resp = client.get("/notes")
    assert resp.status_code == 401

    resp = client.post("/notes", json={"title": "x", "content": {}})
    assert resp.status_code == 401


def test_users_cannot_see_each_others_notes(client, register):
    alice = register()
    bob = register()

    client.headers["Authorization"] = f"Bearer {alice['access_token']}"
    created = client.post("/notes", json={"title": "Alice's note", "content": {}}).json()

    client.headers["Authorization"] = f"Bearer {bob['access_token']}"
    resp = client.get(f"/notes/{created['id']}")
    assert resp.status_code == 404

    resp = client.get("/notes")
    assert resp.json() == []
