# Cortex

Cortex is a notes app that builds itself into a knowledge graph as you write. Every note gets processed in the background: entities and relationships get pulled out, embeddings get generated, and the result is a live graph you can explore, search semantically, and ask questions against — instead of a pile of notes you eventually stop searching through.

## Why

Most note apps only find what you explicitly link. Cortex tries to surface connections you didn't think to make yourself, and lets you treat your own notes as a queryable knowledge base rather than a flat list of documents.

## Stack

- **Frontend** (`web/`): Next.js, TypeScript, Tailwind, Tiptap (editor), React Flow (graph view)
- **Backend** (`api/`): FastAPI, SQLAlchemy, Alembic, Postgres + pgvector
- **Jobs**: Redis + RQ for async note processing (extraction, embeddings)
- **AI**: local inference via [Ollama](https://ollama.com) — no external API keys required to run this
- **Auth**: Clerk

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
.venv/bin/uvicorn app.main:app --reload

# 4. frontend (new terminal)
cd web
cp ../.env.example .env.local
npm install
npm run dev
```

See `api/README.md` and `web/README.md` for details on each app.
