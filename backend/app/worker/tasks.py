"""Background tasks for heavy analytics operations."""

from datetime import datetime

from backend.app.analytics.engine import AnalyticsEngine
from backend.app.db.session import SessionLocal
from backend.app.worker.celery_app import celery_app

analytics_engine = AnalyticsEngine()


@celery_app.task(name="backend.app.worker.tasks.run_analytics_pipeline")
def run_analytics_pipeline(start_datetime: str, end_datetime: str, resolution: int = 8) -> str:
    """Execute full analytics pipeline. Retries on transient DB errors."""
    db = SessionLocal()
    try:
        analytics_engine.run_pipeline(
            db=db,
            start_dt=datetime.fromisoformat(start_datetime),
            end_dt=datetime.fromisoformat(end_datetime),
            resolution=resolution,
        )
        return "completed"
    finally:
        db.close()

