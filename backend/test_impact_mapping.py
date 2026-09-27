"""Focused tests for deterministic Supply Chain Impact Mapping."""
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
from app.services.impact_mapping import (
    MAX_AREAS,
    MAX_CHECKS,
    MAX_IMPACTS,
    MAX_MAPPINGS,
    build_impact_map,
)


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def add_risk(session, *, title, description=None, category="Energy", location="India", risk_type="Political"):
    event = Event(
        title=title,
        description=description if description is not None else title,
        event_type="News",
        location=location,
        category=category,
        severity="High",
        status="Active",
    )
    session.add(event)
    session.flush()
    risk = Risk(
        event_id=event.id,
        risk_name=risk_type,
        risk_type=risk_type,
        risk_score=80,
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
    profile = CompanyProfile(user_id=user.id, company_name="Test Electronics", industry="Consumer Electronics")
    session.add(profile)
    session.flush()
    for category, values in dependencies.items():
        for value in values:
            session.add(CompanyDependency(company_profile_id=profile.id, category=category, value=value))
    session.commit()
    return profile


def mapping_for(db, title, dependencies, user=None, **kwargs):
    owner = user or add_user(db)
    add_profile(db, owner, dependencies)
    _, risk = add_risk(db, title=title, **kwargs)
    return build_impact_map(db, risk.id, user_id=owner.id)


def test_diesel_direct_match(db):
    result = mapping_for(db, "Record diesel prices raise fuel shortage fears", {"fuel_energy": ["Diesel"]})
    assert result["relevance"] == "direct"
    assert result["company_name"] == "Test Electronics"
    dep = result["mappings"][0]
    assert dep["dependency"] == "Diesel"
    assert "Transportation" in dep["supply_chain_areas"]
    assert "Logistics" in dep["supply_chain_areas"]
    assert "Fuel consumption" in dep["verification_checks"]


def test_semiconductors_direct_match(db):
    result = mapping_for(db, "Semiconductor supply disruption halts chip output", {"materials": ["Semiconductors"]})
    dep = result["mappings"][0]
    assert dep["dependency"] == "Semiconductors"
    assert "Manufacturing" in dep["supply_chain_areas"]
    assert "Semiconductor suppliers" in dep["verification_checks"]


def test_ports_direct_match(db):
    result = mapping_for(db, "Port congestion delays vessels at terminal", {"logistics": ["Ports"]})
    dep = result["mappings"][0]
    assert dep["dependency"] == "Ports"
    assert "Import/Export Operations" in dep["supply_chain_areas"]


def test_road_direct_match(db):
    result = mapping_for(db, "Road freight trucking route closure", {"logistics": ["Road"]})
    assert result["mappings"][0]["dependency"] == "Road"
    assert "Last-Mile Operations" in result["mappings"][0]["supply_chain_areas"]


def test_rail_direct_match(db):
    result = mapping_for(db, "Rail service disruption halts railway freight", {"logistics": ["Rail"]})
    assert result["mappings"][0]["dependency"] == "Rail"
    assert "Bulk Logistics" in result["mappings"][0]["supply_chain_areas"]


def test_sea_direct_match(db):
    result = mapping_for(db, "Sea shipping vessel freight disruption", {"logistics": ["Sea"]})
    assert result["mappings"][0]["dependency"] == "Sea"
    assert "Maritime Logistics" in result["mappings"][0]["supply_chain_areas"]


def test_air_direct_match(db):
    result = mapping_for(db, "Air cargo flight disruption delays shipments", {"logistics": ["Air"]})
    assert result["mappings"][0]["dependency"] == "Air"
    assert "Air Freight" in result["mappings"][0]["supply_chain_areas"]


def test_multiple_matched_dependencies(db):
    result = mapping_for(
        db,
        "Port congestion affects diesel imports and road trucking",
        {"fuel_energy": ["Diesel"], "logistics": ["Ports", "Road"]},
    )
    names = {item["dependency"] for item in result["mappings"]}
    assert {"Diesel", "Ports", "Road"} <= names


def test_no_company_profile_returns_no_mappings(db):
    _, risk = add_risk(db, title="Diesel prices surge")
    result = build_impact_map(db, risk.id, user_id=None)
    assert result["company_available"] is False
    assert result["mappings"] == []
    assert "not configured" in result["summary"]


def test_none_dependency_produces_no_mapping(db):
    result = mapping_for(db, "Diesel prices surge sharply", {"fuel_energy": ["None"]})
    assert result["mappings"] == []


def test_other_dependency_is_not_a_wildcard(db):
    result = mapping_for(db, "Diesel prices surge sharply", {"fuel_energy": ["Other"]})
    assert result["mappings"] == []


def test_no_identified_relevance(db):
    result = mapping_for(db, "Wheat harvest fails after poor rainfall", {"fuel_energy": ["Diesel"]})
    assert result["relevance"] == "no_identified_relevance"
    assert result["mappings"] == []
    assert "No company-specific impact mapping" in result["summary"]


def test_specialised_dependency_mapping_is_used(db):
    result = mapping_for(db, "Lithium supply from Chile is constrained", {"materials": ["Lithium"]})
    dep = result["mappings"][0]
    assert dep["dependency"] == "Lithium"
    assert "Manufacturing" in dep["supply_chain_areas"]
    assert "Lithium suppliers" in dep["verification_checks"]


def test_geographic_exposure_cannot_create_relevance_alone(db):
    # The existing relevance engine requires a non-geographic dependency, so
    # a location-only configuration must not produce a mapping.
    result = mapping_for(db, "India factory output disrupted by floods", {"geographic_exposure": ["India"]})
    assert result["mappings"] == []
    assert result["relevance"] == "no_identified_relevance"


def test_geographic_exposure_maps_to_regional_areas(db):
    # Alongside a real dependency, the matched region maps to region areas.
    user = add_user(db)
    add_profile(db, user, {"geographic_exposure": ["India"], "logistics": ["Sea"]})
    _, risk = add_risk(db, title="India shipping container vessel rerouted")
    result = build_impact_map(db, risk.id, user_id=user.id)
    by_name = {item["dependency"]: item for item in result["mappings"]}
    assert "India" in by_name
    assert by_name["India"]["supply_chain_areas"] == [
        "Regional Operations", "Distribution", "Market Coverage"
    ]
    assert by_name["India"]["verification_checks"][0] == "Activity in the configured region"
    assert "Sea" in by_name


def test_diesel_shortage_refinement(db):
    result = mapping_for(db, "Record diesel prices raise fears of fuel shortages", {"fuel_energy": ["Diesel"]})
    impacts = result["mappings"][0]["potential_impacts"]
    # The shortage-specific refinement leads, and the generic availability
    # impact is retained so the mapping still covers fuel availability.
    assert impacts[0] == "Fuel supply continuity pressure"
    assert "Fuel availability pressure" in impacts


def test_diesel_price_refinement(db):
    result = mapping_for(db, "Diesel prices climb across the region", {"fuel_energy": ["Diesel"]})
    impacts = result["mappings"][0]["potential_impacts"]
    assert "Fuel cost pressure" in impacts
    assert "Transportation budget pressure" in impacts


def test_semiconductor_shortage_refinement(db):
    result = mapping_for(db, "Semiconductor shortage delays chip production", {"materials": ["Semiconductors"]})
    impacts = result["mappings"][0]["potential_impacts"]
    assert "Production continuity pressure" in impacts


def test_port_congestion_refinement(db):
    result = mapping_for(db, "Port congestion strands vessels at the terminal", {"logistics": ["Ports"]})
    impacts = result["mappings"][0]["potential_impacts"]
    assert "Port congestion exposure" in impacts


def test_mapping_limits_are_respected(db):
    result = mapping_for(
        db,
        "Diesel supply cut affects ports, road, rail, sea and air freight",
        {"fuel_energy": ["Diesel"], "logistics": ["Ports", "Road", "Rail", "Sea", "Air"]},
    )
    assert len(result["mappings"]) <= MAX_MAPPINGS
    for item in result["mappings"]:
        assert len(item["supply_chain_areas"]) <= MAX_AREAS
        assert len(item["potential_impacts"]) <= MAX_IMPACTS
        assert len(item["verification_checks"]) <= MAX_CHECKS


def test_no_fabricated_quantitative_exposure(db):
    result = mapping_for(db, "Record diesel prices raise fuel shortage fears", {"fuel_energy": ["Diesel"]})
    text = " ".join(
        [result["summary"]]
        + [item["dependency"] for item in result["mappings"]]
        + [value for item in result["mappings"] for value in item["potential_impacts"]]
        + [value for item in result["mappings"] for value in item["verification_checks"]]
        + result["data_limitations"]
    ).casefold()
    for invented in ("%", "crore", "lakh", "usd", "per month", "per year", "confirmed", "guaranteed"):
        assert invented not in text



def test_missing_risk_returns_empty_map(db):
    result = build_impact_map(db, 999999, user_id=None)
    assert result["mappings"] == []
    assert result["event_id"] is None


def test_mappings_do_not_contaminate_each_other(db):
    user = add_user(db)
    add_profile(db, user, {"fuel_energy": ["Diesel"], "materials": ["Semiconductors"]})
    _, diesel_risk = add_risk(db, title="Diesel supply shortage hits refineries")
    _, semi_risk = add_risk(db, title="Semiconductor wafer shortage delays production")

    diesel_map = build_impact_map(db, diesel_risk.id, user_id=user.id)
    semi_map = build_impact_map(db, semi_risk.id, user_id=user.id)
    assert [item["dependency"] for item in diesel_map["mappings"]] == ["Diesel"]
    assert [item["dependency"] for item in semi_map["mappings"]] == ["Semiconductors"]


def test_endpoint_and_permissions(db):
    from app.api.deps import get_current_user
    from app.database.database import get_db
    from app.routers.investigation import router

    user = add_user(db)
    add_profile(db, user, {"fuel_energy": ["Diesel"]})
    _, risk = add_risk(db, title="Diesel prices surge")

    def build(active_user):
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: active_user
        return TestClient(app)

    with build(user) as client:
        response = client.get(f"/investigations/risk/{risk.id}/impact-map")
    assert response.status_code == 200
    assert response.json()["mappings"][0]["dependency"] == "Diesel"

    with build(add_user(db, "viewer@example.com", role="viewer")) as client:
        assert client.get(f"/investigations/risk/{risk.id}/impact-map").status_code == 403

    with build(user) as client:
        assert client.get("/investigations/risk/999999/impact-map").status_code == 404


def test_endpoint_requires_authentication(db):
    from app.routers.investigation import router

    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        assert client.get("/investigations/risk/1/impact-map").status_code == 401


def test_no_database_writes(db):
    user = add_user(db)
    add_profile(db, user, {"fuel_energy": ["Diesel"]})
    _, risk = add_risk(db, title="Diesel prices surge")
    db.add(
        Prediction(
            risk_id=risk.id,
            predicted_risk="Financial",
            confidence_score=0.8,
            predicted_severity="High",
        )
    )
    db.commit()

    before = (
        db.query(Event).count(), db.query(Risk).count(), db.query(Prediction).count(),
        db.query(Recommendation).count(), db.query(CompanyProfile).count(),
        db.query(CompanyDependency).count(),
    )
    build_impact_map(db, risk.id, user_id=user.id)
    after = (
        db.query(Event).count(), db.query(Risk).count(), db.query(Prediction).count(),
        db.query(Recommendation).count(), db.query(CompanyProfile).count(),
        db.query(CompanyDependency).count(),
    )
    assert after == before
