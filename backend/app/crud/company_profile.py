from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.company_profile import CompanyDependency, CompanyProfile
from app.models.event import Event
from app.models.risk import Risk
from app.schemas.company_profile import CompanyProfileRequest, DEPENDENCY_CATEGORIES
from app.services.company_relevance import (
    DIRECT,
    INDIRECT,
    NONE,
    evaluate_event_relevance,
)

SUMMARY_EVENT_LIMIT = 300
TOP_RELEVANT_LIMIT = 8


class CompanyProfileSaveError(RuntimeError):
    """Raised when a company profile write fails; the transaction is rolled back."""


def get_company_profile(db: Session, user_id: int) -> CompanyProfile | None:
    return (
        db.query(CompanyProfile)
        .filter(CompanyProfile.user_id == user_id)
        .first()
    )


def _dependency_values(profile: CompanyProfile) -> dict[str, list[str]]:
    dependencies = {category: [] for category in DEPENDENCY_CATEGORIES}
    for dependency in profile.dependencies:
        if dependency.category in dependencies:
            dependencies[dependency.category].append(dependency.value)
    return {
        category: (
            [value for value in DEPENDENCY_CATEGORIES[category] if value in values]
            or ["None"]
        )
        for category, values in dependencies.items()
    }


def _normalized_dependencies(payload: CompanyProfileRequest) -> list[tuple[str, str]]:
    """Build a deduplicated, constraint-safe set of (category, value) rows."""
    rows: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for category, values in payload.dependencies.items():
        for value in values:
            key = (category, value)
            if key in seen:
                continue
            seen.add(key)
            rows.append(key)
    return rows


def save_company_profile(
    db: Session,
    user_id: int,
    payload: CompanyProfileRequest,
) -> CompanyProfile:
    """Create or replace a company profile and its dependency rows.

    Existing rows are deleted and flushed before the new rows are inserted so
    the (company_profile_id, category, value) unique constraint can never be
    violated by re-selecting a dependency that is already stored.
    """
    rows = _normalized_dependencies(payload)

    try:
        profile = get_company_profile(db, user_id)
        if profile is None:
            profile = CompanyProfile(user_id=user_id)
            db.add(profile)

        profile.company_name = payload.company_name
        profile.industry = payload.industry
        db.flush()

        # Remove the current dependency rows directly, then flush so the
        # pending DELETEs are emitted before any INSERT.
        db.query(CompanyDependency).filter(
            CompanyDependency.company_profile_id == profile.id
        ).delete(synchronize_session=False)
        db.flush()

        db.add_all(
            [
                CompanyDependency(company_profile_id=profile.id, category=category, value=value)
                for category, value in rows
            ]
        )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise CompanyProfileSaveError(
            "The company profile could not be saved. No changes were applied."
        ) from exc

    db.refresh(profile)
    return profile


def company_profile_response(profile: CompanyProfile) -> dict:
    return {
        "company_name": profile.company_name,
        "industry": profile.industry,
        "dependencies": _dependency_values(profile),
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }


def _primary_risks_by_event(db: Session) -> dict[int, Risk]:
    risks: dict[int, Risk] = {}
    for risk in db.query(Risk).order_by(Risk.risk_score.desc().nullslast()).all():
        risks.setdefault(risk.event_id, risk)
    return risks


def _relevance_rows(
    db: Session,
    profile: CompanyProfile,
    *,
    limit: int | None = None,
) -> list[dict]:
    """Compute company relevance for current events without storing derived data."""
    dependencies = _dependency_values(profile)
    query = db.query(Event).order_by(Event.created_at.desc().nullslast())
    if limit is not None:
        query = query.limit(limit)
    events = query.all()
    risks = _primary_risks_by_event(db)

    rows: list[dict] = []
    for event in events:
        risk = risks.get(event.id)
        result = evaluate_event_relevance(
            {
                "title": event.title,
                "description": event.description,
                "category": event.category,
                "event_type": event.event_type,
                "location": event.location,
                "source": event.source,
            },
            dependencies,
            {
                "risk_type": risk.risk_type if risk else None,
                "risk_name": risk.risk_name if risk else None,
            } if risk else None,
        )
        rows.append({
            "event_id": event.id,
            "title": event.title,
            "location": event.location,
            "category": event.category,
            "severity": risk.severity if risk else None,
            "event_time": event.event_time,
            "relevance": {**result, "event_id": event.id},
        })

    order = {DIRECT: 0, INDIRECT: 1, NONE: 2}
    rows.sort(
        key=lambda row: (
            order.get(row["relevance"]["relevance"], 3),
            -len(row["relevance"]["matched_dependencies"]),
        )
    )
    return rows


def company_relevance_for_event(
    db: Session,
    user_id: int,
    event_id: int,
) -> dict | None:
    profile = get_company_profile(db, user_id)
    if profile is None:
        return None
    event = db.query(Event).filter(Event.id == event_id).first()
    if event is None:
        return None
    risk = (
        db.query(Risk)
        .filter(Risk.event_id == event_id)
        .order_by(Risk.risk_score.desc().nullslast())
        .first()
    )
    result = evaluate_event_relevance(
        {
            "title": event.title,
            "description": event.description,
            "category": event.category,
            "event_type": event.event_type,
            "location": event.location,
            "source": event.source,
        },
        _dependency_values(profile),
        {
            "risk_type": risk.risk_type,
            "risk_name": risk.risk_name,
        } if risk else None,
    )
    return {
        "event_id": event.id,
        "title": event.title,
        "location": event.location,
        "category": event.category,
        "severity": risk.severity if risk else None,
        "event_time": event.event_time,
        "relevance": {**result, "event_id": event.id},
    }


def company_relevance_summary(
    db: Session,
    user_id: int,
    *,
    include_events: bool = True,
) -> dict:
    profile = get_company_profile(db, user_id)
    if profile is None:
        return {
            "company_name": None,
            "industry": None,
            "total_events": 0,
            "direct_count": 0,
            "indirect_count": 0,
            "no_identified_count": 0,
            "top_relevant_events": [],
            "events": [],
        }

    rows = _relevance_rows(db, profile, limit=SUMMARY_EVENT_LIMIT)
    relevant = [row for row in rows if row["relevance"]["relevance"] in {DIRECT, INDIRECT}]
    return {
        "company_name": profile.company_name,
        "industry": profile.industry,
        "total_events": len(rows),
        "direct_count": sum(1 for row in rows if row["relevance"]["relevance"] == DIRECT),
        "indirect_count": sum(1 for row in rows if row["relevance"]["relevance"] == INDIRECT),
        "no_identified_count": sum(1 for row in rows if row["relevance"]["relevance"] == NONE),
        "top_relevant_events": relevant[:TOP_RELEVANT_LIMIT],
        "events": rows if include_events else [],
    }

