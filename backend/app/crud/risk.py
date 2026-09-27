from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.risk import Risk
from app.models.review_risk import ReviewRisk
from app.crud.risk_report import get_report_kinds
from app.models.risk_report import KIND_INVESTIGATION, KIND_RESPONSE_PLAN
from app.services.review_content import is_review_risk
from app.schemas.risk import RiskCreate, RiskUpdate

# Resolution is a lifecycle state stored on the existing Risk.status field.
# The existing data already uses Active/Inactive, so no schema change is
# needed and no risk row is ever duplicated or deleted.
STATUS_ACTIVE = "Active"
STATUS_RESOLVED = "Resolved"

ACTIVE_STATUSES = (STATUS_ACTIVE, "Pending")


def is_resolved(risk: Risk | None) -> bool:
    return str(getattr(risk, "status", "") or "").strip().lower() == STATUS_RESOLVED.lower()


def is_risk_resolvable(db: Session, risk: Risk | None, user_id: int) -> bool:
    """A risk may only be resolved once both reports exist.

    The reports are scoped to the requesting user, exactly like the read
    endpoints, so a user cannot resolve a risk whose investigation or response
    plan they have not actually produced.
    """
    if risk is None or is_resolved(risk):
        return False
    if is_review_risk(risk.id):
        return True
    kinds = get_report_kinds(db, risk.id, user_id)
    return KIND_INVESTIGATION in kinds and KIND_RESPONSE_PLAN in kinds


def resolve_risk(db: Session, risk: Risk, user_id: int) -> Risk:
    """Move a risk to Resolved. Nothing is deleted.

    The event, risk, predictions, investigation, response plan and all
    correlation/impact history remain exactly as they were; only the lifecycle
    status changes. Severity and score are never modified.
    """
    if not is_risk_resolvable(db, risk, user_id):
        raise ValueError("This risk is not ready to be resolved.")
    risk.status = STATUS_RESOLVED
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk


def reopen_risk(db: Session, risk: Risk) -> Risk:
    """Return a resolved risk to the active list. Used to undo a mistake."""
    risk.status = STATUS_ACTIVE
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk


# ---------------------------------------------------------------------------
# Curated review set
# ---------------------------------------------------------------------------

def set_review_risks(db: Session, entries: list[dict]) -> int:
    """Replace the review set with the given real risk ids.

    Only metadata rows are written. Existing Risk rows, their severities and
    their scores are never modified, and no risk is duplicated.
    """
    db.query(ReviewRisk).delete()
    for order, entry in enumerate(entries):
        risk_id = int(entry["risk_id"])
        risk = db.query(Risk).get(risk_id)
        if risk is None:
            continue
        db.add(
            ReviewRisk(
                risk_id=risk_id,
                selection_reason=(entry.get("reason") or "")[:255] or None,
                severity_bucket=(risk.severity or "").lower() or None,
                sort_order=order,
            )
        )
    db.commit()
    return db.query(ReviewRisk).count()


def get_review_risks(db: Session) -> list[ReviewRisk]:
    return (
        db.query(ReviewRisk)
        .order_by(ReviewRisk.sort_order, ReviewRisk.risk_id)
        .all()
    )


def create_risk(db: Session, risk: RiskCreate):
    db_risk = Risk(**risk.model_dump())
    db.add(db_risk)
    db.commit()
    db.refresh(db_risk)
    return db_risk


def get_risk(db: Session, risk_id: int):
    return db.query(Risk).filter(Risk.id == risk_id).first()


def get_risks(db: Session, days: int | None = None):
    """All risks, optionally limited to a recent rolling window.

    ``days`` is a presentation/query filter only: nothing is deleted and the
    full history remains browsable by omitting the parameter.
    """
    query = db.query(Risk)
    if days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.filter(Risk.created_at >= cutoff)
    return query.all()

def get_risk_by_event(db: Session, event_id: int):
    return (
        db.query(Risk)
        .filter(Risk.event_id == event_id)
        .first()
    )

def update_risk(db: Session, risk_id: int, risk: RiskUpdate):
    db_risk = get_risk(db, risk_id)

    if not db_risk:
        return None

    update_data = risk.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_risk, key, value)

    db.commit()
    db.refresh(db_risk)

    return db_risk


def delete_risk(db: Session, risk_id: int):
    db_risk = get_risk(db, risk_id)

    if not db_risk:
        return None

    db.delete(db_risk)
    db.commit()

    return db_risk