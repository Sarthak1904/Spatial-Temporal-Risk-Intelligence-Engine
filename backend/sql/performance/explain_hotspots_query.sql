-- Hotspot feed benchmark for temporal range + risk filter.
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT
    r.h3_index,
    r.time_bucket,
    r.risk_score,
    r.risk_level,
    c.growth_rate,
    COALESCE(a.flagged, false) AS anomaly_flagged
FROM risk_scores r
JOIN cell_aggregates c
  ON c.h3_index = r.h3_index
 AND c.time_bucket = r.time_bucket
LEFT JOIN anomaly_flags a
  ON a.h3_index = r.h3_index
 AND a.time_bucket = r.time_bucket
WHERE r.time_bucket BETWEEN DATE '2026-01-01' AND DATE '2026-02-20'
  AND (r.risk_level IN ('high', 'critical') OR COALESCE(a.flagged, false) = true)
ORDER BY r.time_bucket DESC, r.risk_score DESC
LIMIT 2000;
