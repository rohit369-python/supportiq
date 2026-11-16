"""Customer-facing chatbot API."""

from typing import Annotated, Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database.session import get_db
from app.models.conversation import Conversation, Message
from app.models.customer import Customer
from app.core.deps import get_current_user, CurrentUser
from ai_engine.rag.pipeline import RAGPipeline

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


class ChatMessageIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None


class CitationOut(BaseModel):
    index: int
    title: str
    score: float
    page: Optional[int] = None


class ChatMessageOut(BaseModel):
    conversation_id: UUID
    message_id: UUID
    role: str
    content: str
    citations: list[CitationOut] = []
    escalated: bool = False
    escalation_reason: Optional[str] = None
    confidence: float = 0.0


@router.post("/message", response_model=ChatMessageOut)
async def send_chat_message(
    body: ChatMessageIn,
    current: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    org_id = current.organization_id

    # Resolve or create conversation
    conversation = None
    if body.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == body.conversation_id,
                Conversation.organization_id == org_id,
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation is None:
        conversation = Conversation(
            organization_id=org_id,
            customer_id=body.customer_id,
            channel="chatbot",
            status="open",
            is_ai_handled=True,
            last_message_at=datetime.now(timezone.utc),
        )
        db.add(conversation)
        await db.flush()

    # Store customer message
    user_msg = Message(
        conversation_id=conversation.id,
        sender_id=current.user_id,
        sender_type="customer",
        content=body.message,
        message_type="text",
        is_internal=False,
    )
    db.add(user_msg)
    conversation.message_count = (conversation.message_count or 0) + 1
    conversation.last_message_at = datetime.now(timezone.utc)
    await db.flush()

    # RAG
    pipeline = RAGPipeline(db, org_id)
    rag_result = await pipeline.ask(body.message)

    # Store AI reply
    ai_msg = Message(
        conversation_id=conversation.id,
        sender_type="ai",
        content=rag_result.answer,
        message_type="text",
        is_internal=False,
        is_ai_generated=True,
        citations=rag_result.citations,
    )
    db.add(ai_msg)
    conversation.message_count += 1
    conversation.last_message_at = datetime.now(timezone.utc)

    if rag_result.escalated:
        conversation.handoff_requested = True
        conversation.handoff_at = datetime.now(timezone.utc)

    await db.flush()

    citations_out = [
        CitationOut(index=c["index"], title=c["title"], score=c["score"], page=c.get("page"))
        for c in rag_result.citations
    ]

    return ChatMessageOut(
        conversation_id=conversation.id,
        message_id=ai_msg.id,
        role="assistant",
        content=rag_result.answer,
        citations=citations_out,
        escalated=rag_result.escalated,
        escalation_reason=rag_result.escalation_reason,
        confidence=rag_result.confidence,
    )