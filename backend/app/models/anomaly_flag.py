"""Anomaly spike flags derived from z-score."""

from datetime import datetime

from sqlalchemy import Boolean, Date, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class AnomalyFlag(Base):
    """Stores anomaly detection output per cell/day."""

    __tablename__ = "anomaly_flags"
    __table_args__ = (UniqueConstraint("h3_index", "time_bucket", name="uq_anomaly_flags_h3_time"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    h3_index: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    time_bucket: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
