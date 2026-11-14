import os
from celery import Celery
from backend.app.core.config import settings

celery_app = Celery(
    "documind_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=4,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)


@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, document_id: str):
    """Celery background worker task for document processing."""
    from backend.app.database.session import SessionLocal
    from backend.app.services.pipeline import pipeline

    db = SessionLocal()
    try:
        pipeline.process_document(document_id, db)
    except Exception as exc:
        # Retry with backoff
        raise self.retry(exc=exc, countdown=10)
    finally:
        db.close()

