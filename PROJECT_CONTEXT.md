# SupportIQ – Project Context

## Architecture Decisions

- Modular monolith (FastAPI + Celery)
- PostgreSQL as system of record + pgvector for RAG
- MongoDB only for flexible webhook / integration event documents
- Provider-independent AI layer with mock fallback
- JWT + refresh token rotation
- Granular RBAC enforced on the backend

## Implemented Modules

- Organizations & multi-tenancy
- Users, roles, permissions, refresh tokens
- Customers (models + seed)
- Tickets (CRUD, status transitions, AI classification on create)
- Conversations & messages (models + chatbot flow)
- Knowledge base models (documents, chunks, articles)
- AI engine: classification, mock LLM/embeddings, RAG pipeline, safety guardrails
- Chatbot API with escalation
- Celery app + sample tasks
- React frontend: login, agent dashboard, ticket list/detail, chatbot
- Docker Compose stack
- Seed script with realistic e-commerce demo data
- Core unit tests (auth, transitions, safety)

## Environment Variables

See `.env.example`. Critical ones:

- `DATABASE_URL` / `DATABASE_URL_SYNC`
- `LLM_PROVIDER` (mock | openai)
- `OPENAI_API_KEY` (only if using openai)
- `JWT_SECRET_KEY`, `APP_SECRET_KEY`

## Known Limitations

- Full document upload → extract → chunk → embed pipeline is scaffolded (models + Celery task) but not fully wired end-to-end in this delivery.
- Vector search requires a running PostgreSQL with pgvector; without it RAG returns a safe “no relevant documents” response.
- Power BI: reporting schema and measure guidance are described; actual .pbix files are not generated.
- Frontend covers core agent and chatbot flows; manager/admin/analytics screens follow the same patterns and can be extended.
- Some advanced features (WebSocket real-time, full evaluation harness, hybrid search, reranking) are architected and partially implemented.

## Test Status

- Unit tests for password hashing, JWT, ticket transitions, and safety guardrails pass offline.
- Integration tests require a live Postgres instance (use Docker Compose).

## How to Extend

1. Add new API routers under `backend/app/api/v1/` and include them in `router.py`.
2. Add Celery tasks under `backend/workers/`.
3. Add frontend pages under `frontend/src/pages/` and routes in `App.tsx`.
4. New AI capabilities go into `backend/ai_engine/` behind the provider interfaces.