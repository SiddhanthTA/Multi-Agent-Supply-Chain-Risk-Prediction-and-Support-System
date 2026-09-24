from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from app.database.database import Base


class AILog(Base):
    __tablename__ = "ai_logs"

    id = Column(Integer, primary_key=True, index=True)

    model_name = Column(String(255))

    task = Column(String(255))

    input_summary = Column(Text)

    output_summary = Column(Text)

    execution_status = Column(String(50))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    prediction_id = Column(
    Integer,
    ForeignKey("predictions.id"),
    nullable=False
)
    prediction = relationship(
    "Prediction",
    back_populates="ai_logs"
)