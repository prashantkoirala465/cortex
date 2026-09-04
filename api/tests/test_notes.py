import uuid


def test_create_and_get_note(client):
    resp = client.post("/notes", json={"title": "Test note", "content": {"type": "doc"}})
    assert resp.status_code == 201
    note_id = resp.json()["id"]

    resp = client.get(f"/notes/{note_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test note"


def test_list_notes_returns_created_notes(client):
    client.post("/notes", json={"title": "A", "content": {}})
    client.post("/notes", json={"title": "B", "content": {}})

    resp = client.get("/notes")
    assert resp.status_code == 200
    titles = {note["title"] for note in resp.json()}
    assert {"A", "B"} <= titles


def test_update_note_title(client):
    created = client.post("/notes", json={"title": "Old", "content": {}}).json()

    resp = client.patch(f"/notes/{created['id']}", json={"title": "New"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "New"
    assert resp.json()["content"] == created["content"]


def test_delete_note(client):
    created = client.post("/notes", json={"title": "Bye", "content": {}}).json()

    resp = client.delete(f"/notes/{created['id']}")
    assert resp.status_code == 204

    resp = client.get(f"/notes/{created['id']}")
    assert resp.status_code == 404


def test_get_missing_note_returns_404(client):
    resp = client.get(f"/notes/{uuid.uuid4()}")
    assert resp.status_code == 404
