from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base

# Report kinds stored per (risk, user).
KIND_INVESTIGATION = "investigation"
KIND_RESPONSE_PLAN = "response_plan"


class RiskReport(Base):
    """Persisted, per-user AI output for a specific risk.

    Agent 1 investigations and deterministic response plans are both
    risk-scoped, user-scoped reports. Keeping them in one table with a
    ``kind`` discriminator avoids two near-identical tables, while the
    ``(risk_id, user_id, kind)`` unique constraint guarantees a report is
    generated once and then simply retrieved.

    ``payload`` holds the validated Pydantic response produced by the
    existing services, so stored reports cannot contain partial or
    unvalidated content.
    """

    __tablename__ = "risk_reports"
    __table_args__ = (
        UniqueConstraint(
            "risk_id",
            "user_id",
            "kind",
            name="uq_risk_report_scope",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    risk_id = Column(
        Integer,
        ForeignKey("risks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind = Column(String(40), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    risk = relationship("Risk", foreign_keys=[risk_id])
    user = relationship("User", foreign_keys=[user_id])
