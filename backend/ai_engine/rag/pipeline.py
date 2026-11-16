"""Simple but complete RAG pipeline with organization isolation."""

from dataclasses import dataclass, field
from typing import Optional
import time

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.knowledge import DocumentChunk, KnowledgeDocument
from ai_engine.providers.factory import get_llm_provider, get_embedding_provider
from ai_engine.prompts.templates import RAG_SYSTEM, RAG_USER
from ai_engine.guardrails.safety import SafetyGuard


@dataclass
class RetrievedChunk:
    chunk_id: str
    content: str
    score: float
    document_title: str
    page_number: Optional[int] = None
    section_heading: Optional[str] = None


@dataclass
class RAGResult:
    answer: str
    citations: list[dict] = field(default_factory=list)
    retrieved: list[RetrievedChunk] = field(default_factory=list)
    confidence: float = 0.0
    latency_ms: int = 0
    escalated: bool = False
    escalation_reason: Optional[str] = None


class RAGPipeline:
    def __init__(self, db: AsyncSession, organization_id):
        self.db = db
        self.organization_id = organization_id
        self.llm = get_llm_provider()
        self.embedder = get_embedding_provider()
        self.guard = SafetyGuard()

    async def retrieve(self, query: str, top_k: Optional[int] = None) -> list[RetrievedChunk]:
        top_k = top_k or settings.rag_top_k
        emb_resp = await self.embedder.embed([query])
        query_vec = emb_resp.embeddings[0]

        # pgvector cosine distance query (1 - cosine similarity)
        # We use a raw query for vector search with tenant filter
        sql = text("""
            SELECT
                c.id,
                c.content,
                c.page_number,
                c.section_heading,
                d.title AS document_title,
                1 - (c.embedding <=> :qvec) AS score
            FROM document_chunks c
            JOIN knowledge_documents d ON d.id = c.document_id
            WHERE c.organization_id = :org_id
              AND c.is_active = true
              AND d.is_published = true
              AND d.is_approved = true
              AND c.embedding IS NOT NULL
            ORDER BY c.embedding <=> :qvec
            LIMIT :k
        """)
        # For environments without live pgvector we fall back to empty
        try:
            # Convert list to pgvector string format
            vec_str = "[" + ",".join(str(x) for x in query_vec) + "]"
            result = await self.db.execute(
                sql,
                {"qvec": vec_str, "org_id": str(self.organization_id), "k": top_k},
            )
            rows = result.fetchall()
        except Exception:
            # Fallback: no vector index available – return empty (safe)
            rows = []

        chunks = []
        for row in rows:
            score = float(row.score) if row.score is not None else 0.0
            if score < settings.rag_similarity_threshold:
                continue
            chunks.append(
                RetrievedChunk(
                    chunk_id=str(row.id),
                    content=row.content,
                    score=score,
                    document_title=row.document_title or "Document",
                    page_number=row.page_number,
                    section_heading=row.section_heading,
                )
            )
        return chunks

    async def generate(self, query: str, chunks: list[RetrievedChunk]) -> RAGResult:
        start = time.perf_counter()

        # Safety check on user query
        if self.guard.detect_prompt_injection(query):
            return RAGResult(
                answer="I cannot process this request. Please rephrase your question.",
                escalated=True,
                escalation_reason="potential_prompt_injection",
                latency_ms=int((time.perf_counter() - start) * 1000),
            )

        if not chunks:
            return RAGResult(
                answer=(
                    "I could not find relevant information in our knowledge base for this question. "
                    "Would you like me to connect you with a human support agent?"
                ),
                escalated=True,
                escalation_reason="no_relevant_documents",
                latency_ms=int((time.perf_counter() - start) * 1000),
            )

        context_parts = []
        citations = []
        for i, c in enumerate(chunks, 1):
            context_parts.append(f"[{i}] {c.content}")
            citations.append({
                "index": i,
                "chunk_id": c.chunk_id,
                "title": c.document_title,
                "score": round(c.score, 4),
                "page": c.page_number,
            })

        context = "\n\n".join(context_parts)
        user_prompt = RAG_USER.format(context=context, question=query)
        resp = await self.llm.complete(
            system_prompt=RAG_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=800,
        )

        # Basic groundedness / safety post-check
        answer = resp.content.strip()
        if self.guard.contains_unsafe_claims(answer):
            answer = (
                "I need to escalate this request to a human agent to ensure accuracy. "
                "Please hold on while I create a support ticket for you."
            )
            escalated = True
            reason = "unsafe_or_ungrounded_answer"
        else:
            escalated = False
            reason = None

        avg_score = sum(c.score for c in chunks) / len(chunks) if chunks else 0.0
        latency = int((time.perf_counter() - start) * 1000)

        return RAGResult(
            answer=answer,
            citations=citations,
            retrieved=chunks,
            confidence=round(avg_score, 3),
            latency_ms=latency,
            escalated=escalated,
            escalation_reason=reason,
        )

    async def ask(self, query: str) -> RAGResult:
        chunks = await self.retrieve(query)
        return await self.generate(query, chunks)