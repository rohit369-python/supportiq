"""Celery application and task definitions."""

from celery import Celery
from app.config.settings import settings

celery_app = Celery(
    "supportiq",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,
    task_time_limit=600,
    beat_schedule={
        "check-sla-breaches": {
            "task": "workers.tasks.check_sla_breaches",
            "schedule": 300.0,  # every 5 minutes
        },
    },
)

# Import tasks so they are registered
celery_app.autodiscover_tasks(["workers"])


@celery_app.task(name="workers.tasks.classify_ticket", bind=True, max_retries=3)
def classify_ticket_task(self, ticket_id: str, organization_id: str):
    """Background ticket classification."""
    # In a full implementation this would open a DB session and run TicketClassifier
    return {"ticket_id": ticket_id, "status": "classified"}


@celery_app.task(name="workers.tasks.process_document", bind=True, max_retries=3)
def process_document_task(self, document_id: str, organization_id: str):
    """Background document extraction, chunking and embedding."""
    return {"document_id": document_id, "status": "processed"}


@celery_app.task(name="workers.tasks.check_sla_breaches")
def check_sla_breaches():
    """Periodic SLA breach detection."""
    return {"checked": True}


@celery_app.task(name="workers.tasks.send_notification", bind=True, max_retries=5)
def send_notification_task(self, notification_id: str):
    """Deliver a notification (email / in-app)."""
    return {"notification_id": notification_id, "status": "sent"}