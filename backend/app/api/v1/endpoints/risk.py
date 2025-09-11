"""Risk read endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.rate_limit import limiter
from backend.app.db.session import get_db
from backend.app.schemas.analytics import RiskCellResponse

router = APIRouter(prefix="/risk")
settings = get_settings()


@router.get("/{risk_date}", response_model=list[RiskCellResponse])
@limiter.limit(settings.rate_limit_public)
def get_risk_for_date(
    request: Request,
    risk_date: date = Path(...),
    db: Session = Depends(get_db),
) -> list[RiskCellResponse]:
    """Return scored H3 cells for a specific day."""
    _ = request
    rows = db.execute(
        text(
            """
            SELECT
                rs.h3_index,
                rs.time_bucket,
                ca.event_count,
                ca.rolling_7d_avg,
                ca.growth_rate,
                rs.risk_score,
                rs.risk_level::text AS risk_level,
                COALESCE(af.flagged, false) AS anomaly_flagged
            FROM risk_scores rs
            JOIN cell_aggregates ca
              ON ca.h3_index = rs.h3_index
             AND ca.time_bucket = rs.time_bucket
            LEFT JOIN anomaly_flags af
              ON af.h3_index = rs.h3_index
             AND af.time_bucket = rs.time_bucket
            WHERE rs.time_bucket = :risk_date
            ORDER BY rs.risk_score DESC
            """
        ),
        {"risk_date": risk_date},
    ).mappings()
    return [RiskCellResponse(**row) for row in rows]
