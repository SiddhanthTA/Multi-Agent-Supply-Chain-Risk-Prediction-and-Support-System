"""Pydantic schemas for deterministic risk correlation responses."""

from pydantic import BaseModel, Field


class RiskCorrelationItem(BaseModel):
    risk_id: int
    event_id: int
    event_title: str
    severity: str | None = None
    risk_type: str | None = None
    location: str | None = None
    event_category: str | None = None
    correlation_score: int
    relationship_level: str
    relationship_label: str
    reasons: list[str] = Field(default_factory=list)
    shared_company_dependencies: list[str] = Field(default_factory=list)
    days_apart: float | None = None


class RiskCorrelationResponse(BaseModel):
    risk_id: int
    event_id: int | None = None
    correlations: list[RiskCorrelationItem] = Field(default_factory=list)
    total_candidates_considered: int = 0
    analysis_window_days: int
    message: str | None = None
    disclaimer: str | None = None
    company_context_available: bool = False
