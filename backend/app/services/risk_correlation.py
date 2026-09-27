"""Deterministic Risk Correlation.

Answers "are there other existing SupplySentry risk signals meaningfully
related to this risk?" using only stored Events/Risks plus the authenticated
user's existing company relevance result.

This is similarity scoring, not causal inference. A correlation score never
means a probability that two risks share a cause. Everything is computed on
request and nothing is persisted.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.crud.company_profile import _dependency_values, get_company_profile
from app.models.event import Event
from app.models.risk import Risk
from app.services.company_relevance import evaluate_event_relevance

# --- Tunable constants -------------------------------------------------

# Signal weights. Kept small and explicit so a score is always explainable.
WEIGHT_SAME_LOCATION = 20
WEIGHT_SAME_RISK_TYPE = 20
WEIGHT_SAME_CATEGORY = 20
WEIGHT_TIME_PROXIMITY = 20
WEIGHT_SHARED_DEPENDENCY = 15
WEIGHT_TEXT_SIMILARITY = 15

MAX_RAW_SCORE = (
    WEIGHT_SAME_LOCATION
    + WEIGHT_SAME_RISK_TYPE
    + WEIGHT_SAME_CATEGORY
    + WEIGHT_TIME_PROXIMITY
    + WEIGHT_SHARED_DEPENDENCY
    + WEIGHT_TEXT_SIMILARITY
)

# Only compare recent signals; older events are not considered candidates.
ANALYSIS_WINDOW_DAYS = 7

# Normalized (0-100) score a candidate must reach to be returned.
MIN_CORRELATION_SCORE = 50

# Never return an unbounded list of related risks.
MAX_CORRELATIONS = 5

# Bounded candidate scan so a request cannot load the whole table.
CANDIDATE_SCAN_LIMIT = 400

# Deterministic Jaccard overlap over normalized title tokens.
TEXT_SIMILARITY_MIN = 0.30

# Words too common to describe a relationship.
_STOPWORDS = frozenset(
    """
    a an the and or but of to in on at for with by from as is are was were be been
    this that these those it its into over after before new says say said will would
    could may might can amid more most less least than then they their them we you
    """.split()
)

RELATIONSHIP_HIGH = "high_similarity"
RELATIONSHIP_MODERATE = "moderate_similarity"
RELATIONSHIP_LIMITED = "limited_similarity"

RELATIONSHIP_LABELS = {
    RELATIONSHIP_HIGH: "High similarity",
    RELATIONSHIP_MODERATE: "Moderate similarity",
    RELATIONSHIP_LIMITED: "Limited similarity",
}

DISCLAIMER = (
    "Correlation scores describe similarity within SupplySentry's monitored data. "
    "They do not indicate a probability that two risks share a cause, and no causal "
    "link is established."
)


def _normalize(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.casefold().split())


GENERIC_LOCATION_VALUES = frozenset({"", "unknown", "global", "none", "n/a", "not specified"})

# Broad risk types carry little information on their own. They may only earn the
# risk-type signal together with at least one substantive signal, so that a
# common label such as "Supplier" does not relate every nearby event.
GENERIC_RISK_TYPES = frozenset(
    {
        "supplier", "political", "financial", "general", "operational",
        "other", "unknown", "logistics", "geopolitical", "weather", "energy",
    }
)


def _normalized_location(value: object) -> str:
    """Stored location, or empty when it is a placeholder rather than a place.

    'Unknown' and similar placeholders are not geographic locations, so two
    events that both lack a location do not share a location relationship.
    """
    normalized = _normalize(value)
    return "" if normalized in GENERIC_LOCATION_VALUES else normalized


def _time_of(event: Event) -> datetime | None:
    value = event.event_time or event.published_at or event.received_at
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _day_distance(left: datetime | None, right: datetime | None) -> float | None:
    if left is None or right is None:
        return None
    return abs((left - right).total_seconds()) / 86400


def _tokens(text: str | None) -> set[str]:
    """Significant normalized words, ignoring very common stop words."""
    return {
        token
        for token in _normalize(text).split()
        if len(token) > 3 and token not in _STOPWORDS
    }


def _text_similarity(left: str | None, right: str | None) -> tuple[bool, float]:
    """Deterministic Jaccard overlap of the two titles' significant words."""
    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens or not right_tokens:
        return False, 0.0
    overlap = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
    return overlap >= TEXT_SIMILARITY_MIN, round(overlap, 3)


def _time_signal(distance_days: float | None) -> tuple[int, str | None]:
    """Points and an explanation for how close two events are in time."""
    if distance_days is None:
        return 0, None
    if distance_days <= 1:
        return WEIGHT_TIME_PROXIMITY, "Within 1 day"
    if distance_days <= 3:
        return int(round(WEIGHT_TIME_PROXIMITY * 0.7)), f"Within {int(round(distance_days))} days"
    if distance_days <= ANALYSIS_WINDOW_DAYS:
        return int(round(WEIGHT_TIME_PROXIMITY * 0.4)), f"Within {int(round(distance_days))} days"
    # Beyond the window the candidate is excluded entirely, so no points apply.
    return 0, None


def _risk_type(risk: Risk | None) -> str:
    if risk is None:
        return ""
    return _normalize(risk.risk_type or risk.risk_name)


def _highest_risk(event: Event) -> Risk | None:
    if not event.risks:
        return None
    return sorted(
        event.risks,
        key=lambda risk: (risk.risk_score is None, -(risk.risk_score or 0), risk.id),
    )[0]


def _matched_dependencies(event: Event, risk: Risk | None, dependencies: dict | None) -> set[tuple[str, str]]:
    if not dependencies:
        return set()
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
        }
        if risk
        else None,
    )
    return {(item["category"], item["value"]) for item in result.get("matched_dependencies") or []}


def _relationship_level(score: int) -> str:
    if score >= 75:
        return RELATIONSHIP_HIGH
    if score >= 60:
        return RELATIONSHIP_MODERATE
    return RELATIONSHIP_LIMITED


def _candidate_events(db: Session, target: Event, target_time: datetime | None) -> list[Event]:
    query = db.query(Event).filter(Event.id != target.id)
    if target_time is not None:
        cutoff = target_time - timedelta(days=ANALYSIS_WINDOW_DAYS)
        horizon = target_time + timedelta(days=ANALYSIS_WINDOW_DAYS)
        # An event with no usable timestamp cannot be placed in the window, so it
        # is not treated as a candidate rather than being silently included.
        query = query.filter(
            or_(
                Event.event_time.between(cutoff, horizon),
                (Event.event_time.is_(None)) & Event.published_at.between(cutoff, horizon),
            )
        )
    return query.order_by(Event.id.desc()).limit(CANDIDATE_SCAN_LIMIT).all()


def _dependencies_for_user(db: Session, user_id: int | None) -> dict | None:
    """Configured dependencies for the authenticated user, or None."""
    if user_id is None:
        return None
    profile = get_company_profile(db, user_id)
    if profile is None:
        return None
    return _dependency_values(profile)


def find_correlations(
    db: Session,
    risk_id: int,
    *,
    user_id: int | None = None,
) -> dict:
    """Score a target risk against other stored risks. Read-only and bounded."""
    target_risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if target_risk is None or target_risk.event is None:
        return {
            "risk_id": risk_id,
            "event_id": None,
            "correlations": [],
            "total_candidates_considered": 0,
            "analysis_window_days": ANALYSIS_WINDOW_DAYS,
        }

    target_event = target_risk.event
    target_time = _time_of(target_event)
    target_type = _risk_type(target_risk)
    target_location = _normalized_location(target_event.location)
    target_category = _normalize(target_event.category)

    dependencies = _dependencies_for_user(db, user_id)
    target_dependencies = _matched_dependencies(target_event, target_risk, dependencies)

    considered = 0
    scored: list[tuple[int, datetime, int, dict]] = []

    for event in _candidate_events(db, target_event, target_time):
        candidate_risk = _highest_risk(event)
        if candidate_risk is None:
            continue
        considered += 1

        distance = _day_distance(target_time, _time_of(event))
        if distance is None or distance > ANALYSIS_WINDOW_DAYS:
            continue

        raw = 0
        reasons: list[str] = []
        shared: list[str] = []

        if target_location and _normalized_location(event.location) == target_location:
            raw += WEIGHT_SAME_LOCATION
            reasons.append(f"Same location: {event.location}")

        candidate_type = _risk_type(candidate_risk)
        if target_type and candidate_type == target_type:
            raw += WEIGHT_SAME_RISK_TYPE
            reasons.append(f"Same risk type: {candidate_risk.risk_type or candidate_risk.risk_name}")

        if target_category and _normalize(event.category) == target_category:
            raw += WEIGHT_SAME_CATEGORY
            reasons.append(f"Same event category: {event.category}")

        time_points, time_reason = _time_signal(distance)
        if time_points:
            raw += time_points
            if time_reason:
                reasons.append(time_reason)

        if target_dependencies:
            candidate_dependencies = _matched_dependencies(event, candidate_risk, dependencies)
            overlap = sorted(target_dependencies & candidate_dependencies)
            if overlap:
                raw += WEIGHT_SHARED_DEPENDENCY
                shared = [f"{category.replace('_', ' ')}: {value}" for category, value in overlap]
                names = sorted({value for _, value in overlap})
                reasons.append("Shared company dependency: " + ", ".join(names))

        similar, overlap_score = _text_similarity(target_event.title, event.title)
        if similar:
            raw += WEIGHT_TEXT_SIMILARITY
            reasons.append(f"Similar event wording (overlap {overlap_score})")

        if not reasons:
            continue

        # A generic risk type or category on its own would relate everything that
        # happened nearby, so it must be supported by a substantive signal: a real
        # stored location, a shared company dependency, or similar wording.
        substantive = bool(
            target_location
            or shared
            or similar
        )
        if not substantive and target_type in GENERIC_RISK_TYPES:
            continue
        if not substantive and not shared and not similar and not target_location:
            continue

        score = round(raw / MAX_RAW_SCORE * 100)
        if score < MIN_CORRELATION_SCORE:
            continue

        level = _relationship_level(score)
        scored.append(
            (
                score,
                _time_of(event) or datetime.min.replace(tzinfo=timezone.utc),
                candidate_risk.id,
                {
                    "risk_id": candidate_risk.id,
                    "event_id": event.id,
                    "event_title": event.title,
                    "severity": candidate_risk.severity or event.severity,
                    "risk_type": candidate_risk.risk_type or candidate_risk.risk_name,
                    "location": event.location,
                    "event_category": event.category,
                    "correlation_score": score,
                    "relationship_level": level,
                    "relationship_label": RELATIONSHIP_LABELS[level],
                    "reasons": reasons,
                    "shared_company_dependencies": shared,
                    "days_apart": round(distance, 1),
                },
            )
        )

    # Highest score first; recency then risk id keep ties fully deterministic.
    scored.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)

    return {
        "risk_id": risk_id,
        "event_id": target_event.id,
        "correlations": [item[3] for item in scored[:MAX_CORRELATIONS]],
        "total_candidates_considered": considered,
        "analysis_window_days": ANALYSIS_WINDOW_DAYS,
    }
