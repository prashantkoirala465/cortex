# Cortex API

FastAPI backend for Cortex: notes CRUD, background extraction pipeline, knowledge graph, search, and RAG chat.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp ../.env.example .env  # then fill in as needed
.venv/bin/uvicorn app.main:app --reload
```

Requires Postgres (with `pgvector`) and Redis running — see the root `docker-compose.yml`.
