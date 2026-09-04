import uuid


def test_register_returns_access_token_and_sets_refresh_cookie(client):
    resp = client.post(
        "/auth/register",
        json={"email": f"{uuid.uuid4()}@example.com", "password": "testpassword123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert "refresh_token" not in body
    assert client.cookies.get("refresh_token")


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


def test_refresh_without_cookie_fails(client):
    resp = client.post("/auth/refresh")
    assert resp.status_code == 401


def test_refresh_issues_new_access_token_and_rotates_cookie(client, register):
    tokens = register()
    old_refresh_cookie = client.cookies.get("refresh_token")

    resp = client.post("/auth/refresh")
    assert resp.status_code == 200
    assert resp.json()["access_token"] != tokens["access_token"]

    new_refresh_cookie = client.cookies.get("refresh_token")
    assert new_refresh_cookie != old_refresh_cookie

    # the old refresh token was single-use - presenting it again must fail
    client.cookies.set("refresh_token", old_refresh_cookie)
    resp = client.post("/auth/refresh")
    assert resp.status_code == 401


def test_refresh_rejects_garbage_cookie(client):
    client.cookies.set("refresh_token", "garbage")
    resp = client.post("/auth/refresh")
    assert resp.status_code == 401


def test_refresh_rejects_access_token_used_as_refresh_token(client, register):
    tokens = register()
    client.cookies.set("refresh_token", tokens["access_token"])
    resp = client.post("/auth/refresh")
    assert resp.status_code == 401


def test_logout_clears_cookie_and_revokes_it(client, register):
    register()

    resp = client.post("/auth/logout")
    assert resp.status_code == 204
    assert client.cookies.get("refresh_token") is None

    resp = client.post("/auth/refresh")
    assert resp.status_code == 401
