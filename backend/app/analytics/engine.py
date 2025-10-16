"""Spatial-temporal analytics pipeline. Computes H3 aggregates, risk scores, anomalies."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from statistics import mean, pstdev

import h3
from shapely.geometry import Polygon
from sqlalchemy import text
from sqlalchemy.orm import Session


class AnalyticsEngine:
    """Computes H3 aggregates, risk score, and anomalies."""

    def run_pipeline(self, db: Session, start_dt: datetime, end_dt: datetime, resolution: int = 8) -> None:
        """Run full analytics pipeline in deterministic order."""
        self.aggregate_events(db, start_dt, end_dt, resolution=resolution)
        self.compute_risk_scores(db, start_dt.date(), end_dt.date())
        self.detect_anomalies(db, start_dt.date(), end_dt.date())
        self.refresh_materialized_views(db)

    def aggregate_events(self, db: Session, start_dt: datetime, end_dt: datetime, resolution: int = 8) -> None:
        """Aggregate events by day and H3 index."""
        rows = db.execute(
            text(
                """
                SELECT
                    id,
                    date_trunc('day', event_timestamp)::date AS day_bucket,
                    ST_Y(geom::geometry) AS latitude,
                    ST_X(geom::geometry) AS longitude
                FROM events
                WHERE event_timestamp >= :start_dt
                  AND event_timestamp < :end_dt
                """
            ),
            {"start_dt": start_dt, "end_dt": end_dt},
        ).all()

        grouped: dict[tuple[str, date], int] = defaultdict(int)
        h3_registry: set[str] = set()
        for row in rows:
            h3_idx = h3.latlng_to_cell(row.latitude, row.longitude, resolution)
            grouped[(h3_idx, row.day_bucket)] += 1
            h3_registry.add(h3_idx)

        for h3_idx in h3_registry:
            cell_boundary = h3.cell_to_boundary(h3_idx)
            polygon = Polygon([(lng, lat) for lat, lng in cell_boundary])
            db.execute(
                text(
                    """
                    INSERT INTO h3_cells (h3_index, resolution, geom)
                    VALUES (:h3_index, :resolution, ST_GeomFromText(:wkt, 4326))
                    ON CONFLICT (h3_index) DO NOTHING
                    """
                ),
                {"h3_index": h3_idx, "resolution": resolution, "wkt": polygon.wkt},
            )

        for (h3_idx, bucket), count in grouped.items():
            db.execute(
                text(
                    """
                    INSERT INTO cell_aggregates (h3_index, time_bucket, event_count, rolling_7d_avg, growth_rate, created_at)
                    VALUES (:h3_index, :time_bucket, :event_count, 0, 0, NOW())
                    ON CONFLICT (h3_index, time_bucket)
                    DO UPDATE SET event_count = EXCLUDED.event_count
                    """
                ),
                {"h3_index": h3_idx, "time_bucket": bucket, "event_count": count},
            )

        db.execute(
            text(
                """
                WITH metrics AS (
                    SELECT
                        id,
                        event_count,
                        AVG(event_count) OVER (
                            PARTITION BY h3_index
                            ORDER BY time_bucket
                            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                        ) AS rolling_avg,
                        AVG(event_count) OVER (
                            PARTITION BY h3_index
                            ORDER BY time_bucket
                            ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
                        ) AS prev_7d_avg
                    FROM cell_aggregates
                    WHERE time_bucket >= :start_date
                      AND time_bucket <= :end_date
                )
                UPDATE cell_aggregates ca
                SET rolling_7d_avg = COALESCE(m.rolling_avg, 0),
                    growth_rate = CASE
                        WHEN COALESCE(m.prev_7d_avg, 0) = 0 THEN 0
                        ELSE (m.event_count - m.prev_7d_avg) / m.prev_7d_avg
                    END
                FROM metrics m
                WHERE ca.id = m.id
                """
            ),
            {"start_date": start_dt.date(), "end_date": end_dt.date()},
        )
        db.commit()

    def compute_risk_scores(self, db: Session, start_date: date, end_date: date) -> None:
        """Compute and normalize risk score from aggregate metrics."""
        db.execute(
            text(
                """
                WITH base AS (
                    SELECT
                        h3_index,
                        time_bucket,
                        event_count,
                        growth_rate,
                        rolling_7d_avg,
                        ((event_count * 0.5) + (growth_rate * 0.3) + (rolling_7d_avg * 0.2))::float AS raw_score
                    FROM cell_aggregates
                    WHERE time_bucket >= :start_date
                      AND time_bucket <= :end_date
                ),
                bounds AS (
                    SELECT COALESCE(MIN(raw_score), 0) AS min_score, COALESCE(MAX(raw_score), 0) AS max_score
                    FROM base
                )
                INSERT INTO risk_scores (h3_index, time_bucket, risk_score, risk_level)
                SELECT
                    b.h3_index,
                    b.time_bucket,
                    CASE
                        WHEN bo.max_score = bo.min_score THEN 0
                        ELSE ((b.raw_score - bo.min_score) / NULLIF((bo.max_score - bo.min_score), 0)) * 100
                    END AS risk_score,
                    CASE
                        WHEN
                            (CASE WHEN bo.max_score = bo.min_score THEN 0 ELSE ((b.raw_score - bo.min_score) / NULLIF((bo.max_score - bo.min_score), 0)) * 100 END) <= 25
                            THEN 'low'
                        WHEN
                            (CASE WHEN bo.max_score = bo.min_score THEN 0 ELSE ((b.raw_score - bo.min_score) / NULLIF((bo.max_score - bo.min_score), 0)) * 100 END) <= 50
                            THEN 'medium'
                        WHEN
                            (CASE WHEN bo.max_score = bo.min_score THEN 0 ELSE ((b.raw_score - bo.min_score) / NULLIF((bo.max_score - bo.min_score), 0)) * 100 END) <= 75
                            THEN 'high'
                        ELSE 'critical'
                    END::risk_level
                FROM base b
                CROSS JOIN bounds bo
                ON CONFLICT (h3_index, time_bucket)
                DO UPDATE SET
                    risk_score = EXCLUDED.risk_score,
                    risk_level = EXCLUDED.risk_level
                """
            ),
            {"start_date": start_date, "end_date": end_date},
        )
        db.commit()

    def detect_anomalies(self, db: Session, start_date: date, end_date: date) -> None:
        """Detect anomalies using z-score over daily event count."""
        rows = db.execute(
            text(
                """
                SELECT h3_index, time_bucket, event_count
                FROM cell_aggregates
                WHERE time_bucket >= :start_date
                  AND time_bucket <= :end_date
                ORDER BY h3_index, time_bucket
                """
            ),
            {"start_date": start_date, "end_date": end_date},
        ).all()

        grouped: dict[str, list[tuple[date, int]]] = defaultdict(list)
        for row in rows:
            grouped[row.h3_index].append((row.time_bucket, row.event_count))

        for h3_idx, series in grouped.items():
            counts = [count for _, count in series]
            mu = mean(counts) if counts else 0
            sigma = pstdev(counts) if len(counts) > 1 else 0
            for bucket, count in series:
                z_score = 0.0 if sigma == 0 else (count - mu) / sigma
                db.execute(
                    text(
                        """
                        INSERT INTO anomaly_flags (h3_index, time_bucket, anomaly_score, flagged)
                        VALUES (:h3_index, :time_bucket, :anomaly_score, :flagged)
                        ON CONFLICT (h3_index, time_bucket)
                        DO UPDATE SET
                            anomaly_score = EXCLUDED.anomaly_score,
                            flagged = EXCLUDED.flagged
                        """
                    ),
                    {
                        "h3_index": h3_idx,
                        "time_bucket": bucket,
                        "anomaly_score": z_score,
                        "flagged": z_score >= 2.0,
                    },
                )
        db.commit()

    def refresh_materialized_views(self, db: Session) -> None:
        """Refresh precomputed reporting views used by APIs and tiles."""
        db.execute(text("REFRESH MATERIALIZED VIEW mv_daily_risk"))
        db.commit()

