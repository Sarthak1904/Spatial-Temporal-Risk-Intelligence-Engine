"""Event ingestion and retrieval endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.api.deps import require_role
from backend.app.core.config import get_settings
from backend.app.core.rate_limit import limiter
from backend.app.db.session import get_db
from backend.app.models.user import UserRole
from backend.app.schemas.event import EventResponse, EventUploadRequest
from backend.app.services.ingestion import ingest_events

router = APIRouter(prefix="/events")
settings = get_settings()


@router.post("/upload")
@limiter.limit(settings.rate_limit_analyst)
def upload_events(
    request: Request,
    payload: EventUploadRequest,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(UserRole.admin, UserRole.analyst)),
) -> dict[str, int]:
    """Bulk-upload event records."""
    _ = request
    inserted = ingest_events(db, payload.events)
    return {"inserted": inserted}


@router.get("", response_model=list[EventResponse])
@limiter.limit(settings.rate_limit_public)
def list_events(
    request: Request,
    db: Session = Depends(get_db),
    limit: int = Query(default=500, le=5000),
    event_type: str | None = Query(default=None),
    start_datetime: datetime | None = Query(default=None),
    end_datetime: datetime | None = Query(default=None),
) -> list[EventResponse]:
    """Return events with optional temporal and type filtering."""
    _ = request
    rows = db.execute(
        text(
            """
            SELECT
                id,
                event_type,
                event_timestamp,
                ST_X(geom::geometry) AS longitude,
                ST_Y(geom::geometry) AS latitude,
                attributes_json
            FROM events
            WHERE (:event_type IS NULL OR event_type = :event_type)
              AND (:start_datetime IS NULL OR event_timestamp >= :start_datetime)
              AND (:end_datetime IS NULL OR event_timestamp <= :end_datetime)
            ORDER BY event_timestamp DESC
            LIMIT :limit
            """
        ),
        {
            "event_type": event_type,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "limit": limit,
        },
    ).mappings()
    return [EventResponse(**row) for row in rows]
