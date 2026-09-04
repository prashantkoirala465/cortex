# Cortex API

FastAPI backend for Cortex: notes CRUD, background extraction pipeline, knowledge graph, search, and RAG chat.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp ../.env.example .env  # then fill in as needed
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload
```

Requires Postgres (with `pgvector`) and Redis running — see the root `docker-compose.yml` — and [Ollama](https://ollama.com) serving locally with `llama3.2` and `nomic-embed-text` pulled.

Notes get processed (entity/relationship extraction + embeddings) by a background worker, not inline in the request:

```bash
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES .venv/bin/rq worker extraction --url redis://localhost:6379/0
```

(the `OBJC_DISABLE_INITIALIZE_FORK_SAFETY` flag is a macOS-only workaround for a crash in RQ's forking worker; not needed on Linux)

## Tests

```bash
.venv/bin/pytest -v
```
