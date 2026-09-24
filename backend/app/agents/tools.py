from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import re

from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.risk import Risk
from app.schemas.investigation import InvestigationActor, InvestigationEvidence


MAX_DESCRIPTION_LENGTH = 2000
RELATED_EVENT_LIMIT = 5
PREDICTION_LIMIT = 3
LOCATION_EVENT_LIMIT = 3


class InvestigationNotFoundError(LookupError):
    pass


class InvestigationAccessError(PermissionError):
    pass


def authorize_investigation(actor: InvestigationActor) -> None:
    from app.config.settings import settings

    allowed = {
        role.strip().lower()
        for role in settings.INVESTIGATION_ALLOWED_ROLES.split(",")
        if role.strip()
    }
    if actor.role.strip().lower() not in allowed:
        raise InvestigationAccessError("This role cannot run risk investigations.")


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _clip(value: str | None, limit: int = MAX_DESCRIPTION_LENGTH) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}… [truncated]"


def _event_record(event: Event, *, include_description: bool = True) -> dict:
    return {
        "id": event.id,
        "title": event.title,
        "description": _clip(event.description) if include_description else None,
        "event_type": event.event_type,
        "location": event.location,
        "source": event.source,
        "source_type": event.source_type,
        "category": event.category,
        "severity": event.severity,
        "status": event.status,
        "event_time": _iso(event.event_time),
        "published_at": _iso(event.published_at),
        "received_at": _iso(event.received_at),
        "latitude": event.latitude,
        "longitude": event.longitude,
        "url": event.url,
    }


def get_event(db: Session, event_id: int, *, actor: InvestigationActor) -> dict:
    authorize_investigation(actor)
    event = db.query(Event).filter(Event.id == event_id).first()
    if event is None:
        raise InvestigationNotFoundError("Event not found.")
    return _event_record(event)


def get_risk(db: Session, risk_id: int, *, actor: InvestigationActor) -> dict:
    authorize_investigation(actor)
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if risk is None:
        raise InvestigationNotFoundError("Risk not found.")
    return {
        "id": risk.id,
        "event_id": risk.event_id,
        "risk_name": risk.risk_name,
        "risk_type": risk.risk_type,
        "risk_score": risk.risk_score,
        "severity": risk.severity,
        "probability": risk.probability,
        "status": risk.status,
        "created_at": _iso(risk.created_at),
        "updated_at": _iso(risk.updated_at),
    }


def get_predictions(
    db: Session,
    risk_id: int,
    *,
    actor: InvestigationActor,
) -> list[dict]:
    authorize_investigation(actor)
    rows = (
        db.query(Prediction)
        .filter(Prediction.risk_id == risk_id)
        .order_by(Prediction.created_at.desc(), Prediction.id.desc())
        .limit(PREDICTION_LIMIT)
        .all()
    )
    return [
        {
            "id": row.id,
            "risk_id": row.risk_id,
            "predicted_risk": row.predicted_risk,
            "confidence_score": row.confidence_score,
            "predicted_severity": row.predicted_severity,
            "prediction_model": row.prediction_model,
            "prediction_status": row.prediction_status,
            "created_at": _iso(row.created_at),
            "updated_at": _iso(row.updated_at),
        }
        for row in rows
    ]



def _normalized(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _time_distance_days(left: datetime | None, right: datetime | None) -> float | None:
    if left is None or right is None:
        return None
    if left.tzinfo is None:
        left = left.replace(tzinfo=timezone.utc)
    if right.tzinfo is None:
        right = right.replace(tzinfo=timezone.utc)
    return abs((left - right).total_seconds()) / 86400


def get_related_events(
    db: Session,
    event_id: int,
    *,
    actor: InvestigationActor,
) -> list[dict]:
    authorize_investigation(actor)
    source = db.query(Event).filter(Event.id == event_id).first()
    if source is None:
        raise InvestigationNotFoundError("Event not found.")

    candidates = (
        db.query(Event)
        .filter(Event.id != event_id)
        .order_by(Event.event_time.desc().nullslast(), Event.id.desc())
        .limit(250)
        .all()
    )
    source_time = source.event_time or source.published_at or source.received_at
    source_risk_types = {
        _normalized(risk.risk_type or risk.risk_name)
        for risk in source.risks
        if risk.risk_type or risk.risk_name
    }
    ranked = []
    for event in candidates:
        reasons = []
        score = 0
        same_location = bool(
            source.location
            and event.location
            and _normalized(source.location) == _normalized(event.location)
        )
        same_category = bool(
            source.category
            and event.category
            and _normalized(source.category) == _normalized(event.category)
        )
        distance = _time_distance_days(source_time, event.event_time or event.published_at)
        nearby = distance is not None and distance <= 14
        risk_types = {
            _normalized(risk.risk_type or risk.risk_name)
            for risk in event.risks
            if risk.risk_type or risk.risk_name
        }
        same_risk_type = bool(source_risk_types & risk_types)

        if same_location:
            reasons.append("same location")
            score += 4
        if same_category:
            reasons.append("same category")
            score += 2
        if same_risk_type:
            reasons.append("similar risk type")
            score += 2
        if nearby:
            reasons.append(f"within {int(distance)} days")
            score += 1
        if not same_location and not same_category and not same_risk_type:
            continue
        if distance is not None:
            score += max(0, 2 - distance / 14)

        highest = max(
            (risk.risk_score or 0 for risk in event.risks),
            default=None,
        )
        ranked.append(
            (
                score,
                event.event_time or event.published_at or event.created_at,
                {
                    **_event_record(event, include_description=False),
                    "description": _clip(event.description, 500),
                    "highest_risk_score": highest,
                    "similarity_reasons": reasons,
                    "relationship_note": "Related platform signal; no causal link is established.",
                },
            )
        )

    ranked.sort(
        key=lambda item: (
            item[0],
            item[1] or datetime.min.replace(tzinfo=timezone.utc),
        ),
        reverse=True,
    )
    return [item[2] for item in ranked[:RELATED_EVENT_LIMIT]]


def get_location_context(
    db: Session,
    location: str | None,
    *,
    actor: InvestigationActor,
) -> dict:
    authorize_investigation(actor)
    normalized = _normalized(location)
    if not normalized or normalized == "unknown":
        return {
            "location": location,
            "event_count": 0,
            "risk_count": 0,
            "active_risk_count": 0,
            "high_or_critical_count": 0,
            "top_risk_categories": [],
            "latest_events": [],
        }

    events = (
        db.query(Event)
        .filter(Event.location == location)
        .order_by(Event.event_time.desc().nullslast(), Event.id.desc())
        .all()
    )
    risks = [risk for event in events for risk in event.risks]
    categories = Counter(
        (risk.risk_type or risk.risk_name or "Unknown")
        for risk in risks
    )
    return {
        "location": location,
        "event_count": len(events),
        "risk_count": len(risks),
        "active_risk_count": sum(
            1 for risk in risks if _normalized(risk.status) == "active"
        ),
        "high_or_critical_count": sum(
            1 for risk in risks if _normalized(risk.severity) in {"high", "critical"}
        ),
        "top_risk_categories": [
            {"name": name, "count": count}
            for name, count in categories.most_common(5)
        ],
        "latest_events": [
            {
                "id": event.id,
                "title": event.title,
                "category": event.category,
                "event_time": _iso(event.event_time or event.published_at),
            }
            for event in events[:LOCATION_EVENT_LIMIT]
        ],
    }


def get_correlations(
    db: Session,
    location: str | None,
    *,
    actor: InvestigationActor,
) -> dict:
    authorize_investigation(actor)
    get_location_context(db, location, actor=actor)
    risks = [
        risk
        for event in db.query(Event).filter(Event.location == location).all()
        for risk in event.risks
        if _normalized(risk.status) == "active"
    ]
    scores = [risk.risk_score for risk in risks if risk.risk_score is not None]
    average = sum(scores) / len(scores) if scores else 0
    if average >= 80:
        level = "Critical"
    elif average >= 60:
        level = "High"
    elif average >= 40:
        level = "Medium"
    else:
        level = "Low"
    return {
        "location": location,
        "active_risks": len(risks),
        "categories": sorted({risk.risk_name for risk in risks if risk.risk_name}),
        "overall_score": round(average, 2),
        "overall_risk": level,
        "interpretation": "Location-level aggregate, not proof of causation.",
    }


def get_recommendation(
    db: Session,
    prediction_id: int | None,
    *,
    actor: InvestigationActor,
) -> dict | None:
    authorize_investigation(actor)
    if prediction_id is None:
        return None
    row = (
        db.query(Recommendation)
        .filter(Recommendation.prediction_id == prediction_id)
        .order_by(Recommendation.updated_at.desc(), Recommendation.id.desc())
        .first()
    )
    if row is None:
        return None
    return {
        "id": row.id,
        "prediction_id": row.prediction_id,
        "recommendation_title": row.recommendation_title,
        "recommendation_text": _clip(row.recommendation_text, 1200),
        "priority": row.priority,
        "status": row.status,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }



def build_evidence_bundle(
    db: Session,
    risk_id: int,
    *,
    actor: InvestigationActor,
) -> tuple[dict, list[InvestigationEvidence]]:
    authorize_investigation(actor)
    risk = get_risk(db, risk_id, actor=actor)
    event = get_event(db, risk["event_id"], actor=actor)
    predictions = get_predictions(db, risk_id, actor=actor)
    recommendation = get_recommendation(
        db,
        predictions[0]["id"] if predictions else None,
        actor=actor,
    )
    related_events = get_related_events(db, event["id"], actor=actor)
    location_context = get_location_context(db, event["location"], actor=actor)
    correlation = get_correlations(db, event["location"], actor=actor)

    evidence = [
        InvestigationEvidence(
            ref="E1",
            evidence_type="event",
            label=f"Event {event['id']}: {event['title']}",
            data=event,
        ),
        InvestigationEvidence(
            ref="E2",
            evidence_type="risk",
            label=f"Risk {risk['id']}: {risk['risk_name']}",
            data=risk,
        ),
    ]
    for prediction in predictions:
        evidence.append(
            InvestigationEvidence(
                ref=f"E{len(evidence) + 1}",
                evidence_type="prediction",
                label=(
                    f"Prediction {prediction['id']}: "
                    f"{prediction['predicted_risk'] or 'Unspecified prediction'}"
                ),
                data=prediction,
            )
        )
    if recommendation:
        evidence.append(
            InvestigationEvidence(
                ref=f"E{len(evidence) + 1}",
                evidence_type="platform_recommendation",
                label=f"Platform recommendation {recommendation['id']}",
                data=recommendation,
            )
        )
    for item in related_events:
        evidence.append(
            InvestigationEvidence(
                ref=f"E{len(evidence) + 1}",
                evidence_type="related_event",
                label=f"Related Event {item['id']}: {item['title']}",
                data=item,
            )
        )
    evidence.append(
        InvestigationEvidence(
            ref=f"E{len(evidence) + 1}",
            evidence_type="location_context",
            label=f"Location context: {event['location'] or 'Unknown'}",
            data=location_context,
        )
    )
    evidence.append(
        InvestigationEvidence(
            ref=f"E{len(evidence) + 1}",
            evidence_type="correlation",
            label=f"Location correlation: {event['location'] or 'Unknown'}",
            data=correlation,
        )
    )

    return {
        "target": {"risk_id": risk_id, "event_id": event["id"]},
        "event": event,
        "risk": risk,
        "predictions": predictions,
        "recommendation": recommendation,
        "related_events": related_events,
        "location_context": location_context,
        "correlation": correlation,
    }, evidence

