"""SQLAlchemy models package."""

from app.models.organization import Organization, OrganizationSettings
from app.models.user import User, Role, Permission, UserRole, RolePermission, RefreshToken
from app.models.customer import Customer, CustomerNote, CustomerTag
from app.models.ticket import (
    Ticket,
    TicketStatusHistory,
    TicketPriorityHistory,
    TicketAssignment,
    TicketEvent,
    Tag,
    TicketTag,
)
from app.models.conversation import Conversation, Message, MessageAttachment, InternalNote
from app.models.knowledge import (
    KnowledgeDocument,
    KnowledgeDocumentVersion,
    KnowledgeArticle,
    DocumentChunk,
    DocumentProcessingJob,
)
from app.models.ai import (
    AIInteraction,
    AIClassification,
    AISentimentResult,
    AIPriorityRecommendation,
    AISummary,
    AISuggestion,
    AIFeedback,
    AIPromptVersion,
    AIUsageRecord,
)
from app.models.sla import SLAPolicy, SLAEvent, WorkflowRule, EscalationEvent
from app.models.notification import Notification, NotificationTemplate
from app.models.audit import AuditLog

__all__ = [
    "Organization",
    "OrganizationSettings",
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "RefreshToken",
    "Customer",
    "CustomerNote",
    "CustomerTag",
    "Ticket",
    "TicketStatusHistory",
    "TicketPriorityHistory",
    "TicketAssignment",
    "TicketEvent",
    "Tag",
    "TicketTag",
    "Conversation",
    "Message",
    "MessageAttachment",
    "InternalNote",
    "KnowledgeDocument",
    "KnowledgeDocumentVersion",
    "KnowledgeArticle",
    "DocumentChunk",
    "DocumentProcessingJob",
    "AIInteraction",
    "AIClassification",
    "AISentimentResult",
    "AIPriorityRecommendation",
    "AISummary",
    "AISuggestion",
    "AIFeedback",
    "AIPromptVersion",
    "AIUsageRecord",
    "SLAPolicy",
    "SLAEvent",
    "WorkflowRule",
    "EscalationEvent",
    "Notification",
    "NotificationTemplate",
    "AuditLog",
]