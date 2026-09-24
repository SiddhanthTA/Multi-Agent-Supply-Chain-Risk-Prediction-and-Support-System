from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class RecommendationCreate(BaseModel):
    prediction_id: int
    recommendation_title: Optional[str] = None
    recommendation_text: Optional[str] = None
    priority: str = "Medium"
    status: str = "Pending"


class RecommendationUpdate(BaseModel):
    recommendation_title: Optional[str] = None
    recommendation_text: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class RecommendationResponse(BaseModel):
    id: int
    prediction_id: int
    recommendation_title: Optional[str]
    recommendation_text: Optional[str]
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)