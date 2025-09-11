"""Event ingestion service functions."""

import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.schemas.event import EventUploadItem


def ingest_events(db: Session, events: list[EventUploadItem]) -> int:
    """Insert validated events in a single transaction."""
    payload = [
        {
            "event_type": item.event_type,
            "event_timestamp": item.event_timestamp,
            "longitude": item.longitude,
            "latitude": item.latitude,
            "attributes_json": json.dumps(item.attributes_json) if item.attributes_json is not None else None,
        }
        for item in events
    ]
    db.execute(
        text(
            """
            INSERT INTO events (event_type, event_timestamp, geom, attributes_json, created_at)
            VALUES (
                :event_type,
                :event_timestamp,
                ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)::geometry,
                CAST(:attributes_json AS jsonb),
                NOW()
            )
            """
        ),
        payload,
    )
    db.commit()
    return len(payload)
