"""Event schema definitions."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EventUploadItem(BaseModel):
    """One event feature for ingestion."""

    event_type: str = Field(min_length=2, max_length=64)
    event_timestamp: datetime
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)
    attributes_json: dict[str, Any] | None = None


class EventUploadRequest(BaseModel):
    """Bulk upload request."""

    events: list[EventUploadItem]


class EventResponse(BaseModel):
    """Serialized event record."""

    id: int
    event_type: str
    event_timestamp: datetime
    longitude: float
    latitude: float
    attributes_json: dict[str, Any] | None
