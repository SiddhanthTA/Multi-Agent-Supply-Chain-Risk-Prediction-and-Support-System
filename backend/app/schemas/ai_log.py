from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class AILogCreate(BaseModel):
    prediction_id: int
    model_name: Optional[str] = None
    task: Optional[str] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    execution_status: Optional[str] = None


class AILogUpdate(BaseModel):
    model_name: Optional[str] = None
    task: Optional[str] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    execution_status: Optional[str] = None


class AILogResponse(BaseModel):
    id: int
    prediction_id: int
    model_name: Optional[str]
    task: Optional[str]
    input_summary: Optional[str]
    output_summary: Optional[str]
    execution_status: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)