"""Customer management models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin, SoftDeleteMixin


class Customer(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "customers"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_type: Mapped[str] = mapped_column(String(50), default="individual")  # individual | business
    account_status: Mapped[str] = mapped_column(String(50), default="active")  # active | inactive | suspended
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    tags: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True, default=list)
    custom_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    last_interaction_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_tickets: Mapped[int] = mapped_column(Integer, default=0)
    avg_satisfaction: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    notes: Mapped[list["CustomerNote"]] = relationship(
        "CustomerNote", back_populates="customer", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Customer {self.email}>"


class CustomerNote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "customer_notes"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="notes")


class CustomerTag(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "customer_tags"

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)