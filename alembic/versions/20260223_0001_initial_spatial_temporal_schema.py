"""Initial spatial temporal schema."""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260223_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create base schema, indexes, hypertable, and materialized view."""
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'risk_level') THEN
            CREATE TYPE risk_level AS ENUM ('low', 'medium', 'high', 'critical');
          END IF;
          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
            CREATE TYPE user_role AS ENUM ('admin', 'analyst', 'public');
          END IF;
        END $$;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
            event_type VARCHAR(64) NOT NULL,
            event_timestamp TIMESTAMPTZ NOT NULL,
            geom GEOMETRY(Point, 4326) NOT NULL,
            attributes_json JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (event_timestamp, id)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_events_geom_gist ON events USING GIST (geom)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (event_timestamp DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events (event_type)")
    op.execute("SELECT create_hypertable('events', by_range('event_timestamp', INTERVAL '1 month'), if_not_exists => TRUE)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) NOT NULL UNIQUE,
            hashed_password VARCHAR(255) NOT NULL,
            role user_role NOT NULL DEFAULT 'public',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS h3_cells (
            h3_index VARCHAR(32) PRIMARY KEY,
            resolution INTEGER NOT NULL,
            geom GEOMETRY(Polygon, 4326) NOT NULL
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_h3_cells_geom_gist ON h3_cells USING GIST (geom)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_h3_cells_resolution ON h3_cells (resolution)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cell_aggregates (
            id BIGSERIAL PRIMARY KEY,
            h3_index VARCHAR(32) NOT NULL,
            time_bucket DATE NOT NULL,
            event_count INTEGER NOT NULL,
            rolling_7d_avg DOUBLE PRECISION NOT NULL DEFAULT 0,
            growth_rate DOUBLE PRECISION NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_cell_aggregates_h3_time UNIQUE (h3_index, time_bucket),
            CONSTRAINT fk_cell_aggregates_h3 FOREIGN KEY (h3_index) REFERENCES h3_cells(h3_index)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_cell_aggregates_h3_index ON cell_aggregates (h3_index)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_cell_aggregates_time_bucket ON cell_aggregates (time_bucket DESC)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS risk_scores (
            id BIGSERIAL PRIMARY KEY,
            h3_index VARCHAR(32) NOT NULL,
            time_bucket DATE NOT NULL,
            risk_score DOUBLE PRECISION NOT NULL,
            risk_level risk_level NOT NULL,
            CONSTRAINT uq_risk_scores_h3_time UNIQUE (h3_index, time_bucket),
            CONSTRAINT fk_risk_scores_h3 FOREIGN KEY (h3_index) REFERENCES h3_cells(h3_index)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_risk_scores_h3_index ON risk_scores (h3_index)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_risk_scores_time_bucket ON risk_scores (time_bucket DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_risk_scores_level ON risk_scores (risk_level)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS anomaly_flags (
            id BIGSERIAL PRIMARY KEY,
            h3_index VARCHAR(32) NOT NULL,
            time_bucket DATE NOT NULL,
            anomaly_score DOUBLE PRECISION NOT NULL,
            flagged BOOLEAN NOT NULL DEFAULT FALSE,
            CONSTRAINT uq_anomaly_flags_h3_time UNIQUE (h3_index, time_bucket),
            CONSTRAINT fk_anomaly_flags_h3 FOREIGN KEY (h3_index) REFERENCES h3_cells(h3_index)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_anomaly_flags_h3_index ON anomaly_flags (h3_index)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_anomaly_flags_time_bucket ON anomaly_flags (time_bucket DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_anomaly_flags_flagged ON anomaly_flags (flagged)")

    op.execute(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_risk AS
        SELECT
            rs.h3_index,
            rs.time_bucket,
            rs.risk_score,
            rs.risk_level,
            ca.event_count,
            ca.rolling_7d_avg,
            ca.growth_rate,
            COALESCE(af.flagged, false) AS flagged,
            h3.geom
        FROM risk_scores rs
        JOIN cell_aggregates ca
          ON ca.h3_index = rs.h3_index
         AND ca.time_bucket = rs.time_bucket
        JOIN h3_cells h3
          ON h3.h3_index = rs.h3_index
        LEFT JOIN anomaly_flags af
          ON af.h3_index = rs.h3_index
         AND af.time_bucket = rs.time_bucket;
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_daily_risk_h3_time ON mv_daily_risk (h3_index, time_bucket)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_mv_daily_risk_geom_gist ON mv_daily_risk USING GIST (geom)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_mv_daily_risk_time ON mv_daily_risk (time_bucket DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_mv_daily_risk_level ON mv_daily_risk (risk_level)")


def downgrade() -> None:
    """Drop platform schema objects."""
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_daily_risk")
    op.execute("DROP TABLE IF EXISTS anomaly_flags")
    op.execute("DROP TABLE IF EXISTS risk_scores")
    op.execute("DROP TABLE IF EXISTS cell_aggregates")
    op.execute("DROP TABLE IF EXISTS h3_cells")
    op.execute("DROP TABLE IF EXISTS events")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TYPE IF EXISTS risk_level")
    op.execute("DROP TYPE IF EXISTS user_role")
