"""Risk scoring output model."""

import enum
from datetime import datetime

from sqlalchemy import Date, Enum, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class RiskLevel(enum.StrEnum):
    """Normalized risk classes."""

    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RiskScore(Base):
    """Computed risk score per H3 per day."""

    __tablename__ = "risk_scores"
    __table_args__ = (UniqueConstraint("h3_index", "time_bucket", name="uq_risk_scores_h3_time"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    h3_index: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    time_bucket: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel, name="risk_level"), nullable=False, index=True)
