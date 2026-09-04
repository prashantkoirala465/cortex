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

Coming together as the project is built out — see individual `web/` and `api/` READMEs once they exist.
