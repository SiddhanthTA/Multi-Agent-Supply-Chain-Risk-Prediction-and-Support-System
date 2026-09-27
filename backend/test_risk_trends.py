"""Focused tests for deterministic Risk Trends."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.models.company_profile import CompanyDependency, CompanyProfile
from app.models.event import Event
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.risk import Risk
from app.models.user import User
from app.services.risk_trends import (
    ALLOWED_RANGES,
    InvalidTrendRangeError,
    build_risk_trends,
    normalize_severity,
)

NOW = datetime.now(timezone.utc)


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        # One shared connection so the TestClient thread sees the same rows.
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def days_ago(count: int) -> datetime:
    return NOW - timedelta(days=count)


def add_risk(session, *, title, risk_type="Political", severity="High", status="Active",
             category="Energy", location="India", days=1):
    event = Event(
        title=title,
        description=title,
        event_type="News",
        location=location,
        category=category,
        severity=severity,
        status=status,
        event_time=days_ago(days),
    )
    session.add(event)
    session.flush()
    risk = Risk(
        event_id=event.id,
        risk_name=risk_type,
        risk_type=risk_type,
        risk_score=70,
        severity=severity,
        status=status,
    )
    session.add(risk)
    session.flush()
    # created_at is a server_default, so set it explicitly for deterministic
    # trends and expire the identity map so later reads see the new value.
    session.query(Risk).filter(Risk.id == risk.id).update(
        {"created_at": days_ago(days)}, synchronize_session=False
    )
    session.commit()
    session.expire_all()
    return event, risk


def test_supported_ranges_work(db):
    for value in ALLOWED_RANGES:
        result = build_risk_trends(db, days=value)
        assert result["days"] == value
        assert len(result["daily"]) == value


def test_invalid_range_is_rejected(db):
    with pytest.raises(InvalidTrendRangeError):
        build_risk_trends(db, days=45)


def test_daily_counts_are_correct(db):
    add_risk(db, title="One", days=1)
    add_risk(db, title="Two", days=1)
    add_risk(db, title="Three", days=2)

    daily = {row["date"]: row["total"] for row in build_risk_trends(db, days=7)["daily"]}
    today = NOW.date().isoformat()
    yesterday = (NOW - timedelta(days=1)).date().isoformat()
    two_days = (NOW - timedelta(days=2)).date().isoformat()
    assert daily[yesterday] == 2
    assert daily[two_days] == 1
    assert daily[today] == 0


def test_zero_risk_days_are_included(db):
    add_risk(db, title="Only one", days=1)
    series = build_risk_trends(db, days=7)["daily"]
    assert len(series) == 7
    assert sum(row["total"] for row in series) == 1
    assert any(row["total"] == 0 for row in series)


def test_severity_counts_are_correct(db):
    add_risk(db, title="Crit", severity="Critical", days=1)
    add_risk(db, title="High", severity="High", days=1)
    add_risk(db, title="Med", severity="Medium", days=1)
    add_risk(db, title="Low", severity="Low", days=1)

    yesterday = (NOW - timedelta(days=1)).date().isoformat()
    row = next(r for r in build_risk_trends(db, days=7)["daily"] if r["date"] == yesterday)
    assert (row["critical"], row["high"], row["medium"], row["low"]) == (1, 1, 1, 1)


def test_severity_normalization_handles_inconsistent_casing(db):
    assert normalize_severity("HIGH") == "high"
    assert normalize_severity(" Critical ") == "critical"
    assert normalize_severity("Moderate") == "medium"
    add_risk(db, title="Weird", severity="HIGH", days=1)
    yesterday = (NOW - timedelta(days=1)).date().isoformat()
    row = next(r for r in build_risk_trends(db, days=7)["daily"] if r["date"] == yesterday)
    assert row["high"] == 1


def test_high_critical_and_active_summaries(db):
    add_risk(db, title="A", severity="High", status="Active", days=1)
    add_risk(db, title="B", severity="Critical", status="Pending", days=1)
    add_risk(db, title="C", severity="Low", status="Active", days=1)



def test_previous_period_comparison_and_change_percent(db):
    # Current window (inside 7 days).
    add_risk(db, title="Cur1", days=1)
    add_risk(db, title="Cur2", days=2)
    # Previous window (8-14 days ago).
    add_risk(db, title="Prev1", days=10)

    summary = build_risk_trends(db, days=7)["summary"]
    assert summary["total_risks"] == 2
    assert summary["previous_total_risks"] == 1
    assert summary["change_percent"] == 100.0


def test_zero_previous_period_returns_no_baseline(db):
    add_risk(db, title="Only", days=1)
    summary = build_risk_trends(db, days=7)["summary"]
    assert summary["previous_total_risks"] == 0
    assert summary["change_percent"] is None


def test_company_relevance_counts_use_existing_engine(db):
    user = add_user(db)
    add_profile(db, user, {"fuel_energy": ["Diesel"]})
    add_risk(db, title="Diesel export ban widens", category="Energy", days=1)
    add_risk(db, title="Local festival opens", category="General", location="France", days=1)

    company = build_risk_trends(db, days=7, user_id=user.id)["company"]
    assert company["available"] is True
    assert company["total_relevant"] >= 1
    assert company["direct"] >= 1
    assert any(item["dependency"] == "Diesel" for item in company["dependencies"])


def test_trends_work_without_company_profile(db):
    add_risk(db, title="Diesel export ban widens", days=1)
    result = build_risk_trends(db, days=7)
    assert result["company"]["available"] is False
    assert result["summary"]["total_risks"] == 1


def test_risks_are_not_double_counted_by_joins(db):
    _, risk = add_risk(db, title="Join risk", days=1)
    prediction = Prediction(risk_id=risk.id, predicted_risk="X", confidence_score=0.5, predicted_severity="High")
    db.add(prediction)
    db.flush()
    db.add(Recommendation(prediction_id=prediction.id, recommendation_title="T", recommendation_text="x"))
    db.commit()

    summary = build_risk_trends(db, days=7)["summary"]
    assert summary["total_risks"] == 1
    yesterday = (NOW - timedelta(days=1)).date().isoformat()
    row = next(r for r in build_risk_trends(db, days=7)["daily"] if r["date"] == yesterday)
    assert row["total"] == 1


def client_for(session, user):
    from app.api.deps import get_current_user
    from app.database.database import get_db
    from app.routers.risk import router

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def test_endpoint_requires_authentication(db):
    from app.routers.risk import router

    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        assert client.get("/risks/trends").status_code == 401


def test_endpoint_rejects_invalid_range(db):
    user = add_user(db)
    with client_for(db, user) as client:
        response = client.get("/risks/trends?days=45")
    assert response.status_code == 400
    assert "Allowed values" in response.json()["detail"]


def test_endpoint_forbidden_for_unsupported_role(db):
    user = add_user(db, "viewer@example.com", role="viewer")
    with client_for(db, user) as client:
        assert client.get("/risks/trends").status_code == 403


def test_endpoint_returns_trends_and_writes_nothing(db):
    user = add_user(db)
    add_profile(db, user, {"fuel_energy": ["Diesel"]})
    add_risk(db, title="Diesel export ban widens", days=1)
    add_risk(db, title="Another diesel signal", days=2)

    before = (
        db.query(Event).count(), db.query(Risk).count(), db.query(Prediction).count(),
        db.query(Recommendation).count(), db.query(CompanyProfile).count(), db.query(CompanyDependency).count(),
    )
    with client_for(db, user) as client:
        response = client.get("/risks/trends?days=7")
    after = (
        db.query(Event).count(), db.query(Risk).count(), db.query(Prediction).count(),
        db.query(Recommendation).count(), db.query(CompanyProfile).count(), db.query(CompanyDependency).count(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["days"] == 7
    assert len(body["daily"]) == 7
    assert body["summary"]["total_risks"] == 2
    assert after == before


def test_risk_type_and_category_breakdowns(db):
    add_risk(db, title="A", risk_type="Political", category="Energy", days=1)
    add_risk(db, title="B", risk_type="Political", category="Energy", days=1)
    add_risk(db, title="C", risk_type="Supplier", category="Logistics", days=1)
    # The model defaults category to "General", so clear it explicitly to cover
    # the uncategorized grouping path.
    blank, _ = add_risk(db, title="D", risk_type="Financial", category="General", days=1)
    db.query(Event).filter(Event.id == blank.id).update({"category": None}, synchronize_session=False)
    db.commit()

    result = build_risk_trends(db, days=7)
    types = {item["name"]: item["count"] for item in result["risk_type_breakdown"]}
    assert types["Political"] == 2
    assert types["Supplier"] == 1
    assert types["Financial"] == 1
    categories = {item["name"]: item["count"] for item in result["category_breakdown"]}
    assert categories["Energy"] == 2
    assert categories["Logistics"] == 1
    assert categories["Uncategorized"] == 1



def add_user(session, email="a@example.com", role="analyst"):
    user = User(username="u", email=email, password="x", role=role)
    session.add(user)
    session.commit()
    return user


def add_profile(session, user, dependencies):
    profile = CompanyProfile(user_id=user.id, company_name="Test Electronics", industry="Consumer Electronics")
    session.add(profile)
    session.flush()
    for category, values in dependencies.items():
        for value in values:
            session.add(CompanyDependency(company_profile_id=profile.id, category=category, value=value))
    session.commit()
    return profile
