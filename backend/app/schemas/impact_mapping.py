"""Pydantic schemas for deterministic Supply Chain Impact Mapping."""

from pydantic import BaseModel, Field


class ImpactMappingEvent(BaseModel):
    id: int
    title: str
    description: str | None = None
    category: str | None = None
    event_type: str | None = None
    location: str | None = None
    source: str | None = None


class ImpactMappingPrediction(BaseModel):
    predicted_risk: str | None = None
    predicted_severity: str | None = None
    confidence_score: float | None = None


class ImpactMappingRisk(BaseModel):
    id: int
    severity: str | None = None
    risk_type: str | None = None
    risk_score: float | None = None
    status: str | None = None
    created_at: str | None = None
    prediction: ImpactMappingPrediction | None = None


class ImpactMapItem(BaseModel):
    dependency: str
    category: str
    relevance: str
    matched_terms: list[str] = Field(default_factory=list)
    matched_on: str | None = None
    supply_chain_areas: list[str] = Field(default_factory=list)
    potential_impacts: list[str] = Field(default_factory=list)
    verification_checks: list[str] = Field(default_factory=list)


class ImpactMapResponse(BaseModel):
    risk_id: int
    event_id: int | None = None
    company_available: bool = False
    company_name: str | None = None
    industry: str | None = None
    risk: ImpactMappingRisk | None = None
    event: ImpactMappingEvent | None = None
    relevance: str
    relevance_reason: str | None = None
    summary: str
    mappings: list[ImpactMapItem] = Field(default_factory=list)
    data_limitations: list[str] = Field(default_factory=list)
