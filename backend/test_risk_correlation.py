"""Focused tests for deterministic Risk Correlation."""
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
from app.models.risk import Risk
from app.models.user import User
from app.services.risk_correlation import (
    MAX_CORRELATIONS,
    MIN_CORRELATION_SCORE,
    find_correlations,
)

NOW = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        # StaticPool keeps one connection for the whole in-memory database so the
        # TestClient worker thread sees the same rows as the test session.
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def add_signal(session, *, title, location, category, risk_type, days_ago=0, risk_score=70):
    event = Event(
        title=title,
        description=title,
        event_type="News",
        location=location,
        category=category,
        severity="High",
        status="Active",
        event_time=NOW - timedelta(days=days_ago),
    )
    session.add(event)
    session.flush()
    risk = Risk(
        event_id=event.id,
        risk_name=risk_type,
        risk_type=risk_type,
        risk_score=risk_score,
        severity="High",
        status="Active",
    )
    session.add(risk)
    session.commit()
    return event, risk


def add_user(session, email="a@example.com", role="analyst"):
    user = User(username="u", email=email, password="x", role=role)
    session.add(user)
    session.commit()
    return user


def add_profile(session, user, dependencies):
    profile = CompanyProfile(
        user_id=user.id,
        company_name="Test Electronics",
        industry="Consumer Electronics",
    )
    session.add(profile)
    session.flush()
    for category, values in dependencies.items():
        for value in values:
            session.add(
                CompanyDependency(
                    company_profile_id=profile.id,
                    category=category,
                    value=value,
                )
            )
    session.commit()
    return profile


def test_same_location_increases_correlation(db):
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    add_signal(db, title="Refinery output falls sharply", location="India", category="Energy", risk_type="Financial", days_ago=1)
    add_signal(db, title="Port congestion elsewhere", location="France", category="Logistics", risk_type="Operational", days_ago=1)

    result = find_correlations(db, target.id)
    same = [c for c in result["correlations"] if c["location"] == "India"]
    assert same and any("Same location: India" in r for r in same[0]["reasons"])
    assert all(c["location"] != "France" for c in result["correlations"])


def test_same_risk_type_and_category_add_reasons(db):
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    add_signal(db, title="Government weighs fuel curbs", location="Iran", category="Energy", risk_type="Political", days_ago=1)

    reasons = find_correlations(db, target.id)["correlations"][0]["reasons"]
    assert any("Same risk type" in r for r in reasons)
    assert any("Same event category" in r for r in reasons)


def test_close_timestamps_add_time_signal(db):
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    add_signal(db, title="Fuel curbs discussed", location="Iran", category="Energy", risk_type="Political", days_ago=0.5)

    result = find_correlations(db, target.id)
    assert any("Within 1 day" in r for c in result["correlations"] for r in c["reasons"])


def test_events_beyond_window_are_excluded(db):
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    add_signal(db, title="Very old identical signal", location="India", category="Energy", risk_type="Political", days_ago=30)

    result = find_correlations(db, target.id)
    assert result["correlations"] == []
    assert result["analysis_window_days"] == 7


def test_shared_company_dependency_adds_signal(db):
    user = add_user(db)
    add_profile(db, user, {"fuel_energy": ["Diesel"], "geographic_exposure": ["India"]})
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    add_signal(db, title="Another diesel supply signal", location="Iran", category="Energy", risk_type="Financial", days_ago=1)

    item = find_correlations(db, target.id, user_id=user.id)["correlations"][0]
    assert any("Shared company dependency: Diesel" in r for r in item["reasons"])
    assert any("Diesel" in dep for dep in item["shared_company_dependencies"])


def test_same_region_alone_gives_no_company_dependency_signal(db):
    user = add_user(db)
    add_profile(db, user, {"fuel_energy": ["Diesel"]})
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")


def test_generic_risk_type_alone_does_not_correlate(db):
    """A broad label plus recency must not relate unrelated nearby events."""
    _, target = add_signal(db, title="Harvest festival begins", location="Unknown", category="Energy", risk_type="Political")
    add_signal(db, title="Nuclear plant returns after hiatus", location="Unknown", category="Energy", risk_type="Political", days_ago=1)

    result = find_correlations(db, target.id)
    assert result["correlations"] == []


def test_unknown_location_does_not_award_the_location_signal(db):
    _, target = add_signal(db, title="Diesel export ban widens", location="Unknown", category="Energy", risk_type="Political")
    add_signal(db, title="Nuclear plant returns after hiatus", location="Unknown", category="Energy", risk_type="Political", days_ago=1)

    for item in find_correlations(db, target.id)["correlations"]:
        assert not any("Same location" in r for r in item["reasons"])


def test_distinct_stored_locations_are_not_merged(db):
    _, target = add_signal(db, title="Diesel export ban widens", location="United States", category="Energy", risk_type="Political")
    add_signal(db, title="Fuel curbs discussed", location="North America", category="Energy", risk_type="Political", days_ago=1)

    for item in find_correlations(db, target.id)["correlations"]:
        assert not any("Same location" in r for r in item["reasons"])


def test_maximum_five_correlations_returned(db):
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    for index in range(9):
        add_signal(db, title=f"Fuel signal variant number {index}", location="India", category="Energy", risk_type="Political", days_ago=1)

    assert len(find_correlations(db, target.id)["correlations"]) <= MAX_CORRELATIONS


def test_reasons_explain_each_correlation(db):
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    add_signal(db, title="Fuel curbs discussed", location="India", category="Energy", risk_type="Political", days_ago=1)

    for item in find_correlations(db, target.id)["correlations"]:
        assert item["reasons"]
        assert item["relationship_label"]
        assert 0 <= item["correlation_score"] <= 100


def test_scores_are_deterministic(db):
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    for index in range(4):
        add_signal(db, title=f"Fuel signal variant {index}", location="India", category="Energy", risk_type="Political", days_ago=1)

    first = find_correlations(db, target.id)["correlations"]
    second = find_correlations(db, target.id)["correlations"]
    assert [c["risk_id"] for c in first] == [c["risk_id"] for c in second]
    assert [c["correlation_score"] for c in first] == [c["correlation_score"] for c in second]


def test_ties_are_deterministic_by_recency(db):
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    add_signal(db, title="Fuel signal alpha", location="India", category="Energy", risk_type="Political", days_ago=1)
    add_signal(db, title="Fuel signal beta", location="India", category="Energy", risk_type="Political", days_ago=1)

    orders = {
        tuple(c["risk_id"] for c in find_correlations(db, target.id)["correlations"])
        for _ in range(3)
    }
    assert len(orders) == 1


def test_target_is_never_returned_as_itself(db):
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    add_signal(db, title="Fuel curbs discussed", location="India", category="Energy", risk_type="Political", days_ago=1)

    assert target.id not in [c["risk_id"] for c in find_correlations(db, target.id)["correlations"]]


def test_missing_metadata_does_not_crash(db):
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    blank = Event(title="Blank signal", description=None, event_type="News", location=None, category=None, severity=None, status="Active", event_time=NOW)
    db.add(blank)
    db.flush()
    db.add(Risk(event_id=blank.id, risk_name="Unspecified", risk_type=None, risk_score=None, severity=None, status="Active"))
    db.add(Event(title="No risk signal", description=None, event_type="News", location="India", category="Energy", event_time=NOW))
    db.commit()

    assert isinstance(find_correlations(db, target.id)["correlations"], list)


def test_missing_risk_returns_empty_result(db):
    result = find_correlations(db, 999999)
    assert result["correlations"] == []


def client_for(session, user):
    from app.api.deps import get_current_user
    from app.database.database import get_db
    from app.routers.investigation import router

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def client_with_user(session, user):
    """Client whose auth dependency is overridden before any request runs.

    get_current_user opens its own session, so the user must be supplied through
    the dependency override rather than created inside the test's session.
    """
    from app.api.deps import get_current_user
    from app.database.database import get_db
    from app.routers.investigation import router

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def detached_user(email="a@example.com", role="analyst"):
    """A user object usable without a database row (auth is overridden)."""
    return User(id=999, username="u", email=email, password="x", role=role)


def test_endpoint_requires_authentication(db):
    from app.routers.investigation import router

    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        assert client.get("/investigations/risk/1/correlations").status_code == 401


def test_endpoint_forbidden_for_unsupported_role(db):
    user = add_user(db, "guest@example.com", role="viewer")
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    with client_for(db, user) as client:
        assert client.get(f"/investigations/risk/{target.id}/correlations").status_code == 403


def test_endpoint_unknown_risk_returns_404(db):
    user = add_user(db)
    add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    with client_for(db, user) as client:
        assert client.get("/investigations/risk/999999/correlations").status_code == 404


def test_endpoint_performs_no_database_writes(db):
    user = add_user(db)
    add_profile(db, user, {"fuel_energy": ["Diesel"]})
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    add_signal(db, title="Another diesel supply signal", location="Iran", category="Energy", risk_type="Financial", days_ago=1)

    before = (
        db.query(Event).count(), db.query(Risk).count(),
        db.query(CompanyProfile).count(), db.query(CompanyDependency).count(),
    )
    with client_for(db, user) as client:
        response = client.get(f"/investigations/risk/{target.id}/correlations")
    after = (
        db.query(Event).count(), db.query(Risk).count(),
        db.query(CompanyProfile).count(), db.query(CompanyDependency).count(),
    )

    assert response.status_code == 200
    assert response.json()["correlations"]
    assert after == before


def test_endpoint_empty_message_when_nothing_qualifies(db):
    user = add_user(db)
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")

    with client_for(db, user) as client:
        body = client.get(f"/investigations/risk/{target.id}/correlations").json()

    assert body["correlations"] == []
    assert "No strongly correlated risk signals" in body["message"]
    assert "do not indicate a probability" in body["disclaimer"]


def test_cross_user_company_isolation(db):
    owner = add_user(db, "owner@example.com")
    other = add_user(db, "other@example.com")
    add_profile(db, owner, {"fuel_energy": ["Diesel"]})
    add_profile(db, other, {"fuel_energy": ["Coal"]})
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    add_signal(db, title="Another diesel supply signal", location="Iran", category="Energy", risk_type="Financial", days_ago=1)

    owner_result = find_correlations(db, target.id, user_id=owner.id)
    other_result = find_correlations(db, target.id, user_id=other.id)
    assert any("Diesel" in d for c in owner_result["correlations"] for d in c["shared_company_dependencies"])
    assert all("Diesel" not in d for c in other_result["correlations"] for d in c["shared_company_dependencies"])


def test_correlation_works_without_company_profile(db):
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    add_signal(db, title="Fuel curbs discussed", location="Iran", category="Energy", risk_type="Political", days_ago=1)

    result = find_correlations(db, target.id)
    assert result["correlations"]
    assert all(not c["shared_company_dependencies"] for c in result["correlations"])


def test_unrelated_event_does_not_pass_threshold(db):
    _, target = add_signal(db, title="Diesel export ban widens", location="India", category="Energy", risk_type="Political")
    add_signal(db, title="Local festival opens", location="Brazil", category="General", risk_type="Other", days_ago=5)

    result = find_correlations(db, target.id)
    assert all(c["correlation_score"] >= MIN_CORRELATION_SCORE for c in result["correlations"])
