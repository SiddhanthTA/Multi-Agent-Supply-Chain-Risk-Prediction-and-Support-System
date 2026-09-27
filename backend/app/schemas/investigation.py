from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class InvestigationActor(BaseModel):
    user_id: int
    role: str


class InvestigationStatement(BaseModel):
    text: str = Field(min_length=1, max_length=1200)
    statement_type: Literal[
        "fact",
        "model_prediction",
        "platform_recommendation",
        "agent_interpretation",
    ]
    evidence_refs: list[str] = Field(min_length=1, max_length=5)
    evidence_quotes: list[str] = Field(min_length=1, max_length=3)


class InvestigationSections(BaseModel):
    investigation_summary: list[InvestigationStatement] = Field(min_length=1, max_length=6)
    why_this_matters: list[InvestigationStatement] = Field(min_length=1, max_length=6)
    supporting_evidence: list[InvestigationStatement] = Field(min_length=1, max_length=8)
    related_intelligence: list[InvestigationStatement] = Field(max_length=6)
    what_to_investigate_next: list[InvestigationStatement] = Field(min_length=1, max_length=6)


class InvestigationEvidence(BaseModel):
    ref: str
    evidence_type: Literal[
        "event",
        "risk",
        "prediction",
        "platform_recommendation",
        "related_event",
        "location_context",
        "correlation",
        "company_context",
        "company_relevance",
    ]
    label: str
    data: dict


class InvestigationTarget(BaseModel):
    risk_id: int
    event_id: int


class InvestigationModel(BaseModel):
    provider: str
    name: str
    quantization: str | None = None


class InvestigationResponse(BaseModel):
    investigation_id: str
    target: InvestigationTarget
    generated_at: datetime
    model: InvestigationModel
    sections: InvestigationSections
    evidence: list[InvestigationEvidence]
    warnings: list[str]
    decision_support_only: bool = True


class InvestigationGeneration(BaseModel):
    sections: InvestigationSections


class RiskReportStatus(BaseModel):
    """Which AI reports already exist for a risk, for the current user."""

    risk_id: int
    investigation_exists: bool = False
    response_plan_exists: bool = False


class ResponsePlanOption(BaseModel):
    name: str
    what_to_check: list[str] = Field(default_factory=list)
    why: str
    information_required: list[str] = Field(default_factory=list)


class ResponsePlanPlatformRecommendation(BaseModel):
    title: str
    text: str
    priority: str | None = None
    status: str | None = None


class ResponsePlanResponse(BaseModel):
    risk_id: int
    event_id: int
    scenario: str
    generated_by: str = "runtime-context-response-planner"
    is_demo_template: bool = False
    company_context_available: bool
    company_name: str | None = None
    company_industry: str | None = None
    company_relevance: str | None = None
    matched_dependencies: list[str] = Field(default_factory=list)
    risk_summary: str
    response_objective: str
    immediate_checks: list[str] = Field(default_factory=list)
    response_options: list[ResponsePlanOption] = Field(default_factory=list)
    information_required: list[str] = Field(default_factory=list)
    escalation_conditions: list[str] = Field(default_factory=list)
    responsible_areas: list[str] = Field(default_factory=list)
    platform_recommendation: ResponsePlanPlatformRecommendation | None = None
    notes: list[str] = Field(default_factory=list)
    decision_support_only: bool = True
