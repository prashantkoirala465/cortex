import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db import get_db
from app.main import app

engine = create_engine(settings.database_url)
TestSessionLocal = sessionmaker(bind=engine)


@pytest.fixture()
def db_session():
    """Each test runs in a savepoint that's rolled back afterwards, so
    nothing a test writes ever persists past that test."""
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _register(client: TestClient, password: str = "testpassword123") -> dict:
    email = f"test-{uuid.uuid4()}@example.com"
    resp = client.post("/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    return {"email": email, "password": password, **resp.json()}


@pytest.fixture()
def register(client):
    """Factory for creating a fresh registered user against the test client."""

    def _make():
        return _register(client)

    return _make


@pytest.fixture()
def authed_client(client):
    """A TestClient with a freshly registered user's access token attached
    to every request, for tests that only care about authenticated notes
    behavior rather than the auth flow itself."""
    tokens = _register(client)
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    return client
