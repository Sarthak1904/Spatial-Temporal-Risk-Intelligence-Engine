"""Vector tile endpoint."""

from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.cache import redis_client
from backend.app.core.config import get_settings
from backend.app.core.rate_limit import limiter
from backend.app.db.session import get_db

router = APIRouter(prefix="/tiles")
settings = get_settings()


@router.get("/{z}/{x}/{y}.mvt")
@limiter.limit(settings.rate_limit_public)
def get_risk_tile(
    request: Request,
    z: int,
    x: int,
    y: int,
    db: Session = Depends(get_db),
    risk_date: date | None = Query(default=None),
    risk_level: str | None = Query(default=None),
) -> Response:
    """Serve MVT for risk layers using ST_AsMVT."""
    _ = request
    cache_key = f"tile:{z}:{x}:{y}:{risk_date}:{risk_level}"
    cached = redis_client.get(cache_key)
    if cached:
        return Response(content=cached, media_type="application/vnd.mapbox-vector-tile")

    levels = risk_level.split(",") if risk_level else None
    tile = db.execute(
        text(
            """
            WITH bounds AS (
                SELECT ST_TileEnvelope(:z, :x, :y) AS geom
            ),
            source AS (
                SELECT
                    m.h3_index,
                    m.time_bucket,
                    m.event_count,
                    m.rolling_7d_avg,
                    m.growth_rate,
                    m.risk_score,
                    m.risk_level,
                    m.flagged,
                    ST_AsMVTGeom(ST_Transform(m.geom, 3857), b.geom, 4096, 64, true) AS geom
                FROM mv_daily_risk m
                CROSS JOIN bounds b
                WHERE ST_Intersects(ST_Transform(m.geom, 3857), b.geom)
                  AND (CAST(:risk_date AS DATE) IS NULL OR m.time_bucket = :risk_date)
                  AND (
                      CAST(:risk_levels AS text[]) IS NULL
                      OR m.risk_level::text = ANY(CAST(:risk_levels AS text[]))
                  )
            )
            SELECT ST_AsMVT(source, 'risk', 4096, 'geom') AS tile
            FROM source
            """
        ),
        {"z": z, "x": x, "y": y, "risk_date": risk_date, "risk_levels": levels},
    ).scalar_one_or_none()

    binary_tile = tile or b""
    redis_client.setex(cache_key, 300, binary_tile)
    return Response(content=binary_tile, media_type="application/vnd.mapbox-vector-tile")
