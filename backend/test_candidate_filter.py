from app.ai.candidate_filter import classify_candidate
from app.integrations.news_api import is_supply_chain_related
from app.services.ingestion_metrics import base_stats, record_candidate_shadow


def result(text):
    return classify_candidate({"title": text, "description": ""})


def test_word_boundaries_and_generic_terms():
    assert result("ship")["passed"] is False
    assert result("shipped a software release")["reason"] == "no_relevant_terms"
    assert result("shipping")["reason"] == "generic_domain_only"
    assert result("road")["reason"] == "generic_domain_only"
    assert result("infrastructure")["reason"] == "generic_domain_only"


def test_explicit_phrases_and_domain_event_combinations():
    assert result("Port closure")["reason"] == "explicit_phrase"
    assert result("Port closure at the terminal")["reason"] == "explicit_phrase"
    assert result("vessel attack near a trade route")["passed"] is True
    assert result("factory shutdown")["passed"] is True
    assert result("logistics delay")["reason"] == "strong_event_context"
    assert result("trade route disruption")["reason"] == "explicit_phrase"


def test_preserved_energy_trade_and_weather_cases():
    assert result("pipeline outage")["reason"] == "explicit_phrase"
    assert result("pipeline therapies address unmet needs")["passed"] is False
    assert result("energy infrastructure attack")["reason"] == "explicit_phrase"
    assert result("refinery outage")["reason"] == "explicit_phrase"
    assert result("sanctions on exports")["reason"] == "preserved_trade_event"
    assert result("storm disrupted logistics")["reason"] == "preserved_weather_event"


def test_generic_corporate_announcement_is_rejected():
    decision = result("Manufacturing company announces a new product line")
    assert decision["passed"] is False
    assert decision["reason"] == "generic_domain_only"


def test_empty_and_malformed_text_are_safe():
    assert classify_candidate({})["reason"] == "no_relevant_terms"
    assert classify_candidate({"title": None, "description": 123})["reason"] == "no_relevant_terms"
    assert classify_candidate(None)["reason"] == "no_relevant_terms"


def test_existing_production_keyword_filter_behavior_is_unchanged():
    assert is_supply_chain_related({"title": "shipping", "description": ""}) is True
    assert is_supply_chain_related({"title": "road", "description": ""}) is True
    assert is_supply_chain_related({"title": "pipeline therapies", "description": ""}) is True
    assert is_supply_chain_related({"title": "shipped software", "description": ""}) is True
    assert is_supply_chain_related({"title": "unrelated music review", "description": ""}) is False


def test_shadow_metrics_record_both_decisions_and_reason():
    stats = base_stats("cycle", "Currents API", "query")
    record_candidate_shadow(stats, True, {"passed": True, "reason": "domain_event"})
    record_candidate_shadow(stats, True, {"passed": False, "reason": "generic_domain_only"})
    record_candidate_shadow(stats, False, {"passed": True, "reason": "preserved_energy_event"})
    record_candidate_shadow(stats, False, {"passed": False, "reason": "no_relevant_terms"})

    assert stats["proposed_classifier_passed"] == 2
    assert stats["proposed_classifier_rejected"] == 2
    assert stats["current_pass_proposed_pass"] == 1
    assert stats["current_pass_proposed_reject"] == 1
    assert stats["current_reject_proposed_pass"] == 1
    assert stats["current_reject_proposed_reject"] == 1
    assert stats["proposed_reason_counts"]["domain_event"] == 1


def article(title, description=""):
    return classify_candidate({"title": title, "description": description})


def test_aviation_disruptions_and_advisories_pass():
    assert (
        result("Over 774 flights delayed and canceled amid travel disruptions")["reason"]
        == "preserved_aviation_event"
    )
    assert result("Airlines cancel flights as airspace closed")["reason"] == "preserved_aviation_event"
    assert (
        result("US government issues travel advisory for airspace closures")["reason"]
        == "preserved_aviation_signal"
    )


def test_energy_security_soft_language_passes():
    assert result("France faces diesel crisis")["reason"] == "preserved_energy_signal"
    assert result("Politicians panic over record-high diesel costs")["reason"] == "preserved_energy_signal"
    assert result("India and Opec discuss oil market stability")["reason"] == "preserved_energy_signal"
    assert result("Nations meet to discuss energy security")["reason"] == "preserved_energy_signal"


def test_fuel_flow_changes_pass():
    assert result("India's Russian oil imports fall 17%")["reason"] == "preserved_fuel_flow"
    assert result("Government moves to cut petrol and diesel imports")["reason"] == "preserved_fuel_flow"
    assert result("Crude oil exports drop sharply")["passed"] is True


def test_labor_and_transit_disruptions_pass():
    assert result("Dockworkers strike halts port operations")["reason"] == "preserved_labor_disruption"
    assert result("Transit workers strike disrupts rail service")["reason"] == "preserved_labor_disruption"
    assert result("Port workers walkout delays cargo")["reason"] == "preserved_labor_disruption"


def test_semiconductor_supply_signals_pass():
    decision = article(
        "Samsung considers expanding 4nm capacity as HBM4 demand rises",
        "Memory demand continues to outpace supply, particularly for high-bandwidth memory.",
    )
    assert decision["reason"] == "preserved_semiconductor_signal"
    assert result("Chipmaker warns of wafer shortage")["reason"] == "preserved_semiconductor_signal"


def test_sanctions_touching_aviation_fuel_and_shipping_pass():
    assert (
        result("US sanctions on Iranian civil aviation come into force")["reason"]
        == "preserved_trade_event"
    )
    assert result("US sanctions on shipping companies")["reason"] == "preserved_trade_event"
    assert result("New sanctions target semiconductor exports")["reason"] == "preserved_trade_event"


def test_soft_signals_reject_generic_business_news():
    assert result("Oil firm reports record-high dividend")["reason"] == "generic_business_announcement"
    assert (
        result("Chipmaker announces a new product line with more capacity")["reason"]
        == "generic_business_announcement"
    )
    assert (
        result("Fuel supplier announces record-high quarterly profit")["reason"]
        == "generic_business_announcement"
    )
    assert result("Supplier named a leader in procurement technology")["passed"] is False
    assert result("Company wins award for logistics innovation")["passed"] is False
    assert result("Aviation startup named a leader in industry awards")["passed"] is False


def test_domain_terms_alone_do_not_pass():
    for token in ("aviation", "diesel", "fuel", "workers", "transit", "wafer"):
        decision = result(token)
        assert decision["passed"] is False, token
        assert decision["reason"] == "generic_domain_only", token


def test_existing_reasons_and_rejections_are_preserved():
    assert result("logistics delay")["reason"] == "strong_event_context"
    assert result("sanctions on exports")["reason"] == "preserved_trade_event"
    assert result("storm disrupted logistics")["reason"] == "preserved_weather_event"
    assert result("pipeline therapies address unmet needs")["passed"] is False
    assert result("shipped a software release")["reason"] == "no_relevant_terms"
    assert result("Manufacturing company announces a new product line")["reason"] == "generic_domain_only"


def test_malformed_inputs_remain_safe():
    assert classify_candidate({"title": None, "description": None})["reason"] == "no_relevant_terms"
    assert classify_candidate({"title": ["x"], "description": 5})["reason"] == "no_relevant_terms"
    assert classify_candidate("not a dict")["reason"] == "no_relevant_terms"
