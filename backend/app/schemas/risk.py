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