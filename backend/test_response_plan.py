"""Focused tests for runtime response-plan generation.

These assert plan construction only. They do not run Agent 1 inference.
"""
from datetime import datetime, timezone

import pytest

# Registered at module import time so the in-memory fixtures below, which call
# Base.metadata.create_all(), include the persisted-report table.
from app.models.risk_report import KIND_RESPONSE_PLAN, RiskReport  # noqa: F401
from app.services.response_plan import build_response_plan, select_scenario

RISK = {
    "id": 7,
    "risk_name": "Financial",
    "risk_type": "Financial",
    "severity": "High",
    "risk_score": 95.2,
    "status": "Active",
}
COMPANY = {"company_name": "Test Electronics", "industry": "Consumer Electronics"}
DIRECT_DIESEL = {
    "relevance": "direct",
    "matched_dependencies": [
        {"category": "fuel_energy", "value": "Diesel"},
        {"category": "geographic_exposure", "value": "India"},
    ],
}
PLATFORM_REC = {
    "title": "Shift Procurement Region",
    "text": "Move procurement activities to a more stable region.",
    "priority": "High",
    "status": "Pending",
}


def event(title, description="", category="Energy"):
    return {
        "id": 11,
        "title": title,
        "description": description,
        "location": "Unknown",
        "category": category,
    }


def plan(**overrides):
    kwargs = {
        "risk": RISK,
        "event": event("Russia extends diesel export ban", "Diesel fuel export ban extended."),
        "company": COMPANY,
        "company_relevance": DIRECT_DIESEL,
        "platform_recommendation": PLATFORM_REC,
    }
    kwargs.update(overrides)
    return build_response_plan(**kwargs)


def all_text(plan_obj):
    parts = [
        plan_obj["risk_summary"],
        plan_obj["response_objective"],
        *plan_obj["immediate_checks"],
        *plan_obj["information_required"],
        *plan_obj["escalation_conditions"],
        *plan_obj["notes"],
    ]
    for option in plan_obj["response_options"]:
        parts.extend([option["name"], option["why"]])
        parts.extend(option["what_to_check"])
        parts.extend(option["information_required"])
    if plan_obj["platform_recommendation"]:
        parts.extend([
            plan_obj["platform_recommendation"]["title"],
            plan_obj["platform_recommendation"]["text"],
        ])
    return " ".join(parts)


def test_diesel_company_relevant_scenario():
    result = plan()

    assert result["scenario"] == "fuel_and_energy"
    assert result["company_name"] == "Test Electronics"
    assert result["company_relevance"] == "direct"
    assert set(result["matched_dependencies"]) == {"Diesel", "India"}
    assert "Procurement" in result["responsible_areas"]
    assert "Logistics" in result["responsible_areas"]
    assert "Usage volumes" in " ".join(result["information_required"])


def test_semiconductor_company_relevant_scenario():
    result = plan(
        event=event("Semiconductor supply disruption in China", "Chip output falls.", "Logistics"),
        company_relevance={
            "relevance": "direct",
            "matched_dependencies": [
                {"category": "materials", "value": "Semiconductors"},
            ],
        },
    )

    assert result["scenario"] == "materials_and_supply"
    assert result["matched_dependencies"] == ["Semiconductors"]
    assert "supplier concentration" in " ".join(result["information_required"]).lower()


def test_logistics_scenario_is_supported():
    result = plan(event=event("Port closure delays vessels", "Ships delayed.", "Logistics"))
    assert result["scenario"] == "logistics_and_transport"


def test_financial_scenario_is_supported():
    result = plan(event=event("Tariff increase announced", "New duties on imports.", "Financial"))
    assert result["scenario"] == "financial_market"


def test_generic_fallback_for_unrelated_event():
    result = plan(
        event=event("City festival opens", "A festival began today.", "General"),
        company_relevance={"relevance": "no_identified_relevance", "matched_dependencies": []},
    )

    assert result["scenario"] in {"general", "financial_market"}
    assert result["response_objective"]
    assert len(result["response_options"]) == 3


def test_no_company_relevance_states_no_exposure_is_assumed():
    result = plan(
        event=event("City festival opens", "A festival began today.", "General"),
        company_relevance={"relevance": "no_identified_relevance", "matched_dependencies": []},
    )

    assert result["matched_dependencies"] == []
    text = " ".join(result["notes"])
    assert "no identified configured dependency match" in text
    assert "no company-specific exposure is assumed" in text


def test_missing_company_profile_still_produces_a_plan():
    result = plan(company=None, company_relevance=None)

    assert result["company_context_available"] is False
    assert result["company_name"] is None
    assert result["scenario"] == "fuel_and_energy"
    assert len(result["response_options"]) == 3
    assert "No company profile is configured" in " ".join(result["notes"])


def test_platform_recommendation_is_preserved_separately():
    result = plan()

    assert result["platform_recommendation"]["title"] == "Shift Procurement Region"
    assert result["platform_recommendation"]["priority"] == "High"
    assert result["platform_recommendation"]["status"] == "Pending"


def test_no_platform_recommendation_returns_none():
    result = plan(platform_recommendation=None)
    assert result["platform_recommendation"] is None


def test_options_are_not_ranked_as_best_or_recommended():
    names = " ".join(
        option["name"] for option in plan()["response_options"]
    ).casefold()

    for banned in ("best", "optimal", "recommended", "highest priority"):
        assert banned not in names


def test_plan_contains_no_invented_quantitative_exposure():
    text = all_text(plan()).casefold()

    for invented in (
        "spends", "crore", "per year", "annually", "70%", "supplier named",
        "contract value", "fleet of",
    ):
        assert invented not in text


def test_plan_is_flagged_as_demo_template():
    result = plan()
    assert result["is_demo_template"] is False
    assert result["generated_by"] == "runtime-context-response-planner"
    assert result["decision_support_only"] is True


def test_select_scenario_prefers_fuel_over_other_terms():
    assert select_scenario(
        event("Diesel prices rise", "Diesel costs climbed.", "Financial"), RISK
    ) == "fuel_and_energy"
    assert select_scenario(event("Nothing notable", "", "General"), RISK) in {
        "general",
        "financial_market",
    }


def test_duplicate_dependency_values_across_categories_are_listed_once():
    result = plan(
        event=event("Semiconductor supply disruption", "Chip output falls.", "Logistics"),
        company_relevance={
            "relevance": "direct",
            "matched_dependencies": [
                {"category": "materials", "value": "Semiconductors"},
                {"category": "technology", "value": "Semiconductors"},
                {"category": "geographic_exposure", "value": "China"},
            ],
        },
    )

    assert result["matched_dependencies"] == ["Semiconductors", "China"]


def test_response_plan_changes_with_event_context():
    first = plan(
        event=event(
            "Diesel export restriction raises fuel costs",
            "Diesel prices increase after an export restriction.",
            "Energy",
        )
    )
    second = plan(
        event=event(
            "Port closure delays semiconductor shipments",
            "A port closure is delaying chip shipments.",
            "Logistics",
        ),
        company_relevance={
            "relevance": "direct",
            "matched_dependencies": [
                {"category": "materials", "value": "Semiconductors"},
                {"category": "logistics", "value": "Ports"},
            ],
        },
    )
    assert first["scenario"] != second["scenario"]
    assert first["risk_summary"] != second["risk_summary"]
    assert first["response_options"][0]["name"] != second["response_options"][0]["name"]
    assert first["information_required"] != second["information_required"]


@pytest.fixture()
def plan_db():
    """Self-contained in-memory store for the read-only endpoint test."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.database.database import Base
    from app.models.event import Event
    from app.models.risk import Risk

    # StaticPool keeps a single connection so the table created here is also
    # visible to the TestClient worker thread that serves the request.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    event = Event(
        title="Russia extends diesel export ban",
        description="Diesel fuel export ban extended.",
        event_type="News",
        location="India",
        category="Energy",
        severity="High",
        status="Active",
        event_time=datetime.now(timezone.utc),
    )
    session.add(event)
    session.flush()
    risk = Risk(
        event_id=event.id,
        risk_name="Financial",
        risk_type="Financial",
        risk_score=95.2,
        severity="High",
        probability=0.95,
        status="Active",
    )
    session.add(risk)
    session.commit()
    try:
        yield session, risk.id
    finally:
        session.close()


def test_response_plan_endpoint_does_not_mutate_intelligence(plan_db):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api.deps import get_current_user
    from app.database.database import get_db
    from app.models.company_profile import CompanyDependency, CompanyProfile
    from app.models.event import Event
    from app.models.prediction import Prediction
    from app.models.recommendation import Recommendation
    from app.models.risk import Risk
    from app.models.risk_report import KIND_RESPONSE_PLAN, RiskReport
    from app.models.user import User
    from app.routers.investigation import router

    db, risk_id = plan_db
    user = User(
        id=1,
        username="analyst",
        email="analyst@example.com",
        password="hashed",
        role="analyst",
    )
    db.add(user)
    db.flush()
    profile = CompanyProfile(
        user_id=user.id,
        company_name="Test Electronics",
        industry="Consumer Electronics",
    )
    db.add(profile)
    db.flush()
    db.add(
        CompanyDependency(
            company_profile_id=profile.id,
            category="fuel_energy",
            value="Diesel",
        )
    )
    db.commit()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user

    before = (
        db.query(Event).count(),
        db.query(Risk).count(),
        db.query(Prediction).count(),
        db.query(Recommendation).count(),
        db.query(CompanyProfile).count(),
        db.query(CompanyDependency).count(),
    )

    with TestClient(app) as client:
        response = client.post(
            f"/investigations/risk/{risk_id}/response-plan"
        )

    after = (
        db.query(Event).count(),
        db.query(Risk).count(),
        db.query(Prediction).count(),
        db.query(Recommendation).count(),
        db.query(CompanyProfile).count(),
        db.query(CompanyDependency).count(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_demo_template"] is False
    assert body["company_name"] == "Test Electronics"
    assert body["generated_by"] == "runtime-context-response-planner"
    assert len(body["response_options"]) == 3

    # Intelligence and company data are untouched; only the generated plan is
    # stored, and only once.
    assert after == before
    stored = (
        db.query(RiskReport)
        .filter(
            RiskReport.risk_id == risk_id,
            RiskReport.user_id == user.id,
            RiskReport.kind == KIND_RESPONSE_PLAN,
        )
        .all()
    )
    assert len(stored) == 1

    # A repeat call returns the stored plan without creating a second row.
    with TestClient(app) as client:
        again = client.post(f"/investigations/risk/{risk_id}/response-plan")
    assert again.status_code == 200
    assert again.json()["response_objective"] == body["response_objective"]
    assert (
        db.query(RiskReport)
        .filter(
            RiskReport.risk_id == risk_id,
            RiskReport.user_id == user.id,
            RiskReport.kind == KIND_RESPONSE_PLAN,
        )
        .count()
        == 1
    )


def test_response_plan_endpoint_requires_authentication():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.routers.investigation import router

    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        assert client.post("/investigations/risk/1/response-plan").status_code == 401
