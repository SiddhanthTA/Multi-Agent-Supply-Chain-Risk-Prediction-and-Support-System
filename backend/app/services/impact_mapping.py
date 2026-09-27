"""Deterministic Supply Chain Impact Mapping (read-only).

Answers "which parts of this company's supply chain could potentially be
affected by this risk?" by mapping the company dependencies that the EXISTING
company relevance engine already matched to fixed supply-chain areas,
potential impacts, and verification checks.

This is potential impact mapping, not a prediction of actual company losses.
SupplySentry stores configured dependencies, not supplier contracts, purchase
volumes, fuel consumption, inventory, or financial exposure, so every output
stays explicitly potential and the response lists those limitations.

No LLM, no persistence, no new relevance logic: dependency matching is fully
delegated to ``evaluate_event_relevance``.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.crud.company_profile import _dependency_values, get_company_profile
from app.models.event import Event
from app.models.prediction import Prediction
from app.models.risk import Risk
from app.services.company_relevance import DIRECT, INDIRECT, NONE, evaluate_event_relevance

# Bounded output, per the feature requirements.
MAX_MAPPINGS = 5
MAX_AREAS = 4
MAX_IMPACTS = 4
MAX_CHECKS = 5

# "None" and "Other" are placeholders in the taxonomy, not real dependencies.
PLACEHOLDER_DEPENDENCIES = frozenset({"None", "Other"})

DATA_LIMITATIONS = (
    "Actual supplier contracts and shipment volumes are not stored.",
    "Fuel consumption, inventory, and carrier arrangements are not stored.",
    "Actual financial or operational exposure cannot be quantified from available data.",
)

GEOGRAPHIC_CATEGORY = "geographic_exposure"
# Dependency -> (supply chain areas, potential impacts, verification checks).
# Keys are the configured dependency values from the existing taxonomy.
DEPENDENCY_MAPPINGS: dict[str, dict[str, tuple[str, ...]]] = {
    "Diesel": {
        "areas": ("Transportation", "Logistics", "Delivery Operations", "Fleet Operations"),
        "impacts": (
            "Fuel availability pressure",
            "Transportation cost pressure",
            "Delivery timing pressure",
            "Route and fleet continuity pressure",
        ),
        "checks": (
            "Fuel consumption",
            "Fuel procurement arrangements",
            "Carrier contracts",
            "Upcoming fuel-dependent shipments",
            "Alternative carriers and routes",
        ),
    },
    "Petrol": {
        "areas": ("Transportation", "Logistics", "Delivery Operations", "Fleet Operations"),
        "impacts": ("Fuel availability pressure", "Transportation cost pressure", "Delivery timing pressure"),
        "checks": ("Fuel consumption", "Fuel procurement arrangements", "Carrier contracts", "Upcoming fuel-dependent shipments"),
    },
    "Semiconductors": {
        "areas": ("Procurement", "Manufacturing", "Electronics Production", "Supplier Management"),
        "impacts": (
            "Component availability pressure",
            "Procurement lead-time pressure",
            "Production scheduling pressure",
            "Supplier concentration exposure",
        ),
        "checks": ("Semiconductor suppliers", "Current inventory", "Open purchase orders", "Supplier lead times", "Alternative suppliers"),
    },
    "Batteries": {
        "areas": ("Procurement", "Manufacturing", "Supplier Management", "Operations"),
        "impacts": ("Component availability pressure", "Procurement lead-time pressure", "Production scheduling pressure"),
        "checks": ("Battery suppliers", "Current inventory", "Open purchase orders", "Alternative suppliers"),
    },
    "Ports": {
        "areas": ("Logistics", "Import/Export Operations", "Transportation", "Distribution"),
        "impacts": ("Shipment delay risk", "Port congestion exposure", "Routing pressure", "Delivery timing pressure"),
        "checks": ("Port-dependent shipments", "Current routes", "Carrier commitments", "Shipment schedules", "Alternative ports"),
    },
    "Road": {
        "areas": ("Transportation", "Distribution", "Last-Mile Operations"),
        "impacts": ("Route disruption", "Delivery delay", "Transportation availability pressure"),
        "checks": ("Road-dependent routes", "Upcoming shipments", "Alternative routes", "Carrier availability"),
    },
    "Rail": {
        "areas": ("Transportation", "Bulk Logistics", "Distribution"),
        "impacts": ("Rail service disruption", "Shipment timing pressure", "Alternative transport requirements"),
        "checks": ("Rail-dependent shipments", "Rail schedules", "Alternative transport capacity"),
    },
    "Sea": {
        "areas": ("Maritime Logistics", "Import/Export Operations", "Transportation"),
        "impacts": ("Shipping delays", "Freight availability pressure", "Route disruption"),
        "checks": ("Sea-freight exposure", "Current routes", "Vessel and carrier commitments", "Alternative routes"),
    },
    "Air": {
        "areas": ("Air Freight", "Logistics", "Time-sensitive Distribution"),
        "impacts": ("Air-freight availability pressure", "Shipment delay", "Freight cost pressure"),
        "checks": ("Air-freight dependence", "Upcoming shipments", "Carrier contracts", "Alternative transport modes"),
    },
    "Warehousing": {
        "areas": ("Warehousing", "Distribution", "Operations"),
        "impacts": ("Storage capacity pressure", "Inventory handling continuity pressure", "Order fulfilment timing pressure"),
        "checks": ("Warehouse utilisation", "Inventory levels", "Third-party logistics arrangements"),
    },
    "Natural Gas": {
        "areas": ("Energy Procurement", "Operations", "Manufacturing"),
        "impacts": ("Energy availability pressure", "Energy cost pressure", "Production continuity pressure"),
        "checks": ("Energy consumption", "Energy supply arrangements", "Alternative energy sources"),
    },
    "Electricity": {
        "areas": ("Energy Procurement", "Operations", "Manufacturing"),
        "impacts": ("Power availability pressure", "Energy cost pressure", "Production continuity pressure"),
        "checks": ("Electricity consumption", "Power supply arrangements", "Backup power arrangements"),
    },
    "Coal": {
        "areas": ("Energy Procurement", "Operations"),
        "impacts": ("Energy availability pressure", "Energy cost pressure"),
        "checks": ("Energy consumption", "Energy supply arrangements"),
    },
    "Copper": {
        "areas": ("Procurement", "Manufacturing", "Supplier Management"),
        "impacts": ("Component availability pressure", "Procurement lead-time pressure"),
        "checks": ("Copper suppliers", "Current inventory", "Open purchase orders"),
    },
    "Steel": {
        "areas": ("Procurement", "Manufacturing", "Supplier Management"),
        "impacts": ("Component availability pressure", "Procurement lead-time pressure"),
        "checks": ("Steel suppliers", "Current inventory", "Open purchase orders"),
    },
    "Aluminum": {
        "areas": ("Procurement", "Manufacturing", "Supplier Management"),
        "impacts": ("Component availability pressure", "Procurement lead-time pressure"),
        "checks": ("Aluminum suppliers", "Current inventory", "Open purchase orders"),
    },
    "Lithium": {
        "areas": ("Procurement", "Manufacturing", "Supplier Management"),
        "impacts": ("Component availability pressure", "Procurement lead-time pressure"),
        "checks": ("Lithium suppliers", "Current inventory", "Open purchase orders"),
    },
    "Plastics": {
        "areas": ("Procurement", "Manufacturing", "Supplier Management"),
        "impacts": ("Material availability pressure", "Procurement lead-time pressure"),
        "checks": ("Plastic suppliers", "Current inventory", "Open purchase orders"),
    },
    "Cloud Services": {
        "areas": ("IT Operations", "Digital Services", "Operations"),
        "impacts": ("Service availability pressure", "Business continuity pressure"),
        "checks": ("Service dependencies", "Provider arrangements", "Fallback capability"),
    },
    "Telecom": {
        "areas": ("IT Operations", "Communications", "Operations"),
        "impacts": ("Connectivity availability pressure", "Business continuity pressure"),
        "checks": ("Network dependencies", "Provider arrangements", "Fallback capability"),
    },
    "Data Centers": {
        "areas": ("IT Operations", "Digital Services", "Operations"),
        "impacts": ("Capacity availability pressure", "Service continuity pressure"),
        "checks": ("Capacity arrangements", "Provider dependencies", "Redundancy status"),
    },
}

# Used for a configured dependency with no specialised mapping above.
GENERIC_MAPPING = {
    "areas": ("Procurement", "Supplier Management", "Operations"),
    "impacts": ("Supply availability pressure", "Procurement timing pressure", "Operational continuity pressure"),
    "checks": ("Supplier exposure", "Current inventory", "Open orders", "Alternative suppliers"),
}

# Geographic exposure describes where the company operates, not what it
# consumes, so it maps to location-facing areas rather than procurement.
GEOGRAPHIC_MAPPING = {
    "areas": ("Regional Operations", "Distribution", "Market Coverage"),
    "impacts": ("Regional availability pressure", "Regional logistics continuity pressure"),
    "checks": ("Activity in the configured region", "Regional supplier and route dependencies", "Alternative sourcing regions"),
}

# (category, value) -> (impact, check) refinements applied only when the event
# text actually contains the trigger words. No causation is inferred.
REFINEMENTS: dict[tuple[str, str], dict[str, tuple[str, ...]]] = {
    ("fuel_energy", "Diesel"): {
        "shortage": ("Fuel availability pressure", "Fuel supply continuity pressure"),
        "ban": ("Fuel availability pressure", "Procurement source continuity pressure"),
        "restriction": ("Fuel availability pressure", "Procurement source continuity pressure"),
        "export": ("Fuel availability pressure", "Supply source continuity pressure"),
        "price": ("Fuel cost pressure", "Transportation budget pressure"),
        "prices": ("Fuel cost pressure", "Transportation budget pressure"),
        "cost": ("Fuel cost pressure", "Transportation budget pressure"),
        "costs": ("Fuel cost pressure", "Transportation budget pressure"),
    },
    ("fuel_energy", "Petrol"): {
        "price": ("Fuel cost pressure", "Transportation budget pressure"),
        "cost": ("Fuel cost pressure", "Transportation budget pressure"),
        "shortage": ("Fuel availability pressure", "Fuel supply continuity pressure"),
    },
    ("materials", "Semiconductors"): {
        "shortage": ("Component availability pressure", "Production continuity pressure"),
        "disruption": ("Supplier continuity pressure", "Production continuity pressure"),
        "lead time": ("Procurement lead-time pressure", "Production scheduling pressure"),
        "capacity": ("Component availability pressure", "Production scheduling pressure"),
        "export": ("Supply source continuity pressure", "Procurement lead-time pressure"),
    },
    ("logistics", "Ports"): {
        "congestion": ("Shipment delay risk", "Port congestion exposure"),
        "closure": ("Shipment delay risk", "Routing pressure"),
        "closed": ("Shipment delay risk", "Routing pressure"),
        "blockade": ("Shipment delay risk", "Routing pressure"),
        "disruption": ("Shipment delay risk", "Routing pressure"),
    },
    ("logistics", "Road"): {
        "closure": ("Route availability pressure", "Delivery delay risk"),
        "closed": ("Route availability pressure", "Delivery delay risk"),
        "strike": ("Route availability pressure", "Carrier availability pressure"),
        "disruption": ("Route availability pressure", "Delivery delay risk"),
    },
    ("logistics", "Rail"): {
        "strike": ("Rail service availability pressure", "Shipment timing pressure"),
        "disruption": ("Rail service availability pressure", "Shipment timing pressure"),
    },
    ("logistics", "Sea"): {
        "disruption": ("Shipping delay risk", "Freight availability pressure"),
        "rerouting": ("Route disruption risk", "Freight availability pressure"),
    },
    ("logistics", "Air"): {
        "flight": ("Air-freight availability pressure", "Shipment delay risk"),
        "disruption": ("Air-freight availability pressure", "Shipment delay risk"),
    },
}


def _normalize(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.casefold().split())


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return (value if value.tzinfo else value.replace(tzinfo=timezone.utc)).isoformat()


def _contains(text: str, phrase: str) -> bool:
    """Word-boundary match tolerating a simple plural 's' on the trigger."""
    if f" {phrase} " in f" {text} ":
        return True
    if not phrase.endswith("s") and f" {phrase}s " in f" {text} ":
        return True
    if phrase.endswith("s") and f" {phrase[:-1]} " in f" {text} ":
        return True
    return False


def _base_mapping(category: str, value: str) -> dict:
    """Fixed template for a dependency; geographic exposure uses its own areas."""
    if category == GEOGRAPHIC_CATEGORY:
        template = GEOGRAPHIC_MAPPING
    else:
        template = DEPENDENCY_MAPPINGS.get(value) or GENERIC_MAPPING
    return {
        "areas": list(template["areas"])[:MAX_AREAS],
        "impacts": list(template["impacts"])[:MAX_IMPACTS],
        "checks": list(template["checks"])[:MAX_CHECKS],
    }


    for trigger, values in table.items():
        if not _contains(event_text, trigger):
            continue
        for item in values:
            if item not in additions:
                additions.append(item)


def _refine_impacts(category: str, value: str, impacts: list[str], event_text: str) -> list[str]:
    """Prepend risk-specific impacts only when the event text actually supports them.

    This narrows the generic dependency template using words that are genuinely
    present in the stored event. It never asserts causation.
    """
    refined = list(impacts)
    table = REFINEMENTS.get((category, value))
    if not table:
        return refined
    additions: list[str] = []
    for trigger, values in table.items():
        if not _contains(event_text, trigger):
            continue
        for item in values:
            # Avoid repeating an impact that the base template already lists.
            if item not in additions and item not in refined:
                additions.append(item)
    return (additions + refined)[:MAX_IMPACTS]


def _mappings_from_relevance(result: dict, event_text: str) -> list[dict]:
    """Turn already-matched dependencies into bounded impact mappings."""
    direct_ids = {id(item) for item in (result.get("direct_matches") or [])}
    mappings: list[dict] = []
    # Dedupe by dependency value: a value such as Semiconductors configured
    # under both Materials and Technology is one supply-chain concern, not two.
    seen: set[str] = set()
    for match in result.get("matched_dependencies") or []:
        category = match.get("category") or ""
        value = match.get("value") or ""
        # "None" and "Other" are taxonomy placeholders, never dependencies.
        if not value or value in PLACEHOLDER_DEPENDENCIES:
            continue
        if value in seen:
            continue
        seen.add(value)
        template = _base_mapping(category, value)
        level = DIRECT if id(match) in direct_ids else INDIRECT
        mappings.append(
            {
                "dependency": value,
                "category": category,
                "relevance": level,
                "matched_terms": list(match.get("matched_terms") or [])[:MAX_CHECKS],
                "matched_on": match.get("matched_on"),
                "supply_chain_areas": template["areas"],
                "potential_impacts": _refine_impacts(category, value, template["impacts"], event_text),
                "verification_checks": template["checks"],
            }
        )
        if len(mappings) >= MAX_MAPPINGS:
            break
    return mappings

def _event_payload(event) -> dict:
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "category": event.category,
        "event_type": event.event_type,
        "location": event.location,
        "source": event.source,
    }

def _risk_payload(risk, prediction) -> dict:
    return {
        "id": risk.id,
        "severity": risk.severity,
        "risk_type": risk.risk_type or risk.risk_name,
        "risk_score": risk.risk_score,
        "status": risk.status,
        "created_at": _iso(risk.created_at),
        "prediction": (
            {
                "predicted_risk": prediction.predicted_risk,
                "predicted_severity": prediction.predicted_severity,
                "confidence_score": prediction.confidence_score,
            }
            if prediction
            else None
        ),
    }

def build_impact_map(db: Session, risk_id: int, *, user_id: int | None) -> dict:
    """Map a risk to potential supply-chain areas for the authenticated user.

    Dependency matching is delegated entirely to the existing company
    relevance engine. Read-only: no rows are created or updated.
    """
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if risk is None or risk.event is None:
        return {
            "risk_id": risk_id,
            "event_id": None,
            "company_available": False,
            "company_name": None,
            "industry": None,
            "risk": None,
            "event": None,
            "relevance": NONE,
            "relevance_reason": None,
            "summary": "Risk not found.",
            "mappings": [],
            "data_limitations": list(DATA_LIMITATIONS),
        }

    event = risk.event
    prediction = (
        db.query(Prediction)
        .filter(Prediction.risk_id == risk.id)
        .order_by(Prediction.created_at.desc(), Prediction.id.desc())
        .first()
    )
    event_payload = _event_payload(event)
    risk_payload = _risk_payload(risk, prediction)

    profile = get_company_profile(db, user_id) if user_id is not None else None
    if profile is None:
        return {
            "risk_id": risk.id,
            "event_id": event.id,
            "company_available": False,
            "company_name": None,
            "industry": None,
            "risk": risk_payload,
            "event": event_payload,
            "relevance": NONE,
            "relevance_reason": None,
            "summary": (
                "Company-specific context is not configured, so no company impact mapping "
                "was produced for this risk."
            ),
            "mappings": [],
            "data_limitations": list(DATA_LIMITATIONS),
        }

    result = evaluate_event_relevance(
        event_payload,
        _dependency_values(profile),
        {"risk_type": risk.risk_type, "risk_name": risk.risk_name},
    )
    relevance = result.get("relevance", NONE)
    event_text = _normalize(" ".join(
        part
        for part in (event.title, event.description, event.category)
        if isinstance(part, str)
    ))
    mappings = _mappings_from_relevance(result, event_text)

    if mappings:
        names = ", ".join(item["dependency"] for item in mappings)
        summary = (
            f"This risk is {relevance} to {profile.company_name}'s configured company "
            f"dependencies: {names}. The areas below are potential exposure areas based "
            f"on those configured dependencies."
        )
    else:
        summary = (
            "No company-specific impact mapping was identified for this risk based on the "
            "configured company dependencies."
        )

    return {
        "risk_id": risk.id,
        "event_id": event.id,
        "company_available": True,
        "company_name": profile.company_name,
        "industry": profile.industry,
        "risk": risk_payload,
        "event": event_payload,
        "relevance": relevance,
        "relevance_reason": result.get("reason"),
        "summary": summary,
        "mappings": mappings,
        "data_limitations": list(DATA_LIMITATIONS),
    }
