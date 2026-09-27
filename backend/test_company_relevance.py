from app.services.company_relevance import (
    DIRECT,
    INDIRECT,
    NONE,
    evaluate_event_relevance,
)

TECHNOVA = {
    "company_name": "TechNova Electronics",
    "industry": "Consumer Electronics",
    "dependencies": {
        "materials": ["Semiconductors", "Batteries", "None"],
        "fuel_energy": ["Diesel", "None"],
        "logistics": ["Road", "Sea", "None"],
        "technology": ["None"],
        "geographic_exposure": ["India", "China", "None"],
    },
}


def event(title, **overrides):
    payload = {
        "title": title,
        "description": "",
        "category": "Logistics",
        "event_type": "News",
        "location": "Unknown",
    }
    payload.update(overrides)
    return payload


def matches(result):
    return {(item["category"], item["value"]) for item in result["matched_dependencies"]}


def test_semiconductor_dependency_matches_directly():
    result = evaluate_event_relevance(
        event("Major semiconductor manufacturer warns of supply disruption"),
        TECHNOVA["dependencies"],
    )

    assert result["relevance"] == DIRECT
    assert ("materials", "Semiconductors") in matches(result)
    assert "semiconductor" in result["direct_matches"][0]["matched_terms"]


def test_company_without_semiconductor_dependency_has_no_direct_match():
    dependencies = dict(TECHNOVA["dependencies"], materials=["Batteries"])

    result = evaluate_event_relevance(
        event("Major semiconductor manufacturer warns of supply disruption"),
        dependencies,
    )

    assert ("materials", "Semiconductors") not in matches(result)
    assert result["relevance"] == NONE


def test_diesel_and_road_dependencies_match_diesel_event():
    result = evaluate_event_relevance(
        event("Diesel prices rise sharply across India"),
        TECHNOVA["dependencies"],
    )

    assert result["relevance"] == DIRECT
    assert ("fuel_energy", "Diesel") in matches(result)
    assert ("geographic_exposure", "India") in matches(result)


def test_transport_cost_event_is_indirect_for_road_dependency():
    dependencies = {
        "materials": ["None"],
        "fuel_energy": ["None"],
        "logistics": ["Road"],
        "technology": ["None"],
        "geographic_exposure": ["None"],
    }

    result = evaluate_event_relevance(
        event("Freight costs surge on major transport corridors"),
        dependencies,
    )

    assert result["relevance"] == INDIRECT
    assert matches(result) == {("logistics", "Road")}
    assert result["indirect_matches"][0]["matched_on"] == "structured_relationship"


def test_geographic_exposure_alone_does_not_make_an_event_relevant():
    dependencies = {
        "materials": ["None"],
        "fuel_energy": ["None"],
        "logistics": ["None"],
        "technology": ["None"],
        "geographic_exposure": ["India", "China"],
    }

    result = evaluate_event_relevance(
        event(
            "Local festival opens in Mumbai",
            category="General",
            location="India",
        ),
        dependencies,
    )

    assert result["relevance"] == NONE


def test_geographic_exposure_contributes_to_relevant_maritime_event():
    result = evaluate_event_relevance(
        event(
            "Port disruption affects Chinese semiconductor exports",
            location="China",
        ),
        TECHNOVA["dependencies"],
    )

    assert result["relevance"] == DIRECT
    assert ("geographic_exposure", "China") in matches(result)
    assert ("materials", "Semiconductors") in matches(result)


def test_unrelated_event_returns_no_identified_relevance():
    result = evaluate_event_relevance(
        event("Wheat prices rise following poor harvest", category="General"),
        TECHNOVA["dependencies"],
    )

    assert result["relevance"] == NONE
    assert result["matched_dependencies"] == []
    assert "does not mean the event cannot affect the company" in result["reason"]


def test_multiple_matching_dependencies_are_all_returned():
    result = evaluate_event_relevance(
        event("Battery material disruption hits lithium supply chain in China"),
        TECHNOVA["dependencies"],
    )

    assert result["relevance"] == DIRECT
    assert len(result["matched_dependencies"]) >= 2
    assert ("materials", "Batteries") in matches(result)


def test_other_and_none_dependencies_do_not_create_matches():
    dependencies = {
        "materials": ["Other", "None"],
        "fuel_energy": ["Other", "None"],
        "logistics": ["Other", "None"],
        "technology": ["Other", "None"],
        "geographic_exposure": ["Other", "None"],
    }

    result = evaluate_event_relevance(
        event("Semiconductor shortage in China disrupts road freight"),
        dependencies,
    )

    assert result["relevance"] == NONE


def test_missing_profile_dependencies_return_explanatory_result():
    result = evaluate_event_relevance(event("Anything at all"), None)

    assert result["relevance"] == NONE
    assert "No company dependencies are configured" in result["reason"]


def test_risk_context_enables_relationship_matching():
    dependencies = {
        "materials": ["None"],
        "fuel_energy": ["Diesel"],
        "logistics": ["None"],
        "technology": ["None"],
        "geographic_exposure": ["None"],
    }

    without_risk = evaluate_event_relevance(
        event("Carriers report rising operating costs"),
        dependencies,
    )
    with_risk = evaluate_event_relevance(
        event("Carriers report rising operating costs"),
        dependencies,
        {"risk_type": "Energy", "risk_name": "Fuel cost increase"},
    )

    assert without_risk["relevance"] == NONE
    assert with_risk["relevance"] == INDIRECT
