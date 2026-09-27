from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.crud.risk import (
    create_risk,
    get_risk,
    get_risks,
    update_risk,
    delete_risk,
    is_resolved,
    is_risk_resolvable,
    resolve_risk,
    reopen_risk,
    STATUS_RESOLVED,
)
from app.crud.risk_report import get_report_kinds
from app.models.risk_report import KIND_INVESTIGATION, KIND_RESPONSE_PLAN
from app.schemas.risk import (
    RiskCreate,
    RiskUpdate,
    RiskResponse,
    ResolveRiskResponse,
    ReviewRiskItem,
    ReviewSetResponse,
)

from app.schemas.trends import RiskTrendResponse
from app.services.review_content import is_review_risk
from app.services.risk_trends import (
    ALLOWED_RANGES,
    DEFAULT_RANGE,
    InvalidTrendRangeError,
    build_risk_trends,
)

router = APIRouter(
    prefix="/risks",
    tags=["Risks"]
)


@router.get("/trends", response_model=RiskTrendResponse)
def read_risk_trends(
    days: int = DEFAULT_RANGE,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deterministic, read-only historical risk activity for the dashboard.

    Aggregates stored Risks only. No forecast is produced and nothing is
    written. Company context comes from the authenticated user's own profile.
    """
    from app.agents.tools import InvestigationAccessError, authorize_investigation
    from app.schemas.investigation import InvestigationActor

    actor = InvestigationActor(user_id=current_user.id, role=current_user.role)
    try:
        authorize_investigation(actor)
    except InvestigationAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    try:
        return build_risk_trends(db, days=days, user_id=current_user.id)
    except InvalidTrendRangeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/", response_model=RiskResponse)
def create_new_risk(risk: RiskCreate, db: Session = Depends(get_db)):
    return create_risk(db, risk)


@router.get("/", response_model=list[RiskResponse])
def read_risks(days: int | None = None, db: Session = Depends(get_db)):
    return get_risks(db, days=days)


@router.get("/resolved/list", response_model=list[ReviewRiskItem])
def read_resolved_risks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Risks that have completed the investigate/plan/resolve lifecycle."""
    rows = get_risks(db)
    return [_risk_item(risk) for risk in rows if is_resolved(risk)]


def _risk_item(risk, selection_reason: str | None = None) -> ReviewRiskItem:
    event = risk.event
    return ReviewRiskItem(
        risk_id=risk.id,
        risk_name=risk.risk_name,
        severity=risk.severity,
        risk_score=risk.risk_score,
        risk_type=risk.risk_type,
        status=risk.status,
        selection_reason=selection_reason,
        title=event.title if event else risk.risk_name,
        category=event.category if event else None,
        location=event.location if event else None,
        source=event.source if event else None,
        event_id=risk.event_id,
        created_at=event.created_at if event else risk.created_at,
    )


@router.get("/review-set", response_model=ReviewSetResponse)
def read_review_set(
    location: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Risks currently surfaced for the active workspace.

    This is the platform's own set of risks that have been classified and
    prioritised from the wider event stream. Resolved risks are excluded here
    and appear under /risks/resolved/list instead.
    """
    from app.crud.risk import get_review_risks

    entries = get_review_risks(db)
    selected = (location or "all").strip()

    def matches(item):
        value = str(item.location or "").strip()
        if selected in ("", "all", "All Locations"):
            return True
        if selected == "Global":
            return value == "" or value.lower() == "unknown" or value not in {"India", "United States"}
        if selected == "India":
            return value == "India" or value.endswith(", India") or value.endswith(",India")
        if selected == "United States":
            return value == "United States" or value.endswith(", United States") or value.endswith(",United States")
        return value == selected

    items = [
        _risk_item(e.risk, e.selection_reason)
        for e in entries
        if e.risk and not is_resolved(e.risk) and matches(_risk_item(e.risk, e.selection_reason))
    ]
    counts = {"High": 0, "Medium": 0, "Low": 0}
    for item in items:
        key = str(item.severity or "").lower().capitalize()
        if key in counts:
            counts[key] += 1
    return ReviewSetResponse(
        total=len(items),
        high=counts["High"],
        medium=counts["Medium"],
        low=counts["Low"],
        items=items,
    )
@router.get("/{risk_id}", response_model=RiskResponse)
def read_risk(risk_id: int, db: Session = Depends(get_db)):
    risk = get_risk(db, risk_id)

    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    return risk


@router.put("/{risk_id}", response_model=RiskResponse)
def update_existing_risk(
    risk_id: int,
    risk: RiskUpdate,
    db: Session = Depends(get_db),
):
    updated_risk = update_risk(db, risk_id, risk)

    if not updated_risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    return updated_risk


@router.delete("/{risk_id}")
def delete_existing_risk(
    risk_id: int,
    db: Session = Depends(get_db),
):
    deleted_risk = delete_risk(db, risk_id)

    if not deleted_risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    return {"message": "Risk deleted successfully"}


# ---------------------------------------------------------------------------
# Risk resolution
#
# Resolution is a lifecycle state on the existing Risk.status field. No row is
# ever duplicated or deleted, and severity/score are never modified: the
# original assessment is preserved so the historical intelligence stays intact.
# ---------------------------------------------------------------------------

def _resolution_state(db: Session, risk, user_id: int) -> dict:
    kinds = get_report_kinds(db, risk.id, user_id)
    curated = is_review_risk(risk.id)
    return {
        "risk_id": risk.id,
        "status": risk.status,
        "resolvable": is_risk_resolvable(db, risk, user_id),
        "investigation_exists": curated or KIND_INVESTIGATION in kinds,
        "response_plan_exists": curated or KIND_RESPONSE_PLAN in kinds,
        "resolved_at": risk.updated_at if is_resolved(risk) else None,
    }


@router.get("/{risk_id}/resolution", response_model=ResolveRiskResponse)
def read_risk_resolution(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Whether this risk can be resolved yet, for the authenticated user."""
    risk = get_risk(db, risk_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    return _resolution_state(db, risk, current_user.id)


@router.post("/{risk_id}/resolve", response_model=ResolveRiskResponse)
def resolve_existing_risk(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Move a risk to Resolved once its investigation and response plan exist.

    Ownership comes from the authenticated user only; no user id is accepted
    from the client. All historical data is preserved.
    """
    risk = get_risk(db, risk_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    if is_resolved(risk):
        return _resolution_state(db, risk, current_user.id)
    try:
        resolve_risk(db, risk, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _resolution_state(db, risk, current_user.id)


@router.post("/{risk_id}/reopen", response_model=ResolveRiskResponse)
def reopen_existing_risk(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a resolved risk to Active. Supports undoing a mistake."""
    risk = get_risk(db, risk_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    if not is_resolved(risk):
        raise HTTPException(status_code=409, detail="Risk is not resolved")
    reopen_risk(db, risk)
    return _resolution_state(db, risk, current_user.id)


