"""Service health endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.cache import redis_client
from backend.app.db.session import get_db

router = APIRouter(prefix="/health")


@router.get("/live")
def liveness() -> dict[str, str]:
    """Liveness probe endpoint."""
    return {"status": "alive"}


@router.get("/ready")
def readiness(db: Session = Depends(get_db)) -> dict[str, str]:
    """Readiness probe for DB and Redis."""
    db.execute(text("SELECT 1"))
    redis_client.ping()
    return {"status": "ready"}
