# SQL Tuning Notes

This directory contains profiling scripts for high-frequency geospatial read paths.

## Scripts

- `explain_tile_query.sql`: benchmarks vector tile generation (`ST_AsMVT`) against `mv_daily_risk`.
- `explain_hotspots_query.sql`: benchmarks hotspot query with temporal range and risk/anomaly filters.

## How to run

```bash
psql "$DATABASE_URL" -f backend/sql/performance/explain_tile_query.sql
psql "$DATABASE_URL" -f backend/sql/performance/explain_hotspots_query.sql
```

## Review checklist

- Ensure `Bitmap Index Scan` or `Index Scan` is used on:
  - `idx_mv_daily_risk_time`
  - `idx_mv_daily_risk_level`
  - `idx_mv_daily_risk_geom_gist`
  - `idx_risk_scores_time_bucket`
  - `idx_risk_scores_level`
- Watch for high `Heap Blocks: exact` with poor selectivity.
- Confirm no large `Sort Method: external merge` (indicates memory pressure).
- Validate tile query doesn't repeatedly compute expensive transforms for broad extents.

## Tuning strategy

1. **Predicate pruning first**
   - Always constrain by `time_bucket` and `risk_level` before geometry ops.
2. **Reduce transform overhead**
   - If load is high, store an additional projected geometry column for tile serving.
3. **Materialized view cadence**
   - Refresh after analytics runs; avoid unnecessary frequent refreshes.
4. **Memory tuning**
   - Increase `work_mem` for heavy sort/hash workloads in reporting windows.
5. **Timescale chunking**
   - Keep chunk interval aligned to ingestion rate and retention policy.
