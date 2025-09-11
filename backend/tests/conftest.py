"""Integration test fixtures."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.main import app
from backend.app.db.session import SessionLocal


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """Provide API test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_database() -> Generator[None, None, None]:
    """Keep integration tests isolated by truncating mutable tables."""
    with SessionLocal() as db:
        db.execute(
            text(
                """
                TRUNCATE TABLE
                    anomaly_flags,
                    risk_scores,
                    cell_aggregates,
                    h3_cells,
                    events,
                    users
                RESTART IDENTITY CASCADE
                """
            )
        )
        db.commit()
    yield
