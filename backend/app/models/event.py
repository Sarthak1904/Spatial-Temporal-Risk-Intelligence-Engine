"""Event storage model."""

from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Event(Base):
    """Incoming raw event stream persisted in PostGIS."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, nullable=False, index=True)
    geom: Mapped[str] = mapped_column(Geometry("POINT", srid=4326, spatial_index=True), nullable=False)
    attributes_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
