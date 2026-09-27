"""Read/write helpers for persisted, per-user AI reports.

Reports are keyed by ``(risk_id, user_id, kind)``. Only completed, validated
service output is ever written: the caller is responsible for building the
payload first and passing it to :func:`save_report`.
"""

from sqlalchemy.orm import Session

from app.models.risk_report import (
    KIND_INVESTIGATION,
    KIND_RESPONSE_PLAN,
    RiskReport,
)


def get_report(db: Session, risk_id: int, user_id: int, kind: str) -> RiskReport | None:
    return (
        db.query(RiskReport)
        .filter(
            RiskReport.risk_id == risk_id,
            RiskReport.user_id == user_id,
            RiskReport.kind == kind,
        )
        .first()
    )


def save_report(db: Session, risk_id: int, user_id: int, kind: str, payload: dict) -> RiskReport:
    """Create or replace the stored report for this scope.

    A single row per scope is maintained, so repeated calls never accumulate
    duplicates for the same risk, user and report kind.
    """
    report = get_report(db, risk_id, user_id, kind)
    if report is None:
        report = RiskReport(
            risk_id=risk_id,
            user_id=user_id,
            kind=kind,
            payload=payload,
        )
        db.add(report)
    else:
        report.payload = payload
    db.commit()
    db.refresh(report)
    return report


def get_report_kinds(db: Session, risk_id: int, user_id: int) -> set:
    """Report kinds this user already has for a risk.

    Used by resolution so a risk can only be resolved once the requesting user
    actually has both reports.
    """
    rows = (
        db.query(RiskReport.kind)
        .filter(RiskReport.risk_id == risk_id, RiskReport.user_id == user_id)
        .all()
    )
    return {row[0] for row in rows}


def report_status(db: Session, risk_id: int, user_id: int) -> dict:
    """Which report kinds already exist for this risk and user."""
    rows = (
        db.query(RiskReport.kind)
        .filter(RiskReport.risk_id == risk_id, RiskReport.user_id == user_id)
        .all()
    )
    kinds = {row[0] for row in rows}
    return {
        "risk_id": risk_id,
        "investigation_exists": KIND_INVESTIGATION in kinds,
        "response_plan_exists": KIND_RESPONSE_PLAN in kinds,
    }
