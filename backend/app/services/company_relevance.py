from __future__ import annotations

import re
from collections.abc import Iterable


DIRECT = "direct"
INDIRECT = "indirect"
NONE = "no_identified_relevance"

RELEVANCE_LABELS = {
    DIRECT: "Company Relevant",
    INDIRECT: "Company Relevant",
    NONE: "General Intelligence",
}

DIRECT_CATEGORIES = ("materials", "fuel_energy", "logistics", "technology")
INDIRECT_ONLY_CATEGORIES = ("geographic_exposure",)

# Deterministic match terms per dependency value. A dependency matches an event
# when any of its terms is present in the event's searchable text.
DEPENDENCY_TERMS: dict[tuple[str, str], tuple[str, ...]] = {
    ("materials", "Semiconductors"): (
        "semiconductor", "semiconductors", "chip", "chips", "wafer", "wafers",
        "foundry", "hbm", "lithography", "chipmaker",
    ),
    ("materials", "Batteries"): (
        "battery", "batteries", "cathode", "anode", "lithium ion", "ev battery",
    ),
    ("materials", "Copper"): ("copper",),
    ("materials", "Steel"): ("steel",),
    ("materials", "Aluminum"): ("aluminum", "aluminium"),
    ("materials", "Lithium"): ("lithium",),
    ("materials", "Plastics"): ("plastic", "plastics", "polymer", "resin"),
    ("fuel_energy", "Petrol"): ("petrol", "gasoline"),
    ("fuel_energy", "Diesel"): ("diesel",),
    ("fuel_energy", "Natural Gas"): ("natural gas", "lng", "liquefied natural gas"),
    ("fuel_energy", "Electricity"): ("electricity", "power grid", "power demand", "electricity grid"),
    ("fuel_energy", "Coal"): ("coal",),
    ("logistics", "Road"): ("road freight", "trucking", "truck", "trucks", "highway", "haulage"),
    ("logistics", "Rail"): ("railway", "railways", "rail freight", "rail"),
    ("logistics", "Sea"): ("sea freight", "shipping", "shipment", "vessel", "freighter", "container ship"),
    ("logistics", "Air"): ("air freight", "air cargo", "flight", "flights", "airline", "airlines"),
    ("logistics", "Ports"): ("port", "ports", "harbor", "harbour", "terminal"),
    ("logistics", "Warehousing"): ("warehouse", "warehousing", "distribution center", "fulfilment center", "fulfillment center"),
    ("technology", "Cloud Services"): ("cloud", "hosting outage", "saas"),
    ("technology", "Semiconductors"): (
        "semiconductor", "semiconductors", "chip", "chips", "wafer", "wafers",
        "foundry", "hbm", "lithography", "chipmaker",
    ),
    ("technology", "Telecom"): ("telecom", "telecommunications", "subsea cable", "subsea cables", "fiber network"),
    ("technology", "Data Centers"): ("data center", "data centers", "data centre", "server farm"),
    ("geographic_exposure", "India"): ("india",),
    ("geographic_exposure", "China"): ("china", "chinese"),
    ("geographic_exposure", "Southeast Asia"): (
        "southeast asia", "vietnam", "vietnamese", "singapore", "malaysia",
        "indonesia", "thailand", "philippines", "cambodia", "myanmar",
    ),
    ("geographic_exposure", "Europe"): (
        "europe", "european union", "germany", "france", "spain", "italy",
        "netherlands", "rotterdam", "belgium", "poland",
    ),
    ("geographic_exposure", "North America"): (
        "united states", "usa", "u s", "canada", "canadian", "mexico",
    ),
    ("geographic_exposure", "Middle East"): (
        "middle east", "iran", "iranian", "saudi", "hormuz", "red sea",
        "israel", "emirates", "qatar", "iraq", "syria",
    ),
}

# An event that does not name a configured dependency but names a closely
# related concept the company does depend on.
INDIRECT_TERMS_FOR: dict[tuple[str, str], tuple[str, ...]] = {
    ("logistics", "Road"): (
        "fuel", "petroleum", "energy prices", "transport costs",
        "transportation costs", "freight rates", "freight costs",
    ),
    ("logistics", "Sea"): ("freight", "shipping costs", "container rates", "ocean freight"),
    ("logistics", "Air"): ("airfare", "jet fuel"),
    ("fuel_energy", "Diesel"): (
        "transport", "transportation", "trucking", "freight", "logistics",
        "haulage", "carrier", "carriers",
    ),
    ("fuel_energy", "Petrol"): ("transport", "transportation"),
    ("fuel_energy", "Natural Gas"): ("energy prices", "power generation", "electricity generation"),
    ("fuel_energy", "Electricity"): (
        "energy demand", "energy prices", "grid", "power prices",
        "renewables", "electrification",
    ),
    ("materials", "Semiconductors"): ("electronics", "consumer electronics"),
    ("technology", "Semiconductors"): (
        "electronics", "consumer electronics", "smartphone", "smartphones",
    ),
    ("materials", "Batteries"): ("electric vehicle", "electric vehicles", "electrification"),
    ("logistics", "Ports"): ("maritime", "dockside", "container"),
}

# Event categories/risk types that indicate the event is about this domain.
DOMAIN_HINTS: dict[tuple[str, str], tuple[str, ...]] = {
    ("materials", "Semiconductors"): ("logistics", "supply chain"),
    ("technology", "Semiconductors"): ("logistics", "supply chain"),
    ("materials", "Batteries"): ("logistics", "supply chain", "energy"),
    ("logistics", "Road"): ("logistics", "supply chain", "transport", "transportation"),
    ("logistics", "Sea"): ("logistics", "supply chain", "maritime", "shipping"),
    ("logistics", "Ports"): ("logistics", "supply chain", "maritime", "shipping"),
    ("logistics", "Air"): ("logistics", "supply chain", "aviation", "air cargo"),
    ("logistics", "Rail"): ("logistics", "supply chain"),
    ("logistics", "Warehousing"): ("logistics", "supply chain"),
    ("fuel_energy", "Electricity"): ("energy", "power"),
    ("fuel_energy", "Diesel"): ("energy", "fuel"),
}



def _normalize(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _contains(text: str, term: str) -> bool:
    normalized = _normalize(term)
    if not normalized:
        return False
    return f" {normalized} " in f" {text} "


def _matches(text: str, terms: Iterable[str]) -> list[str]:
    return [term for term in terms if _contains(text, term)]


def dependency_values(dependencies: dict[str, list[str]] | None) -> list[tuple[str, str]]:
    """Return configured (category, value) pairs, excluding 'None' and 'Other'."""
    pairs: list[tuple[str, str]] = []
    for category, values in (dependencies or {}).items():
        for value in values or []:
            if value in {"None", "Other"}:
                continue
            pairs.append((category, value))
    return pairs


def event_searchable_text(event: dict) -> str:
    parts = [
        event.get("title"),
        event.get("description"),
        event.get("category"),
        event.get("event_type"),
        event.get("source"),
    ]
    return _normalize(" ".join(part for part in parts if isinstance(part, str)))


def _risk_text(risk: dict | None) -> str:
    if not isinstance(risk, dict):
        return ""
    return _normalize(f"{risk.get('risk_type') or ''} {risk.get('risk_name') or ''}")




def _no_relevance(profile_missing: bool = False) -> dict:
    if profile_missing:
        reason = (
            "No company dependencies are configured yet, so SupplySentry cannot identify "
            "company relevance for this event."
        )
    else:
        reason = (
            "SupplySentry has no configured company dependency connecting this event to the "
            "company. This does not mean the event cannot affect the company; it means no "
            "configured dependency matches it."
        )
    return {
        "relevance": NONE,
        "label": RELEVANCE_LABELS[NONE],
        "matched_dependencies": [],
        "reason": reason,
        "direct_matches": [],
        "indirect_matches": [],
    }


def evaluate_event_relevance(
    event: dict,
    dependencies: dict[str, list[str]] | None,
    risk: dict | None = None,
) -> dict:
    """Explain whether an event connects to the company's configured dependencies.

    Pure function: no database access, so a semantic matcher can later replace or
    augment the deterministic matching without changing call sites.
    """
    configured = dependency_values(dependencies)
    if not configured:
        return _no_relevance(profile_missing=not bool(dependencies))

    text = event_searchable_text(event)
    location_text = _normalize(event.get("location")) if isinstance(event.get("location"), str) else ""
    risk_text = _risk_text(risk)
    direct: list[dict] = []
    indirect: list[dict] = []

    for category, value in configured:
        key = (category, value)
        value_terms = DEPENDENCY_TERMS.get(key, ())
        if not value_terms:
            continue

        direct_hits = _matches(text, value_terms)
        if direct_hits:
            direct.append({
                "category": category,
                "value": value,
                "matched_terms": sorted(set(direct_hits)),
                "matched_on": "event_text",
            })
            continue

        if category in INDIRECT_ONLY_CATEGORIES:
            if location_text and _contains(location_text, value):
                indirect.append({
                    "category": category,
                    "value": value,
                    "matched_terms": [value],
                    "matched_on": "event_location",
                })
            continue

        domain_hints = DOMAIN_HINTS.get(key, ())
        domain_hit = bool(domain_hints) and bool(_matches(risk_text or text, domain_hints))
        indirect_hits = _matches(text, INDIRECT_TERMS_FOR.get(key, ()))

        if indirect_hits and domain_hit:
            indirect.append({
                "category": category,
                "value": value,
                "matched_terms": sorted(set(indirect_hits)),
                "matched_on": "structured_relationship",
            })
        elif location_text and _contains(location_text, value) and domain_hit:
            indirect.append({
                "category": category,
                "value": value,
                "matched_terms": [value],
                "matched_on": "event_location",
            })

    matched = direct + indirect
    if not matched:
        return _no_relevance()

    # Geographic exposure may contribute to a match, but it can never create
    # company relevance on its own: it must accompany a non-geographic
    # dependency that the event actually relates to.
    has_direct_dependency = any(item["category"] in DIRECT_CATEGORIES for item in direct)
    has_indirect_dependency = any(item["category"] in DIRECT_CATEGORIES for item in indirect)
    if not has_direct_dependency and not has_indirect_dependency:
        return _no_relevance()

    relevance = DIRECT if has_direct_dependency else INDIRECT

    primary = matched[0]
    if relevance == DIRECT and len(matched) > 1:
        reason = (
            f"This event directly names {len(matched)} configured company dependencies, "
            f"starting with {_describe(primary['category'], primary['value'])}."
        )
    elif relevance == DIRECT:
        reason = (
            "The event directly names a configured company dependency: "
            f"{_describe(primary['category'], primary['value'])}."
        )
    elif len(matched) > 1:
        reason = (
            "The event does not name a configured dependency directly, but it has a "
            f"structured relationship to {len(matched)} configured dependencies, starting "
            f"with {_describe(primary['category'], primary['value'])}."
        )
    else:
        reason = (
            "The event does not name a configured dependency directly, but it has a "
            f"structured relationship to {_describe(primary['category'], primary['value'])}."
        )

    return {
        "relevance": relevance,
        "label": RELEVANCE_LABELS[relevance],
        "matched_dependencies": matched,
        "reason": reason,
        "direct_matches": direct,
        "indirect_matches": indirect,
    }

def _describe(category: str, value: str) -> str:
    return f"{value} ({category.replace('_', ' ')})"
