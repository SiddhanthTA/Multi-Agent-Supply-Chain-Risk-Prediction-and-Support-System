"""Curated review set.

This is metadata *about* an existing Risk, not a copy of it. A risk is never
duplicated, and its severity, score and original assessment are never touched
here. A dedicated table is used rather than a new column on ``risks`` so the
existing schema needs no migration and the feature stays purely additive.
"""
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class ReviewRisk(Base):
    """Marks a real, existing Risk as part of the curated review set."""

    __tablename__ = "review_risks"
    __table_args__ = (
        # One row per risk, so the same risk cannot be selected twice.
        UniqueConstraint("risk_id", name="uq_review_risk"),
    )

    id = Column(Integer, primary_key=True, index=True)
    risk_id = Column(
        Integer,
        ForeignKey("risks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Why this risk was chosen, for the review inspection report.
    selection_reason = Column(String(255))
    # Copied from the risk only for grouping/ordering in the review view.
    # It is a presentation label and never drives any risk logic.
    severity_bucket = Column(String(20), index=True)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    risk = relationship("Risk", foreign_keys=[risk_id])
