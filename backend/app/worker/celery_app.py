"""Celery app setup."""

from celery import Celery

from backend.app.core.config import get_settings

settings = get_settings()

celery_app = Celery("risk_intelligence_engine", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_routes={"backend.app.worker.tasks.run_analytics_pipeline": {"queue": "analytics"}},
    task_track_started=True,
)
