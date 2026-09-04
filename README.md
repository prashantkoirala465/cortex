# Cortex

Cortex is a notes app that builds itself into a knowledge graph as you write. Every note gets processed in the background: entities and relationships get pulled out, embeddings get generated, and the result is a live graph you can explore, search semantically, and ask questions against — instead of a pile of notes you eventually stop searching through.

## Why

Most note apps only find what you explicitly link. Cortex tries to surface connections you didn't think to make yourself, and lets you treat your own notes as a queryable knowledge base rather than a flat list of documents.

## Stack

- **Frontend** (`web/`): Next.js, TypeScript, Tailwind, Tiptap (editor), React Flow (graph view)
- **Backend** (`api/`): FastAPI, SQLAlchemy, Alembic, Postgres + pgvector
- **Jobs**: Redis + RQ for async note processing (extraction, embeddings)
- **AI**: local inference via [Ollama](https://ollama.com) — no external API keys required to run this
- **Auth**: self-hosted email/password (bcrypt + JWT access/refresh tokens)

## Status

Early scaffolding. Build log lives in commit history.

## Local setup

Requires Docker, Python 3.11+, Node 20+, and [Ollama](https://ollama.com).

```bash
# 1. pull the local models (one-time)
ollama pull llama3.2
ollama pull nomic-embed-text

# 2. start postgres + redis
docker compose up -d

# 3. backend
cd api
cp ../.env.example .env
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload

# 4. background worker (new terminal) - processes notes: extraction + embeddings
cd api
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES .venv/bin/rq worker extraction --url redis://localhost:6379/0

# 5. frontend (new terminal)
cd web
cp ../.env.example .env.local
npm install
npm run dev
```

Notes get queued for processing on every save; without the worker running, new notes just sit in the queue until one is started.

`OBJC_DISABLE_INITIALIZE_FORK_SAFETY` is only needed on macOS - RQ's default worker forks a subprocess per job, and macOS's Objective-C runtime crashes on fork() unless that guard is disabled. Not needed on Linux (including wherever this ends up deployed).

See `api/README.md` and `web/README.md` for details on each app.
