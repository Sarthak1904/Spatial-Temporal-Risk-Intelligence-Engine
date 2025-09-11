"""Hotspot detection read endpoint."""

from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.rate_limit import limiter
from backend.app.db.session import get_db

router = APIRouter(prefix="/hotspots")
settings = get_settings()


@router.get("")
@limiter.limit(settings.rate_limit_public)
def get_hotspots(
    request: Request,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    """Return emerging hotspots for date range."""
    _ = request
    rows = db.execute(
        text(
            """
            SELECT
                r.h3_index,
                r.time_bucket,
                r.risk_score,
                r.risk_level::text AS risk_level,
                c.growth_rate,
                COALESCE(a.flagged, false) AS anomaly_flagged
            FROM risk_scores r
            JOIN cell_aggregates c
              ON c.h3_index = r.h3_index
             AND c.time_bucket = r.time_bucket
            LEFT JOIN anomaly_flags a
              ON a.h3_index = r.h3_index
             AND a.time_bucket = r.time_bucket
            WHERE r.time_bucket BETWEEN :start_date AND :end_date
              AND (r.risk_level IN ('high', 'critical') OR COALESCE(a.flagged, false) = true)
            ORDER BY r.time_bucket DESC, r.risk_score DESC
            """
        ),
        {"start_date": start_date, "end_date": end_date},
    ).mappings()
    return [dict(row) for row in rows]
