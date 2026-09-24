from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import Text
from app.database.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(Text, nullable=False)
    description = Column(Text)

    event_type = Column(String(100), nullable=False)

    location = Column(String(255))
    source = Column(String(500), nullable=True)
    source_type = Column(String(100), nullable=True, default="general")
    category = Column(String(100), nullable=True, default="General")
    published_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True, default=func.now())
    url = Column(String(500), unique=True, nullable=True)

    latitude = Column(Float)
    longitude = Column(Float)

    severity = Column(String(50), default="Unknown")
    status = Column(String(50), default="Active")

    event_time = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    risks = relationship(
    "Risk",
    back_populates="event"
)