from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class PredictionCreate(BaseModel):
    risk_id: int
    predicted_risk: Optional[str] = None
    predicted_severity: Optional[str] = None
    confidence_score: Optional[float] = None
    prediction_model: Optional[str] = None
    prediction_status: str = "Generated"


class PredictionUpdate(BaseModel):
    predicted_risk: Optional[str] = None
    predicted_severity: Optional[str] = None
    confidence_score: Optional[float] = None
    prediction_model: Optional[str] = None
    prediction_status: Optional[str] = None


class PredictionResponse(BaseModel):
    id: int
    risk_id: int
    predicted_risk: Optional[str]
    predicted_severity: Optional[str] = None
    confidence_score: Optional[float]
    prediction_model: Optional[str]
    prediction_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)