from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base

class Risk(Base):
    __tablename__ = "risks"

    id = Column(Integer, primary_key=True, index=True)

    risk_name = Column(String(255), nullable=False)
    risk_type = Column(String(100))
    risk_score = Column(Float)
    severity = Column(String(50))
    probability = Column(Float)
    status = Column(String(50), default="Pending")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    event = relationship(
        "Event",
        back_populates="risks"
    )

    predictions = relationship(
        "Prediction",
        back_populates="risk"
    )