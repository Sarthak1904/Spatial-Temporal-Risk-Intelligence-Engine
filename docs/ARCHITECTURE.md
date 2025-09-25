# Architecture

## Data Flow
Event ingestion -> PostGIS/TimescaleDB -> H3 aggregation -> Risk scoring -> MVT tiles -> Dashboard

## Key Design Decisions
- TimescaleDB hypertable for time-partitioned event storage
- H3 resolution 7/8 for stable spatial binning
- Materialized view for tile read path
