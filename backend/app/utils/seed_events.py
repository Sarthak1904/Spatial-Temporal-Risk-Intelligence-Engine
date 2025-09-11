"""CLI utility to seed events from a CSV file."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

from backend.app.db.session import SessionLocal
from backend.app.schemas.event import EventUploadItem
from backend.app.services.ingestion import ingest_events


def parse_args() -> argparse.Namespace:
    """Read CSV file location and delimiter options."""
    parser = argparse.ArgumentParser(description="Bulk-load events from CSV.")
    parser.add_argument("--csv", required=True, help="Path to CSV file.")
    parser.add_argument("--delimiter", default=",", help="CSV delimiter. Default is ','.")
    return parser.parse_args()


def parse_row(row: dict[str, str]) -> EventUploadItem:
    """Transform CSV row into validated schema object."""
    attrs_raw = row.get("attributes_json")
    attributes = json.loads(attrs_raw) if attrs_raw else None
    return EventUploadItem(
        event_type=row["event_type"],
        event_timestamp=datetime.fromisoformat(row["event_timestamp"]),
        longitude=float(row["longitude"]),
        latitude=float(row["latitude"]),
        attributes_json=attributes,
    )


def load_events(csv_path: Path, delimiter: str) -> list[EventUploadItem]:
    """Load and validate events from CSV."""
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        return [parse_row(row) for row in reader]


def main() -> None:
    """Entrypoint for event seed utility."""
    args = parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file does not exist: {csv_path}")

    events = load_events(csv_path, args.delimiter)
    if not events:
        print("No rows found in CSV. Nothing to ingest.")
        return

    with SessionLocal() as db:
        inserted = ingest_events(db, events)
    print(f"Inserted {inserted} event records from {csv_path}.")


if __name__ == "__main__":
    main()
