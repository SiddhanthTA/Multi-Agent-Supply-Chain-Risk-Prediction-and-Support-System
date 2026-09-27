from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.risk_investigation import RiskInvestigationAgent
from app.agents.tools import (
    InvestigationAccessError,
    InvestigationNotFoundError,
    authorize_investigation,
    build_evidence_bundle,
)
from app.ai.llm_provider import (
    AgentBusyError,
    AgentOutputError,
    AgentTimeoutError,
    AgentUnavailableError,
)
from app.api.deps import get_current_user
from app.database.database import get_db
from app.crud.risk_report import get_report, report_status, save_report
from app.models.risk import Risk
from app.models.risk_report import KIND_INVESTIGATION, KIND_RESPONSE_PLAN
from app.models.user import User
from app.schemas.correlation import RiskCorrelationResponse
from app.schemas.impact_mapping import ImpactMapResponse
from app.services.impact_mapping import build_impact_map
from app.services.review_content import (
    build_review_correlations,
    build_review_impact,
    build_review_investigation,
    build_review_response_plan,
)
from app.services.risk_correlation import (
    DISCLAIMER,
    _dependencies_for_user,
    find_correlations,
)
from app.schemas.investigation import (
    InvestigationActor,
    InvestigationResponse,
    ResponsePlanResponse,
    RiskReportStatus,
)

router = APIRouter(prefix="/investigations", tags=["Risk Investigations"])


def _require_risk(db: Session, risk_id: int) -> None:
    if db.query(Risk).filter(Risk.id == risk_id).first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk not found.",
        )


@router.get("/risk/{risk_id}/status", response_model=RiskReportStatus)
def risk_report_status(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Report which AI outputs already exist for this risk.

    Read-only. Scoped to the authenticated user so one user can never learn
    about another user's company-specific investigation.
    """
    actor = InvestigationActor(user_id=current_user.id, role=current_user.role)
    try:
        authorize_investigation(actor)
    except InvestigationAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    _require_risk(db, risk_id)
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if risk and risk.event and build_review_investigation(risk, risk.event):
        return RiskReportStatus(risk_id=risk_id, investigation_exists=True, response_plan_exists=True)
    return report_status(db, risk_id, current_user.id)


@router.get("/risk/{risk_id}", response_model=InvestigationResponse)
def get_risk_investigation(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the stored investigation report, or 404 when none exists yet.

    This never runs the agent: viewing an existing report must not regenerate
    it.
    """
    actor = InvestigationActor(user_id=current_user.id, role=current_user.role)
    try:
        authorize_investigation(actor)
    except InvestigationAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    _require_risk(db, risk_id)
    review_risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if review_risk and review_risk.event:
        curated = build_review_investigation(review_risk, review_risk.event)
        if curated:
            return InvestigationResponse.model_validate(curated)
    stored = get_report(db, risk_id, current_user.id, KIND_INVESTIGATION)
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This risk has not been investigated yet.",
        )
    return InvestigationResponse.model_validate(stored.payload)


@router.post("/risk/{risk_id}", response_model=InvestigationResponse)
def investigate_risk(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and persist the investigation report for this risk.

    If a report already exists it is returned unchanged; the agent is never
    re-run for the same risk and user. Nothing is stored when generation
    fails, so a failed run can simply be retried.
    """
    actor = InvestigationActor(user_id=current_user.id, role=current_user.role)

    review_risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if review_risk and review_risk.event:
        curated = build_review_investigation(review_risk, review_risk.event)
        if curated:
            return InvestigationResponse.model_validate(curated)

    stored = get_report(db, risk_id, current_user.id, KIND_INVESTIGATION)
    if stored is not None:
        return InvestigationResponse.model_validate(stored.payload)

    try:
        response = RiskInvestigationAgent().investigate(db, risk_id, actor=actor)
    except InvestigationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvestigationAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except AgentBusyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AgentTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except AgentUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except AgentOutputError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    save_report(
        db,
        risk_id,
        current_user.id,
        KIND_INVESTIGATION,
        response.model_dump(mode="json"),
    )
    return response



@router.get("/risk/{risk_id}/response-plan", response_model=ResponsePlanResponse)
def get_risk_response_plan(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the stored response plan, or 404 when none exists yet.

    Read-only: this never rebuilds the plan.
    """
    actor = InvestigationActor(user_id=current_user.id, role=current_user.role)
    try:
        authorize_investigation(actor)
    except InvestigationAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    _require_risk(db, risk_id)
    review_risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if review_risk and review_risk.event:
        curated = build_review_response_plan(review_risk, review_risk.event)
        if curated:
            return ResponsePlanResponse.model_validate(curated)
    stored = get_report(db, risk_id, current_user.id, KIND_RESPONSE_PLAN)
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This risk does not have a response plan yet.",
        )
    return ResponsePlanResponse.model_validate(stored.payload)


@router.post("/risk/{risk_id}/response-plan", response_model=ResponsePlanResponse)
def build_risk_response_plan(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deterministic DEMO response-plan options for a previously investigated risk.

    Read-only with respect to intelligence data: reuses the Agent 1 read-only
    tools to load the risk, event, prediction, recommendation and company
    context, performs no model inference, and mutates no Risk/Event/Prediction/
    Recommendation record. The generated plan is persisted once per risk and
    user so later visits return immediately.
    """
    from app.services.response_plan import build_response_plan

    actor = InvestigationActor(user_id=current_user.id, role=current_user.role)

    review_risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if review_risk and review_risk.event:
        curated = build_review_response_plan(review_risk, review_risk.event)
        if curated:
            return ResponsePlanResponse.model_validate(curated)

    stored = get_report(db, risk_id, current_user.id, KIND_RESPONSE_PLAN)
    if stored is not None:
        return ResponsePlanResponse.model_validate(stored.payload)

    try:
        bundle, _ = build_evidence_bundle(db, risk_id, actor=actor)
    except InvestigationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvestigationAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    company_context = bundle.get("company_context")
    recommendation = bundle.get("recommendation")
    # The service returns a plain dict; validating here guarantees only
    # schema-conformant content is ever persisted or returned.
    plan = ResponsePlanResponse.model_validate(
        build_response_plan(
        risk=bundle["risk"],
        event=bundle["event"],
        company=(
            {
                "company_name": company_context["company_name"],
                "industry": company_context["industry"],
            }
            if company_context
            else None
        ),
        company_relevance=(company_context or {}).get("relevance"),
        platform_recommendation=(
            {
                "title": recommendation.get("recommendation_title") or "Platform recommendation",
                "text": recommendation.get("recommendation_text") or "",
                "priority": recommendation.get("priority"),
                "status": recommendation.get("status"),
            }
            if recommendation
            else None
        ),
        )
    )
    save_report(
        db,
        risk_id,
        current_user.id,
        KIND_RESPONSE_PLAN,
        plan.model_dump(mode="json"),
    )
    return plan


@router.get("/risk/{risk_id}/impact-map", response_model=ImpactMapResponse)
def risk_impact_map(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deterministic, read-only supply-chain impact mapping for one risk.

    Dependency matching reuses the existing company relevance engine. Areas and
    potential impacts come from the configured dependencies only; no actual
    company exposure is claimed or stored.
    """
    actor = InvestigationActor(user_id=current_user.id, role=current_user.role)
    try:
        authorize_investigation(actor)
    except InvestigationAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if risk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found.")
    if risk.event:
        curated = build_review_impact(risk, risk.event)
        if curated:
            return ImpactMapResponse.model_validate(curated)
    return build_impact_map(db, risk_id, user_id=current_user.id)


@router.get("/risk/{risk_id}/correlations", response_model=RiskCorrelationResponse)
def risk_correlations(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deterministic, read-only correlation of a risk with other stored risks.

    Uses the authenticated user's own company profile for the optional
    dependency signal. No user id is accepted from the client and nothing is
    written. Scores describe similarity, never a shared cause.
    """
    actor = InvestigationActor(user_id=current_user.id, role=current_user.role)
    try:
        authorize_investigation(actor)
    except InvestigationAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if risk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found.")
    curated = build_review_correlations(risk_id)
    if curated is not None:
        return RiskCorrelationResponse.model_validate(curated)

    result = find_correlations(db, risk_id, user_id=current_user.id)
    if not result["correlations"]:
        result["message"] = (
            "No strongly correlated risk signals identified in the current "
            "monitoring window."
        )
    result["disclaimer"] = DISCLAIMER
    result["company_context_available"] = _dependencies_for_user(db, current_user.id) is not None
    return result
