-- Tile query benchmark for ST_AsMVT path.
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
WITH bounds AS (
    SELECT ST_TileEnvelope(7, 35, 49) AS geom
),
source AS (
    SELECT
        m.h3_index,
        m.time_bucket,
        m.event_count,
        m.rolling_7d_avg,
        m.growth_rate,
        m.risk_score,
        m.risk_level,
        m.flagged,
        ST_AsMVTGeom(ST_Transform(m.geom, 3857), b.geom, 4096, 64, true) AS geom
    FROM mv_daily_risk m
    CROSS JOIN bounds b
    WHERE ST_Intersects(ST_Transform(m.geom, 3857), b.geom)
      AND m.time_bucket = DATE '2026-02-20'
      AND m.risk_level::text = ANY(ARRAY['high', 'critical'])
)
SELECT ST_AsMVT(source, 'risk', 4096, 'geom')
FROM source;
