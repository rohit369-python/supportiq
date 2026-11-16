# SupportIQ Architecture

## Overview

SupportIQ is a modular monolith built with FastAPI (backend) and React (frontend). Background work is handled by Celery workers. Data is stored primarily in PostgreSQL (with pgvector for embeddings). MongoDB is reserved for flexible integration/event documents. Redis is used for caching, rate limiting, and as the Celery broker.

## Layers

1. **Presentation** – React SPA (agent workspace, customer portal, chatbot UI)
2. **API** – FastAPI REST + WebSocket-ready endpoints under `/api/v1`
3. **Application / Services** – Business workflows (tickets, auth, notifications)
4. **Domain** – Status transitions, assignment rules, SLA calculations, permissions
5. **AI Engine** – Provider-agnostic LLM/embedding interfaces, classification, RAG, guardrails
6. **Infrastructure** – SQLAlchemy, pgvector, MongoDB, Redis, file storage
7. **Workers** – Celery tasks for classification, document processing, SLA, email

## Multi-tenancy

Every business entity is scoped by `organization_id`. Queries always filter by the authenticated user's organization. Cross-tenant access is denied at the dependency / repository layer.

## AI Design

- All LLM calls go through `LLMProvider` / `EmbeddingProvider` abstractions.
- Default provider is `mock` (deterministic, offline).
- OpenAI-compatible provider is available via environment variables.
- RAG retrieves only published, approved chunks belonging to the caller's organization.
- SafetyGuard blocks common prompt-injection patterns and unsafe action claims.

## Key Design Decisions

- Modular monolith preferred over microservices for operational simplicity.
- Strict separation of internal notes from customer-visible messages.
- AI suggestions never become public replies without agent approval (configurable).
- Critical tickets cannot be silently downgraded by AI.