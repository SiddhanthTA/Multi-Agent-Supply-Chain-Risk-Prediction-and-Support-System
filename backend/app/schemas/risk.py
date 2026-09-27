from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class RiskCreate(BaseModel):
    event_id: int
    risk_name: str
    risk_type: Optional[str] = None
    risk_score: Optional[float] = None
    severity: Optional[str] = None
    probability: Optional[float] = None
    status: str = "Pending"


class RiskUpdate(BaseModel):
    risk_name: Optional[str] = None
    risk_type: Optional[str] = None
    risk_score: Optional[float] = None
    severity: Optional[str] = None
    probability: Optional[float] = None
    status: Optional[str] = None


class RiskResponse(BaseModel):
    id: int
    event_id: int
    risk_name: str
    risk_type: Optional[str]
    risk_score: Optional[float]
    severity: Optional[str]
    probability: Optional[float]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResolveRiskResponse(BaseModel):
    """Result of moving a risk to the Resolved lifecycle state.

    ``resolvable`` is False until both the investigation and the response plan
    exist for the requesting user, which is what the UI keys the Resolve Risk
    action off.
    """

    risk_id: int
    status: str
    resolvable: bool
    investigation_exists: bool
    response_plan_exists: bool
    resolved_at: Optional[datetime] = None


class ReviewRiskItem(BaseModel):
    risk_id: int
    severity: Optional[str] = None
    risk_score: Optional[float] = None
    risk_type: Optional[str] = None
    status: str
    selection_reason: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None
    event_id: Optional[int] = None
    created_at: Optional[datetime] = None


class ReviewSetResponse(BaseModel):
    total: int
    high: int
    medium: int
    low: int
    items: list[ReviewRiskItem]