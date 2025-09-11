"""Analytics related schemas."""

from datetime import date

from pydantic import BaseModel


class AnalyticsRunResponse(BaseModel):
    """Response body after scheduling analytics pipeline."""

    task_id: str
    status: str


class RiskCellResponse(BaseModel):
    """Risk record with operational metrics."""

    h3_index: str
    time_bucket: date
    event_count: int
    rolling_7d_avg: float
    growth_rate: float
    risk_score: float
    risk_level: str
    anomaly_flagged: bool
