"""Analytics trigger endpoint."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query, Request

from backend.app.api.deps import require_role
from backend.app.core.config import get_settings
from backend.app.core.rate_limit import limiter
from backend.app.models.user import UserRole
from backend.app.schemas.analytics import AnalyticsRunResponse
from backend.app.worker.tasks import run_analytics_pipeline

router = APIRouter(prefix="/analytics")
settings = get_settings()


@router.post("/run", response_model=AnalyticsRunResponse)
@limiter.limit(settings.rate_limit_analyst)
def run_analytics(
    request: Request,
    start_datetime: datetime | None = Query(default=None),
    end_datetime: datetime | None = Query(default=None),
    resolution: int = Query(default=8, ge=7, le=8),
    _: object = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> AnalyticsRunResponse:
    """Schedule analytics pipeline in Celery."""
    _ = request
    end_dt = end_datetime or datetime.now(UTC)
    start_dt = start_datetime or (end_dt - timedelta(days=30))
    task = run_analytics_pipeline.delay(start_dt.isoformat(), end_dt.isoformat(), resolution)
    return AnalyticsRunResponse(task_id=task.id, status="queued")
