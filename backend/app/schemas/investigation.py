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
