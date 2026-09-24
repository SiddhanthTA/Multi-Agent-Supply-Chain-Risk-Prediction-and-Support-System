from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: str
    location: Optional[str] = None
    source: Optional[str] = None
    source_type: Optional[str] = None
    category: Optional[str] = None
    published_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    severity: str = "Unknown"
    status: str = "Active"
    event_time: Optional[datetime] = None
    url: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None
    source_type: Optional[str] = None
    category: Optional[str] = None
    published_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    event_time: Optional[datetime] = None
    url: Optional[str] = None


class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    event_type: str
    location: Optional[str]
    source: Optional[str]
    source_type: Optional[str]
    category: Optional[str]
    published_at: Optional[datetime]
    received_at: Optional[datetime]
    latitude: Optional[float]
    longitude: Optional[float]
    severity: str
    status: str
    event_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    url: Optional[str]

    model_config = ConfigDict(from_attributes=True)