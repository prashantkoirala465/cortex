import uuid


def test_register_returns_tokens(client):
    resp = client.post(
        "/auth/register",
        json={"email": f"{uuid.uuid4()}@example.com", "password": "testpassword123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_register_rejects_duplicate_email(client):
    email = f"{uuid.uuid4()}@example.com"
    client.post("/auth/register", json={"email": email, "password": "testpassword123"})

    resp = client.post("/auth/register", json={"email": email, "password": "anotherpassword"})
    assert resp.status_code == 409


def test_register_rejects_short_password(client):
    resp = client.post(
        "/auth/register", json={"email": f"{uuid.uuid4()}@example.com", "password": "short"}
    )
    assert resp.status_code == 422


def test_login_with_correct_credentials(client):
    email = f"{uuid.uuid4()}@example.com"
    client.post("/auth/register", json={"email": email, "password": "testpassword123"})

    resp = client.post("/auth/login", json={"email": email, "password": "testpassword123"})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_with_wrong_password_fails(client):
    email = f"{uuid.uuid4()}@example.com"
    client.post("/auth/register", json={"email": email, "password": "testpassword123"})

    resp = client.post("/auth/login", json={"email": email, "password": "wrongpassword"})
    assert resp.status_code == 401


def test_login_with_unknown_email_fails(client):
    resp = client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "whatever123"}
    )
    assert resp.status_code == 401


def test_me_requires_valid_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401

    client.headers["Authorization"] = "Bearer not-a-real-token"
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(client, register):
    tokens = register()
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"

    resp = client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == tokens["email"]


def test_refresh_issues_new_tokens_and_rotates_old_one(client, register):
    tokens = register()

    resp = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

    # old refresh token was single-use - reusing it must fail
    resp = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401


def test_refresh_rejects_garbage_token(client):
    resp = client.post("/auth/refresh", json={"refresh_token": "garbage"})
    assert resp.status_code == 401


def test_refresh_rejects_access_token_used_as_refresh_token(client, register):
    tokens = register()
    resp = client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert resp.status_code == 401


def test_logout_revokes_refresh_token(client, register):
    tokens = register()

    resp = client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 204

    resp = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401
