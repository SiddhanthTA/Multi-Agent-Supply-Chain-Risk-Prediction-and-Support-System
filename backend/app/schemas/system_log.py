from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class SystemLogCreate(BaseModel):
    user_id: Optional[int] = None
    log_level: str
    module: str
    message: str


class SystemLogUpdate(BaseModel):
    log_level: Optional[str] = None
    module: Optional[str] = None
    message: Optional[str] = None


class SystemLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    log_level: str
    module: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)