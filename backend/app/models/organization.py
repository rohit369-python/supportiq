"""Organization and organization settings models."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class Organization(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    logo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", server_default="UTC")
    default_language: Mapped[str] = mapped_column(String(10), default="en", server_default="en")

    # Relationships
    settings: Mapped[Optional["OrganizationSettings"]] = relationship(
        "OrganizationSettings", back_populates="organization", uselist=False
    )
    users: Mapped[list["User"]] = relationship("User", back_populates="organization")

    def __repr__(self) -> str:
        return f"<Organization {self.slug}>"


class OrganizationSettings(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "organization_settings"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), unique=True
    )

    # Support policies
    auto_assign_tickets: Mapped[bool] = mapped_column(Boolean, default=True)
    require_ai_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_customer_registration: Mapped[bool] = mapped_column(Boolean, default=True)
    default_sla_policy_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    # AI configuration (non-secret)
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    chatbot_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_classify_tickets: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_suggest_replies: Mapped[bool] = mapped_column(Boolean, default=True)
    confidence_threshold: Mapped[float] = mapped_column(default=0.75)

    # Notification preferences
    notify_on_assignment: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_sla_breach: Mapped[bool] = mapped_column(Boolean, default=True)

    # Extensible JSON settings
    extra_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="settings")