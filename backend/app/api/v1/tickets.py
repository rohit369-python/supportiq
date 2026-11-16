"""Ticket management API routes."""

from typing import Annotated, Optional
from uuid import UUID
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database.session import get_db
from app.models.ticket import Ticket, TicketStatusHistory, TicketEvent, TicketStatus, TicketPriority
from app.models.customer import Customer
from app.core.deps import get_current_user, CurrentUser, Perm, require_permissions
from app.schemas.common import PaginatedResponse, MessageResponse
from ai_engine.classification.classifier import TicketClassifier

router = APIRouter(prefix="/tickets", tags=["Tickets"])


class TicketCreate(BaseModel):
    customer_id: UUID
    subject: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1)
    priority: Optional[str] = TicketPriority.MEDIUM.value
    category: Optional[str] = None
    source_channel: str = "portal"
    tags: Optional[list[str]] = None


class TicketUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    assigned_agent_id: Optional[UUID] = None
    tags: Optional[list[str]] = None
    resolution_notes: Optional[str] = None


class TicketOut(BaseModel):
    id: UUID
    ticket_number: str
    organization_id: UUID
    customer_id: UUID
    subject: str
    description: str
    category: Optional[str]
    subcategory: Optional[str]
    intent: Optional[str]
    priority: str
    status: str
    source_channel: str
    assigned_agent_id: Optional[UUID]
    sentiment: Optional[str]
    tags: Optional[list]
    created_at: datetime
    updated_at: datetime
    first_response_at: Optional[datetime]
    resolved_at: Optional[datetime]
    due_at: Optional[datetime]
    ai_classified: bool
    needs_human_review: bool
    ai_confidence: Optional[float]

    model_config = {"from_attributes": True}


VALID_TRANSITIONS = {
    TicketStatus.NEW.value: {TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value, TicketStatus.CLOSED.value},
    TicketStatus.OPEN.value: {
        TicketStatus.IN_PROGRESS.value, TicketStatus.WAITING_CUSTOMER.value,
        TicketStatus.WAITING_INTERNAL.value, TicketStatus.ESCALATED.value,
        TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value,
    },
    TicketStatus.IN_PROGRESS.value: {
        TicketStatus.WAITING_CUSTOMER.value, TicketStatus.WAITING_INTERNAL.value,
        TicketStatus.ESCALATED.value, TicketStatus.RESOLVED.value, TicketStatus.OPEN.value,
    },
    TicketStatus.WAITING_CUSTOMER.value: {
        TicketStatus.IN_PROGRESS.value, TicketStatus.OPEN.value, TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value,
    },
    TicketStatus.WAITING_INTERNAL.value: {
        TicketStatus.IN_PROGRESS.value, TicketStatus.ESCALATED.value, TicketStatus.RESOLVED.value,
    },
    TicketStatus.ESCALATED.value: {
        TicketStatus.IN_PROGRESS.value, TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value,
    },
    TicketStatus.RESOLVED.value: {TicketStatus.CLOSED.value, TicketStatus.REOPENED.value},
    TicketStatus.CLOSED.value: {TicketStatus.REOPENED.value},
    TicketStatus.REOPENED.value: {
        TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value, TicketStatus.RESOLVED.value,
    },
}


async def _generate_ticket_number(db: AsyncSession, org_id: UUID) -> str:
    result = await db.execute(
        select(func.count()).select_from(Ticket).where(Ticket.organization_id == org_id)
    )
    count = result.scalar() or 0
    return f"TKT-{str(org_id)[:8].upper()}-{count + 1:05d}"


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    body: TicketCreate,
    current: Annotated[CurrentUser, Depends(require_permissions(Perm.CREATE_TICKETS))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Verify customer belongs to same org
    result = await db.execute(
        select(Customer).where(
            Customer.id == body.customer_id,
            Customer.organization_id == current.organization_id,
            Customer.is_deleted.is_(False),
        )
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    ticket_number = await _generate_ticket_number(db, current.organization_id)
    ticket = Ticket(
        organization_id=current.organization_id,
        customer_id=body.customer_id,
        ticket_number=ticket_number,
        subject=body.subject,
        description=body.description,
        priority=body.priority or TicketPriority.MEDIUM.value,
        status=TicketStatus.NEW.value,
        source_channel=body.source_channel,
        category=body.category,
        tags=body.tags or [],
    )
    db.add(ticket)
    await db.flush()

    # Status history
    db.add(TicketStatusHistory(
        ticket_id=ticket.id,
        from_status=None,
        to_status=TicketStatus.NEW.value,
        changed_by_id=current.user_id,
    ))
    db.add(TicketEvent(
        ticket_id=ticket.id,
        event_type="created",
        actor_id=current.user_id,
        actor_type="user",
        payload={"source": body.source_channel},
    ))

    # Async AI classification (inline for simplicity; production would use Celery)
    try:
        classifier = TicketClassifier()
        classification = await classifier.classify(body.subject, body.description)
        ticket.intent = classification.intent
        ticket.category = classification.category or body.category
        ticket.subcategory = classification.subcategory
        ticket.ai_confidence = classification.confidence
        ticket.ai_classified = True
        ticket.needs_human_review = classification.confidence < 0.7
        if classification.confidence >= 0.7:
            ticket.status = TicketStatus.OPEN.value
    except Exception:
        ticket.needs_human_review = True

    await db.flush()
    await db.refresh(ticket)
    return TicketOut.model_validate(ticket)


@router.get("", response_model=PaginatedResponse[TicketOut])
async def list_tickets(
    current: Annotated[CurrentUser, Depends(require_permissions(Perm.VIEW_TICKETS))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    assigned_to_me: bool = False,
    search: Optional[str] = None,
):
    filters = [
        Ticket.organization_id == current.organization_id,
        Ticket.is_deleted.is_(False),
    ]
    if status_filter:
        filters.append(Ticket.status == status_filter)
    if priority:
        filters.append(Ticket.priority == priority)
    if assigned_to_me:
        filters.append(Ticket.assigned_agent_id == current.user_id)
    if search:
        filters.append(
            Ticket.subject.ilike(f"%{search}%") | Ticket.ticket_number.ilike(f"%{search}%")
        )

    count_q = select(func.count()).select_from(Ticket).where(and_(*filters))
    total = (await db.execute(count_q)).scalar() or 0

    q = (
        select(Ticket)
        .where(and_(*filters))
        .order_by(Ticket.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(q)
    items = [TicketOut.model_validate(t) for t in result.scalars().all()]
    pages = (total + page_size - 1) // page_size if page_size else 0
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)


@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: UUID,
    current: Annotated[CurrentUser, Depends(require_permissions(Perm.VIEW_TICKETS))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.organization_id == current.organization_id,
            Ticket.is_deleted.is_(False),
        )
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TicketOut.model_validate(ticket)


@router.patch("/{ticket_id}", response_model=TicketOut)
async def update_ticket(
    ticket_id: UUID,
    body: TicketUpdate,
    current: Annotated[CurrentUser, Depends(require_permissions(Perm.UPDATE_TICKETS))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.organization_id == current.organization_id,
            Ticket.is_deleted.is_(False),
        )
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    data = body.model_dump(exclude_unset=True)

    if "status" in data and data["status"] != ticket.status:
        allowed = VALID_TRANSITIONS.get(ticket.status, set())
        if data["status"] not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status transition from {ticket.status} to {data['status']}",
            )
        db.add(TicketStatusHistory(
            ticket_id=ticket.id,
            from_status=ticket.status,
            to_status=data["status"],
            changed_by_id=current.user_id,
        ))
        if data["status"] == TicketStatus.RESOLVED.value:
            ticket.resolved_at = datetime.now(timezone.utc)
        if data["status"] == TicketStatus.CLOSED.value:
            ticket.closed_at = datetime.now(timezone.utc)

    if "priority" in data and data["priority"] != ticket.priority:
        # AI must not silently downgrade critical
        if ticket.priority == TicketPriority.CRITICAL.value and data["priority"] != TicketPriority.CRITICAL.value:
            if not current.has_permission(Perm.ASSIGN_TICKETS):
                raise HTTPException(status_code=403, detail="Cannot downgrade critical ticket without permission")

    for field, value in data.items():
        setattr(ticket, field, value)

    db.add(TicketEvent(
        ticket_id=ticket.id,
        event_type="updated",
        actor_id=current.user_id,
        actor_type="user",
        payload=data,
    ))
    await db.flush()
    await db.refresh(ticket)
    return TicketOut.model_validate(ticket)