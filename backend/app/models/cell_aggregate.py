"""Daily aggregated counts by H3 cell."""

from datetime import datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class CellAggregate(Base):
    """Daily aggregation metrics for each H3 index."""

    __tablename__ = "cell_aggregates"
    __table_args__ = (UniqueConstraint("h3_index", "time_bucket", name="uq_cell_aggregates_h3_time"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    h3_index: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    time_bucket: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False)
    rolling_7d_avg: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    growth_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
