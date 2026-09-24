from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)

    recommendation_title = Column(String(255))

    recommendation_text = Column(Text)

    priority = Column(String(50), default="Medium")

    status = Column(String(50), default="Pending")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    prediction_id = Column(
    Integer,
    ForeignKey("predictions.id"),
    nullable=False
)
    prediction = relationship(
    "Prediction",
    back_populates="recommendations"
)