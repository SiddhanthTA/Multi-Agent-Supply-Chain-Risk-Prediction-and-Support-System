"""Deterministic Risk Trends (read-only historical analytics).

Answers "how has risk activity changed over time?" by aggregating existing
Risk/Event records. Nothing is predicted, forecast, or persisted.

Date convention: all grouping is done on the calendar date of the risk's
``created_at`` value as stored by the database, converted to UTC before the
date is taken. Using a single UTC convention keeps naive and aware datetimes
from being mixed within one aggregation.

The primary metric counts RISK records (not Events). Counts use
``COUNT(Risk.id)`` grouped only by the risk's own columns, and the category
breakdown joins risks to exactly one event, so no join can multiply a risk.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.crud.company_profile import _dependency_values, get_company_profile
from app.models.event import Event
from app.models.risk import Risk
from app.services.company_relevance import evaluate_event_relevance

# Only these ranges are supported; anything else is rejected by the endpoint.
ALLOWED_RANGES = (7, 14, 30)
DEFAULT_RANGE = 30

SEVERITY_ALIASES = {
    "critical": "critical",
    "crit": "critical",
    "high": "high",
    "medium": "medium",
    "med": "medium",
    "moderate": "medium",
    "low": "low",
    "minor": "low",
}
UNCATEGORIZED = "Uncategorized"
UNCATEGORIZED_RISK_TYPE = "Unspecified"

# Bounded scan for the per-event company relevance pass, which cannot be done in
# SQL because the existing relevance engine is a Python function.
COMPANY_SCAN_LIMIT = 1000
BREAKDOWN_LIMIT = 10


class InvalidTrendRangeError(ValueError):
    """Raised when the requested range is not one of ALLOWED_RANGES."""


def normalize_severity(value: object) -> str:
    """Normalize stored severity for aggregation only; never written back."""
    if not isinstance(value, str):
        return ""
    key = value.strip().casefold()
    return SEVERITY_ALIASES.get(key, key)


def _date_range(end: date, days: int) -> tuple[datetime, datetime]:
    start = end - timedelta(days=days - 1)
    return (
        datetime(start.year, start.month, start.day, tzinfo=timezone.utc),
        datetime(end.year, end.month, end.day, 23, 59, 59, 999999, tzinfo=timezone.utc),
    )


def _daily_series(db: Session, start: datetime, end: datetime) -> list[dict]:
    """Per-day risk counts, including days with zero risks."""
    rows = db.execute(
        select(
            func.date(Risk.created_at).label("day"),
            func.count(Risk.id).label("total"),
        )
        .where(Risk.created_at >= start, Risk.created_at <= end)
        .group_by(func.date(Risk.created_at))
    ).all()
    by_day: dict[str, dict] = {str(day): {"total": int(total or 0)} for day, total in rows}

    severity_rows = db.execute(
        select(
            func.date(Risk.created_at).label("day"),
            Risk.severity,
            func.count(Risk.id).label("total"),
        )
        .where(Risk.created_at >= start, Risk.created_at <= end)
        .group_by(func.date(Risk.created_at), Risk.severity)
    ).all()
    for day, severity, total in severity_rows:
        key = normalize_severity(severity)
        if key in {"critical", "high", "medium", "low"}:
            bucket = by_day.setdefault(str(day), {"total": 0})
            bucket[key] = bucket.get(key, 0) + int(total or 0)

    series: list[dict] = []
    cursor = start.date()
    while cursor <= end.date():
        bucket = by_day.get(cursor.isoformat(), {})
        series.append(
            {
                "date": cursor.isoformat(),
                "total": int(bucket.get("total", 0)),
                "critical": int(bucket.get("critical", 0)),
                "high": int(bucket.get("high", 0)),
                "medium": int(bucket.get("medium", 0)),
                "low": int(bucket.get("low", 0)),
            }
        )
        cursor += timedelta(days=1)
    return series


def _totals(db: Session, start: datetime, end: datetime) -> dict:
    """Whole-window totals using the stored severity and status values."""
    rows = db.execute(
        select(Risk.severity, Risk.status, func.count(Risk.id))
        .where(Risk.created_at >= start, Risk.created_at <= end)
        .group_by(Risk.severity, Risk.status)
    ).all()

    total = high_critical = active = 0
    for severity, status, count in rows:
        count = int(count or 0)
        total += count
        if normalize_severity(severity) in {"high", "critical"}:
            high_critical += count
        if isinstance(status, str) and status.strip().casefold() == "active":
            active += count
    return {"total": total, "high_critical": high_critical, "active": active}


def _breakdown(db: Session, start: datetime, end: datetime) -> tuple[list[dict], list[dict]]:
    """Counts by stored risk type and by stored event category."""
    type_rows = db.execute(
        select(Risk.risk_type, func.count(Risk.id))
        .where(Risk.created_at >= start, Risk.created_at <= end)
        .group_by(Risk.risk_type)
    ).all()
    types = Counter()
    for name, count in type_rows:
        label = name.strip() if isinstance(name, str) and name.strip() else UNCATEGORIZED_RISK_TYPE
        types[label] += int(count or 0)

    # A risk joins exactly one event, so grouping by event category cannot
    # multiply risk rows.
    category_rows = db.execute(
        select(Event.category, func.count(Risk.id))
        .join(Event, Risk.event_id == Event.id)
        .where(Risk.created_at >= start, Risk.created_at <= end)
        .group_by(Event.category)
    ).all()
    categories = Counter()
    for name, count in category_rows:
        label = name.strip() if isinstance(name, str) and name.strip() else UNCATEGORIZED
        categories[label] += int(count or 0)

    def _top(counter: Counter) -> list[dict]:
        return [
            {"name": name, "count": count}
            for name, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:BREAKDOWN_LIMIT]
        ]

    return _top(types), _top(categories)


def _company_trend(db: Session, user_id: int | None, start: datetime, end: datetime) -> dict:
    """Company-relevant risk counts using the existing relevance engine only."""
    empty = {
        "available": False,
        "total_relevant": 0,
        "direct": 0,
        "indirect": 0,
        "dependencies": [],
    }
    if user_id is None:
        return empty
    profile = get_company_profile(db, user_id)
    if profile is None:
        return empty
    dependencies = _dependency_values(profile)

    rows = db.execute(
        select(Risk, Event)
        .join(Event, Risk.event_id == Event.id)
        .where(Risk.created_at >= start, Risk.created_at <= end)
        .limit(COMPANY_SCAN_LIMIT)
    ).all()

    direct = indirect = 0
    dependency_counts: Counter = Counter()
    for risk, event in rows:
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
            {"risk_type": risk.risk_type, "risk_name": risk.risk_name},
        )
        level = result.get("relevance")
        if level not in {"direct", "indirect"}:
            continue
        if level == "direct":
            direct += 1
        else:
            indirect += 1
        for match in result.get("matched_dependencies") or []:
            value = match.get("value")
            if value and value not in {"None", "Other"}:
                dependency_counts[value] += 1

    return {
        "available": True,
        "total_relevant": direct + indirect,
        "direct": direct,
        "indirect": indirect,
        "dependencies": [
            {"dependency": name, "count": count}
            for name, count in sorted(dependency_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
    }


def _change_percent(current: int, previous: int) -> float | None:
    """Descriptive change versus the previous period; None when no baseline."""
    if previous <= 0:
        return None
    return round((current - previous) / previous * 100, 1)


def build_risk_trends(db: Session, *, days: int = DEFAULT_RANGE, user_id: int | None = None) -> dict:
    """Aggregate historical risk activity. Read-only and deterministic."""
    if days not in ALLOWED_RANGES:
        raise InvalidTrendRangeError(
            f"Unsupported range '{days}'. Allowed values: {', '.join(str(v) for v in ALLOWED_RANGES)}."
        )

    today = datetime.now(timezone.utc).date()
    start, end = _date_range(today, days)
    previous_end = start - timedelta(seconds=1)
    previous_start, _ = _date_range(previous_end.date(), days)

    current = _totals(db, start, end)
    previous = _totals(db, previous_start, previous_end)
    risk_types, categories = _breakdown(db, start, end)

    return {
        "days": days,
        "start_date": start.date().isoformat(),
        "end_date": end.date().isoformat(),
        "comparison_start_date": previous_start.date().isoformat(),
        "comparison_end_date": previous_end.date().isoformat(),
        "summary": {
            "total_risks": current["total"],
            "high_critical_risks": current["high_critical"],
            "active_risks": current["active"],
            "previous_total_risks": previous["total"],
            "change_percent": _change_percent(current["total"], previous["total"]),
        },
        "daily": _daily_series(db, start, end),
        "risk_type_breakdown": risk_types,
        "category_breakdown": categories,
        "company": _company_trend(db, user_id, start, end),
    }

