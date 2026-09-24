from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)

    predicted_risk = Column(String(255))
    confidence_score = Column(Float)
    predicted_severity = Column(String(50))
    prediction_model = Column(String(100))
    prediction_status = Column(String(50), default="Generated")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    risk_id = Column(Integer, ForeignKey("risks.id"), nullable=False)

    risk = relationship(
        "Risk",
        back_populates="predictions"
    )

    recommendations = relationship(
        "Recommendation",
        back_populates="prediction"
    )

    ai_logs = relationship(
        "AILog",
        back_populates="prediction"
    )