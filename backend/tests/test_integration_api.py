"""Integration tests for ingestion, analytics trigger, and tile serving."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.core.security import get_password_hash
from backend.app.db.session import SessionLocal


def create_token(client: TestClient, username: str = "analyst_1", role: str = "analyst") -> str:
    """Insert user and request JWT token for authenticated tests."""
    with SessionLocal() as db:
        db.execute(
            text(
                """
                INSERT INTO users (username, hashed_password, role)
                VALUES (:username, :hashed_password, :role::user_role)
                """
            ),
            {"username": username, "hashed_password": get_password_hash("secure-pass-123"), "role": role},
        )
        db.commit()
    response = client.post("/v1/auth/token", json={"username": username, "password": "secure-pass-123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_event_ingestion_and_listing(client: TestClient) -> None:
    """Upload spatial-temporal events then query them back."""
    token = create_token(client)
    now = datetime.now(UTC).replace(microsecond=0)

    upload_response = client.post(
        "/v1/events/upload",
        json={
            "events": [
                {
                    "event_type": "fire_incident",
                    "event_timestamp": now.isoformat(),
                    "longitude": -97.0,
                    "latitude": 38.6,
                    "attributes_json": {"severity": "moderate", "source": "ops-feed-a"},
                },
                {
                    "event_type": "fire_incident",
                    "event_timestamp": (now - timedelta(hours=1)).isoformat(),
                    "longitude": -97.1,
                    "latitude": 38.4,
                    "attributes_json": {"severity": "high", "source": "ops-feed-a"},
                },
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_response.status_code == 200
    assert upload_response.json()["inserted"] == 2

    list_response = client.get("/v1/events", params={"event_type": "fire_incident", "limit": 10})
    assert list_response.status_code == 200
    payload = list_response.json()
    assert len(payload) == 2
    assert all(item["event_type"] == "fire_incident" for item in payload)


def test_analytics_endpoint_queues_celery_job(client: TestClient) -> None:
    """Verify analytics API delegates heavy processing to Celery."""
    token = create_token(client, username="analyst_2")
    fake_task = SimpleNamespace(id="task-integration-001")

    with patch("backend.app.api.v1.endpoints.analytics.run_analytics_pipeline.delay", return_value=fake_task):
        response = client.post(
            "/v1/analytics/run",
            params={"resolution": 8},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == {"task_id": "task-integration-001", "status": "queued"}


def test_vector_tile_endpoint_returns_mvt(client: TestClient) -> None:
    """Validate ST_AsMVT tile endpoint produces binary payload."""
    bucket_date = date.today()
    with SessionLocal() as db:
        db.execute(
            text(
                """
                INSERT INTO h3_cells (h3_index, resolution, geom)
                VALUES (
                    'testcell001',
                    8,
                    ST_GeomFromText('POLYGON((-97.2 38.2, -97.2 38.8, -96.8 38.8, -96.8 38.2, -97.2 38.2))', 4326)
                )
                """
            )
        )
        db.execute(
            text(
                """
                INSERT INTO cell_aggregates (h3_index, time_bucket, event_count, rolling_7d_avg, growth_rate)
                VALUES ('testcell001', :bucket_date, 10, 7.5, 0.33)
                """
            ),
            {"bucket_date": bucket_date},
        )
        db.execute(
            text(
                """
                INSERT INTO risk_scores (h3_index, time_bucket, risk_score, risk_level)
                VALUES ('testcell001', :bucket_date, 82.0, 'critical'::risk_level)
                """
            ),
            {"bucket_date": bucket_date},
        )
        db.execute(
            text(
                """
                INSERT INTO anomaly_flags (h3_index, time_bucket, anomaly_score, flagged)
                VALUES ('testcell001', :bucket_date, 2.7, true)
                """
            ),
            {"bucket_date": bucket_date},
        )
        db.execute(text("REFRESH MATERIALIZED VIEW mv_daily_risk"))
        db.commit()

    response = client.get("/v1/tiles/0/0/0.mvt", params={"risk_date": bucket_date.isoformat(), "risk_level": "critical"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.mapbox-vector-tile"
    assert len(response.content) > 0
