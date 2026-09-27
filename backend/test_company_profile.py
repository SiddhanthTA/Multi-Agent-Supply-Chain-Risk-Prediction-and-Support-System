import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user
from app.database.database import Base, get_db
import app.models
from app.models.user import User
from app.models.company_profile import CompanyDependency, CompanyProfile
from app.models.event import Event
from app.models.risk import Risk
from app.routers.company_profile import router
from app.schemas.company_profile import CompanyProfileRequest


@pytest.fixture()
def company_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        engine,
        tables=[
            User.__table__,
            CompanyProfile.__table__,
            CompanyDependency.__table__,
            Event.__table__,
            Risk.__table__,
        ],
    )
    TestingSession = sessionmaker(bind=engine)
    with TestingSession() as db:
        yield db


def user_row(db, user_id, email):
    user = User(
        id=user_id,
        username=f"user{user_id}",
        email=email,
        password="hashed",
        role="analyst",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def client_for(db, user):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def payload(**overrides):
    data = {
        "company_name": "TechNova Electronics",
        "industry": "Consumer Electronics",
        "dependencies": {
            "materials": ["Semiconductors", "Batteries"],
            "fuel_energy": ["Diesel"],
            "logistics": ["Road", "Sea"],
            "technology": ["Data Centers"],
            "geographic_exposure": ["India", "China"],
        },
    }
    data.update(overrides)
    return data


def intelligence_rows(db):
    chip_event = Event(
        title="Major semiconductor manufacturer warns of supply disruption",
        description="Chip output is expected to fall next quarter.",
        event_type="News",
        location="China",
        category="Logistics",
        status="Active",
    )
    harvest_event = Event(
        title="Wheat prices rise following poor harvest",
        event_type="News",
        location="Unknown",
        category="General",
        status="Active",
    )
    db.add_all([chip_event, harvest_event])
    db.flush()
    db.add(
        Risk(
            event_id=chip_event.id,
            risk_name="Supply disruption",
            risk_type="Logistics",
            risk_score=90,
            severity="High",
            status="Active",
        )
    )
    db.commit()
    return chip_event, harvest_event


def relevance_for(body, event_id):
    return next(item for item in body["events"] if item["event_id"] == event_id)


def level_of(row):
    return row["relevance"]["relevance"]


def test_relevance_endpoint_requires_authentication(company_db):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: company_db
    with TestClient(app) as client:
        assert client.get("/company-profile/relevance").status_code == 401


def test_relevance_summary_reports_levels_and_matches(company_db):
    user = user_row(company_db, 1, "owner@example.com")
    client = client_for(company_db, user)
    chip_event, harvest_event = intelligence_rows(company_db)
    client.put("/company-profile", json=payload())

    body = client.get("/company-profile/relevance").json()

    assert body["company_name"] == "TechNova Electronics"
    assert body["total_events"] == 2
    assert body["direct_count"] == 1
    assert body["no_identified_count"] == 1
    assert level_of(relevance_for(body, chip_event.id)) == "direct"
    assert level_of(relevance_for(body, harvest_event.id)) == "no_identified_relevance"
    assert body["top_relevant_events"][0]["event_id"] == chip_event.id


def test_relevance_preserves_existing_risk_classification(company_db):
    user = user_row(company_db, 1, "owner@example.com")
    client = client_for(company_db, user)
    chip_event, _ = intelligence_rows(company_db)
    client.put("/company-profile", json=payload())

    body = client.get("/company-profile/relevance").json()
    row = relevance_for(body, chip_event.id)

    assert row["severity"] == "High"
    assert company_db.query(Risk).count() == 1
    assert company_db.query(Event).count() == 2



def stored_dependency_rows(company_db, user_id):
    profile = (
        company_db.query(CompanyProfile)
        .filter(CompanyProfile.user_id == user_id)
        .first()
    )
    return sorted(
        (dependency.category, dependency.value)
        for dependency in profile.dependencies
    )


def test_updating_unchanged_dependencies_does_not_violate_unique_constraint(company_db):
    """Regression: re-saving the same dependency set used to raise UniqueViolation."""
    user = user_row(company_db, 1, "owner@example.com")
    client = client_for(company_db, user)
    body = payload(dependencies={"materials": ["Semiconductors"]})

    assert client.put("/company-profile", json=body).status_code == 200

    update = client.put("/company-profile", json=body)

    assert update.status_code == 200
    assert update.json()["dependencies"]["materials"] == ["Semiconductors"]
    assert stored_dependency_rows(company_db, user.id) == [("materials", "Semiconductors")]


def test_update_can_add_replace_and_remove_dependencies(company_db):
    user = user_row(company_db, 1, "owner@example.com")
    client = client_for(company_db, user)
    client.put("/company-profile", json=payload(dependencies={"materials": ["Semiconductors", "Batteries"]}))

    added = client.put(
        "/company-profile",
        json=payload(dependencies={"materials": ["Semiconductors", "Batteries", "Lithium"]}),
    )
    assert added.status_code == 200
    assert added.json()["dependencies"]["materials"] == ["Semiconductors", "Batteries", "Lithium"]

    replaced = client.put(
        "/company-profile",
        json=payload(dependencies={"materials": ["Copper"]}),
    )
    assert replaced.status_code == 200
    assert replaced.json()["dependencies"]["materials"] == ["Copper"]

    removed = client.put(
        "/company-profile",
        json=payload(dependencies={"materials": []}),
    )
    assert removed.status_code == 200
    assert removed.json()["dependencies"]["materials"] == ["None"]
    assert stored_dependency_rows(company_db, user.id) == [("materials", "None")]


def test_update_across_multiple_categories_and_none_handling(company_db):
    user = user_row(company_db, 1, "owner@example.com")
    client = client_for(company_db, user)
    client.put("/company-profile", json=payload())

    updated = client.put(
        "/company-profile",
        json=payload(
            dependencies={
                "materials": ["Semiconductors"],
                "fuel_energy": ["Diesel", "Coal"],
                "logistics": ["None"],
                "technology": ["Cloud Services"],
                "geographic_exposure": ["India", "Europe"],
            },
        ),
    )

    assert updated.status_code == 200
    body = updated.json()
    assert body["dependencies"]["fuel_energy"] == ["Diesel", "Coal"]
    assert body["dependencies"]["logistics"] == ["None"]
    assert body["dependencies"]["geographic_exposure"] == ["India", "Europe"]
    assert stored_dependency_rows(company_db, user.id) == sorted(
        [
            ("materials", "Semiconductors"),
            ("fuel_energy", "Diesel"),
            ("fuel_energy", "Coal"),
            ("logistics", "None"),
            ("technology", "Cloud Services"),
            ("geographic_exposure", "India"),
            ("geographic_exposure", "Europe"),
        ]
    )

    restored = client.put(
        "/company-profile",
        json=payload(dependencies={"logistics": ["Road"]}),
    )
    assert restored.status_code == 200
    assert restored.json()["dependencies"]["logistics"] == ["Road"]


def test_repeated_updates_never_create_duplicate_rows(company_db):
    user = user_row(company_db, 1, "owner@example.com")
    client = client_for(company_db, user)
    body = payload(dependencies={"materials": ["Semiconductors", "Batteries"]})

    client.put("/company-profile", json=body)
    for _ in range(3):
        assert client.put("/company-profile", json=body).status_code == 200

    rows = stored_dependency_rows(company_db, user.id)
    assert set(rows) == {("materials", "Semiconductors"), ("materials", "Batteries")}
    assert len(rows) == len(set(rows))


def test_relevance_is_isolated_per_company(company_db):
    first = user_row(company_db, 1, "first@example.com")
    second = user_row(company_db, 2, "second@example.com")
    chip_event, _ = intelligence_rows(company_db)
    first_client = client_for(company_db, first)
    second_client = client_for(company_db, second)

    first_client.put("/company-profile", json=payload())
    second_client.put(
        "/company-profile",
        json=payload(dependencies={"materials": ["Copper"]}),
    )

    first_row = relevance_for(
        first_client.get("/company-profile/relevance").json(),
        chip_event.id,
    )
    second_row = relevance_for(
        second_client.get("/company-profile/relevance").json(),
        chip_event.id,
    )

    assert level_of(first_row) == "direct"
    assert level_of(second_row) == "no_identified_relevance"


def test_changing_dependencies_changes_relevance(company_db):
    user = user_row(company_db, 1, "owner@example.com")
    client = client_for(company_db, user)
    chip_event, _ = intelligence_rows(company_db)

    client.put("/company-profile", json=payload())
    assert level_of(
        relevance_for(client.get("/company-profile/relevance").json(), chip_event.id)
    ) == "direct"

    client.put(
        "/company-profile",
        json=payload(dependencies={"materials": ["Copper"]}),
    )
    assert level_of(
        relevance_for(client.get("/company-profile/relevance").json(), chip_event.id)
    ) == "no_identified_relevance"


def test_single_event_relevance_endpoint(company_db):
    user = user_row(company_db, 1, "owner@example.com")
    client = client_for(company_db, user)
    chip_event, harvest_event = intelligence_rows(company_db)
    client.put("/company-profile", json=payload())

    direct = client.get(f"/company-profile/relevance/events/{chip_event.id}").json()
    none = client.get(f"/company-profile/relevance/events/{harvest_event.id}").json()
    missing = client.get("/company-profile/relevance/events/999999")

    assert direct["relevance"]["relevance"] == "direct"
    assert direct["relevance"]["matched_dependencies"]
    assert none["relevance"]["relevance"] == "no_identified_relevance"
    assert missing.status_code == 404


def test_profile_requires_authentication(company_db):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: company_db
    with TestClient(app) as client:
        assert client.get("/company-profile").status_code == 401


def test_profile_create_read_and_update(company_db):
    user = user_row(company_db, 1, "owner@example.com")
    client = client_for(company_db, user)

    created = client.put("/company-profile", json=payload())
    assert created.status_code == 200
    assert created.json()["company_name"] == "TechNova Electronics"
    assert created.json()["dependencies"]["materials"] == ["Semiconductors", "Batteries"]
    assert created.json()["dependencies"]["logistics"] == ["Road", "Sea"]

    read = client.get("/company-profile")
    assert read.status_code == 200
    assert read.json()["industry"] == "Consumer Electronics"
    assert read.json()["dependencies"]["fuel_energy"] == ["Diesel"]

    updated = client.put(
        "/company-profile",
        json=payload(
            company_name="TechNova Updated",
            dependencies={
                "materials": ["Copper"],
                "fuel_energy": ["Electricity", "Coal"],
                "logistics": ["Air"],
                "technology": ["Cloud Services"],
                "geographic_exposure": ["Europe"],
            },
        ),
    )
    assert updated.status_code == 200
    assert updated.json()["company_name"] == "TechNova Updated"
    assert updated.json()["dependencies"]["materials"] == ["Copper"]
    assert updated.json()["dependencies"]["fuel_energy"] == ["Electricity", "Coal"]


def test_profile_normalizes_none_and_rejects_unknown_values(company_db):
    user = user_row(company_db, 1, "owner@example.com")
    client = client_for(company_db, user)

    normalized = CompanyProfileRequest(
        **payload(
            dependencies={
                "materials": ["Semiconductors", "None"],
                "fuel_energy": [],
            }
        )
    )
    assert normalized.dependencies["materials"] == ["None"]
    assert normalized.dependencies["fuel_energy"] == ["None"]

    invalid = client.put(
        "/company-profile",
        json=payload(dependencies={"materials": ["Unobtainium"]}),
    )
    assert invalid.status_code == 422


def test_profile_is_isolated_between_authenticated_users(company_db):
    first = user_row(company_db, 1, "first@example.com")
    second = user_row(company_db, 2, "second@example.com")
    first_client = client_for(company_db, first)
    second_client = client_for(company_db, second)

    first_client.put("/company-profile", json=payload(company_name="First Company"))
    assert first_client.get("/company-profile").json()["company_name"] == "First Company"
    assert second_client.get("/company-profile").status_code == 404

    second_client.put("/company-profile", json=payload(company_name="Second Company"))
    assert second_client.get("/company-profile").json()["company_name"] == "Second Company"
    assert first_client.get("/company-profile").json()["company_name"] == "First Company"


def test_profile_is_not_found_before_setup(company_db):
    user = user_row(company_db, 1, "new@example.com")
    client = client_for(company_db, user)
    assert client.get("/company-profile").status_code == 404
