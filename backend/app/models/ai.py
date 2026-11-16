"""AI interaction, classification, suggestion and feedback models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class AIInteraction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_interactions"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    interaction_type: Mapped[str] = mapped_column(String(50), nullable=False)  # classify | summarize | rag | suggest
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ticket | conversation | message
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), default="mock")
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    input_preview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # truncated for privacy
    output_preview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token_usage: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="success")  # success | error | timeout
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)


class AIClassification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_classifications"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), index=True)
    interaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extracted_entities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    raw_output: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_corrected: Mapped[bool] = mapped_column(Boolean, default=False)
    corrected_intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    corrected_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)


class AISentimentResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_sentiment_results"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    ticket_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=True)
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    sentiment: Mapped[str] = mapped_column(String(30), nullable=False)  # positive | neutral | negative | very_negative
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_corrected: Mapped[bool] = mapped_column(Boolean, default=False)
    corrected_sentiment: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)


class AIPriorityRecommendation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_priority_recommendations"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), index=True)
    recommended_priority: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    was_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    was_overridden: Mapped[bool] = mapped_column(Boolean, default=False)
    overridden_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)


class AISummary(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_summaries"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    ticket_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=True)
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    summary_type: Mapped[str] = mapped_column(String(40), default="conversation")  # conversation | ticket
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    edited_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    edited_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class AISuggestion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_suggestions"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    ticket_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=True)
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    suggestion_type: Mapped[str] = mapped_column(String(40), default="reply")  # reply | next_action | note
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending | accepted | edited | rejected
    final_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    feedback_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class AIFeedback(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_feedback"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    interaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    suggestion_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # helpful | incorrect | incomplete | irrelevant_source | incorrect_classification | unsafe
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    original_output: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    corrected_output: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class AIPromptVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_prompt_versions"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)  # null = global
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_type: Mapped[str] = mapped_column(String(50), nullable=False)  # classify | summarize | rag | suggest
    version: Mapped[str] = mapped_column(String(30), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    user_prompt_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)


class AIUsageRecord(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "ai_usage_records"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)