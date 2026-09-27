"""Runtime response planning from the current risk, event, and company context.

No per-risk response text is stored in source code. The plan is assembled on each
request from the actual event title/description, risk assessment, matched company
dependencies, and the platform recommendation. It is decision support only.
"""

from __future__ import annotations

import re


def _normalize(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.casefold().split())


def _dependency_values(company_relevance: dict | None) -> list[str]:
    values: list[str] = []
    for match in (company_relevance or {}).get("matched_dependencies") or []:
        value = match.get("value")
        if value and value not in {"None", "Other"} and value not in values:
            values.append(value)
    return values


def _event_text(event: dict) -> str:
    return _normalize(" ".join(
        str(part)
        for part in (
            event.get("title"),
            event.get("description"),
            event.get("category"),
            event.get("event_type"),
        )
        if part
    ))


def _has(text: str, *terms: str) -> bool:
    return any(re.search(rf"\b{re.escape(term)}(?:s|ed|ing)?\b", text) for term in terms)


def select_scenario(event: dict, risk: dict) -> str:
    """Choose the response domain from the strongest signal in the event first."""
    text = _event_text(event)
    deps = {_normalize(value) for value in _dependency_values(risk.get("company_relevance"))}

    # Event-specific language wins over an unrelated configured dependency.
    # This keeps a port event from becoming a fuel plan merely because the
    # company also happens to depend on diesel.
    if _has(
        text, "semiconductor", "chip", "battery", "lithium", "copper", "steel", "aluminum"
    ):
        return "materials_and_supply"
    if _has(
        text, "port", "shipping", "shipment", "freight", "logistics", "route",
        "rail", "truck", "road", "vessel", "cargo", "blockade", "rerouting",
    ):
        return "logistics_and_transport"
    if _has(
        text, "diesel", "fuel", "electricity", "power", "coal", "gas", "energy"
    ):
        return "fuel_and_energy"
    if _has(text, "price", "prices", "cost", "tariff", "market", "revenue", "demand", "inflation"):
        return "financial_market"

    # If the event itself is sparse, use the company's matched dependency.
    if deps & {"semiconductors", "batteries", "lithium", "copper", "steel", "aluminum", "plastics"}:
        return "materials_and_supply"
    if deps & {"ports", "road", "rail", "sea", "air"}:
        return "logistics_and_transport"
    if deps & {"diesel", "petrol", "electricity", "coal", "natural gas"}:
        return "fuel_and_energy"
    return "general"


def _focus(deps: list[str], event: dict, risk: dict) -> str:
    if deps:
        return ", ".join(deps[:3])
    return (
        event.get("category")
        or risk.get("risk_type")
        or risk.get("risk_name")
        or "the monitored signal"
    )


def _event_signal(text: str) -> str:
    if _has(text, "shortage", "scarcity", "low stock", "dwindling"):
        return "availability pressure"
    if _has(text, "price", "prices", "cost", "expensive", "surge"):
        return "cost pressure"
    if _has(text, "ban", "restriction", "sanction", "tariff", "export", "embargo"):
        return "policy or trade pressure"
    if _has(text, "disruption", "closure", "blockade", "outage", "strike", "delay"):
        return "continuity pressure"
    if _has(text, "investment", "partnership", "expansion", "factory", "capacity", "production"):
        return "capacity or sourcing change"
    if _has(text, "demand", "sales", "growth", "decline"):
        return "demand-side change"
    return "external supply-chain signal"


def _company_clause(company: dict | None, relevance: dict | None, deps: list[str]) -> str:
    if not company:
        return "No company profile is configured, so internal exposure must be verified before action."
    if not deps:
        return (
            f"{company.get('company_name', 'The company')} has no identified configured dependency "
            "match for this event; the plan therefore avoids assuming company exposure."
        )
    return (
        f"{company.get('company_name', 'The company')} has configured exposure to "
        f"{', '.join(deps)}; the plan uses those dependencies as investigation targets, "
        "not as proof of an actual disruption."
    )


def _scenario_options(
    scenario: str,
    focus: str,
    signal: str,
    event_title: str,
) -> tuple[list[dict], list[str], list[str], list[str]]:
    """Build risk-domain-specific options instead of one universal 3-option template."""
    if scenario == "materials_and_supply":
        options = [
            {
                "name": f"Map {focus} supplier concentration",
                "why": f"Tests whether the {signal} described in “{event_title}” reaches a critical material or component source.",
                "what_to_check": [
                    f"Identify suppliers and components exposed to {focus}.",
                    "Check open orders, lead times and inventory cover for affected items.",
                ],
                "information_required": ["Supplier concentration", "Open purchase orders", "Inventory cover"],
            },
            {
                "name": f"Qualify an alternative for {focus}",
                "why": "Creates a continuity path if the affected input is critical and a technically acceptable alternative exists.",
                "what_to_check": [
                    f"Identify qualified or near-qualified alternatives for {focus}.",
                    "Check qualification lead time, capacity and commercial constraints.",
                ],
                "information_required": ["Alternative suppliers", "Qualification status", "Available capacity"],
            },
            {
                "name": f"Protect near-term {focus} supply",
                "why": "Focuses on immediate continuity where replenishment timing is more important than long-term sourcing changes.",
                "what_to_check": [
                    "Review critical production and delivery commitments.",
                    "Check whether existing inventory or purchase commitments can bridge the signal window.",
                ],
                "information_required": ["Critical production dates", "Inventory cover", "Supplier commitments"],
            },
        ]
        required = ["Supplier concentration", "Open purchase orders", "Inventory cover", "Alternative supplier capacity"]
        areas = ["Procurement", "Supplier Management", "Operations", "Engineering"]
        escalation = [
            f"Internal data confirms material exposure to {focus}.",
            "A critical input has insufficient cover and no qualified alternative.",
            "The external signal persists or intensifies across monitoring cycles.",
        ]
    elif scenario == "fuel_and_energy":
        options = [
            {
                "name": f"Measure {focus} cost sensitivity",
                "why": f"Separates the external {signal} from the company's actual transportation or energy cost exposure.",
                "what_to_check": [
                    f"Measure current fuel or energy usage linked to {focus}.",
                    "Compare current prices or surcharges with planning assumptions.",
                ],
                "information_required": ["Usage volumes", "Current price exposure", "Budget assumptions"],
            },
            {
                "name": f"Review sourcing and contract flexibility for {focus}",
                "why": "Identifies whether procurement terms can absorb a price or availability change without immediate disruption.",
                "what_to_check": [
                    "Review supplier, carrier and fuel-contract terms.",
                    "Check alternative suppliers, pricing mechanisms and replenishment options.",
                ],
                "information_required": ["Contract terms", "Supplier alternatives", "Fuel/energy availability"],
            },
            {
                "name": f"Adjust transport or operating plans around {focus}",
                "why": "Addresses near-term continuity if fuel or energy conditions begin affecting critical activities.",
                "what_to_check": [
                    "Identify fuel-sensitive shipments or operations.",
                    "Assess consolidation, timing, routing or mode alternatives where feasible.",
                ],
                "information_required": ["Critical shipments", "Transport modes", "Operational schedules"],
            },
        ]
        required = ["Usage volumes", "Contract terms", "Current price exposure", "Alternative supply or transport capacity"]
        areas = ["Procurement", "Logistics", "Operations", "Finance"]
        escalation = [
            f"Verified internal data shows material {focus} cost or availability exposure.",
            "A critical activity faces confirmed supply constraints with limited alternatives.",
            "Cost or continuity exposure exceeds internal planning tolerances.",
        ]
    elif scenario == "logistics_and_transport":
        options = [
            {
                "name": f"Map exposed {focus} lanes",
                "why": f"Determines whether the {signal} in “{event_title}” affects actual inbound or outbound movement.",
                "what_to_check": [
                    f"Identify shipments and suppliers using {focus}.",
                    "Compare affected lanes with delivery commitments and inventory cover.",
                ],
                "information_required": ["Lane volumes", "Shipment schedules", "Inventory cover"],
            },
            {
                "name": f"Prepare alternate routing for {focus}",
                "why": "Reduces dependency on a constrained route, carrier or node when a practical alternative exists.",
                "what_to_check": [
                    "Check alternative ports, carriers, routes or transport modes.",
                    "Compare capacity, transit time and incremental cost.",
                ],
                "information_required": ["Alternative capacity", "Transit times", "Freight quotes"],
            },
            {
                "name": f"Prioritize critical movements through {focus}",
                "why": "Protects business-critical deliveries when capacity is temporarily constrained.",
                "what_to_check": [
                    "Rank upcoming movements by production and customer impact.",
                    "Check expedited options only for shipments whose delay has material consequences.",
                ],
                "information_required": ["Critical delivery dates", "Customer commitments", "Expedite capacity"],
            },
        ]
        required = ["Lane-level shipment volume", "Carrier/routing arrangements", "Alternative capacity", "Delivery commitments"]
        areas = ["Logistics", "Operations", "Procurement", "Supply Planning"]
        escalation = [
            f"A business-critical lane is confirmed exposed to the {focus} disruption.",
            "Alternative routing or carrier capacity is insufficient.",
            "Transit-time or cost impact exceeds internal service thresholds.",
        ]
    elif scenario == "financial_market":
        options = [
            {
                "name": f"Trace {focus} cost transmission",
                "why": f"Tests how the {signal} in “{event_title}” reaches procurement, operating cost or pricing.",
                "what_to_check": [
                    f"Identify activities whose cost structure depends on {focus}.",
                    "Compare current exposure with budget and pricing assumptions.",
                ],
                "information_required": ["Cost exposure", "Contracted prices", "Budget assumptions"],
            },
            {
                "name": f"Review contract and pricing flexibility",
                "why": "Determines whether existing commercial terms can absorb or pass through the identified change.",
                "what_to_check": [
                    "Review price-adjustment, surcharge and renegotiation clauses.",
                    "Check committed volumes and upcoming renewal points.",
                ],
                "information_required": ["Contract clauses", "Committed volumes", "Renewal dates"],
            },
            {
                "name": f"Stress-test the near-term plan",
                "why": "Shows whether the event matters to cash flow, margin or delivery plans without assuming a loss has already occurred.",
                "what_to_check": [
                    "Run internal sensitivity cases using verified exposure data.",
                    "Identify thresholds that would require management review.",
                ],
                "information_required": ["Margin sensitivity", "Cash-flow sensitivity", "Planning thresholds"],
            },
        ]
        required = ["Quantified cost exposure", "Contracted volumes and prices", "Budget assumptions", "Margin sensitivity"]
        areas = ["Finance", "Procurement", "Operations", "Risk / Compliance"]
        escalation = [
            "Verified data shows material impact on committed spend, margin or plan.",
            "The movement exceeds internal financial planning tolerances.",
            "The signal persists and materially changes near-term assumptions.",
        ]
    else:
        options = [
            {
                "name": f"Validate exposure to {focus}",
                "why": f"Connects the specific event “{event_title}” to actual internal activity before action is considered.",
                "what_to_check": [
                    f"Map suppliers, operations, routes or services related to {focus}.",
                    "Check current commitments and dependency concentration.",
                ],
                "information_required": ["Internal exposure data", "Current commitments", "Dependency concentration"],
            },
            {
                "name": f"Prepare continuity options for {focus}",
                "why": f"Identifies practical alternatives if the {signal} becomes materially relevant.",
                "what_to_check": [
                    f"Identify substitute suppliers, routes, services or operating arrangements for {focus}.",
                    "Compare feasibility, lead time and constraints.",
                ],
                "information_required": ["Alternative capacity", "Lead times", "Operational constraints"],
            },
            {
                "name": f"Set review triggers for {focus}",
                "why": "Creates a clear evidence threshold for escalation instead of treating the external signal as a confirmed disruption.",
                "what_to_check": [
                    "Define the internal metrics that would confirm material exposure.",
                    "Track the event for persistence, escalation or reversal.",
                ],
                "information_required": ["Exposure thresholds", "Event status", "Internal monitoring metrics"],
            },
        ]
        required = ["Internal exposure data", "Current commitments", "Alternative capacity", "Monitoring thresholds"]
        areas = ["Operations", "Procurement", "Risk / Compliance"]
        escalation = [
            f"Internal evidence confirms material exposure to {focus}.",
            "The affected activity is business-critical and alternatives are constrained.",
            "The signal persists or intensifies across subsequent monitoring cycles.",
        ]

    return options, required, escalation, areas


def build_response_plan(
    *,
    risk: dict,
    event: dict,
    company: dict | None,
    company_relevance: dict | None,
    platform_recommendation: dict | None,
) -> dict:
    """Build a fresh response plan from the supplied risk/event context."""
    relevance = company_relevance or {}
    deps = _dependency_values(relevance)
    risk_context = dict(risk)
    risk_context["company_relevance"] = relevance

    scenario = select_scenario(event, risk_context)
    text = _event_text(event)
    focus = _focus(deps, event, risk)
    signal = _event_signal(text)
    title = event.get("title") or "the monitored event"
    options, required, escalation, areas = _scenario_options(
        scenario, focus, signal, title
    )

    company_name = (company or {}).get("company_name")
    industry = (company or {}).get("industry")
    notes = [
        _company_clause(company, relevance, deps),
        "This plan is generated at request time from the current stored event, risk assessment and company context.",
        "Options are decision support for human review; no business action is executed automatically.",
    ]
    if platform_recommendation:
        notes.append("The existing platform recommendation is shown separately and was not treated as an AI-generated response action.")

    risk_name = risk.get("risk_name") or risk.get("risk_type") or "Risk"
    severity = risk.get("severity") or "Unrated"
    score = risk.get("risk_score")
    score_text = f"{float(score):.2f}" if isinstance(score, (int, float)) else "not available"

    return {
        "risk_id": risk.get("id"),
        "event_id": event.get("id"),
        "scenario": scenario,
        "generated_by": "runtime-context-response-planner",
        "is_demo_template": False,
        "company_context_available": bool(company),
        "company_name": company_name,
        "company_industry": industry,
        "company_relevance": relevance.get("relevance"),
        "matched_dependencies": deps,
        "risk_summary": (
            f"“{title}” is linked to {risk_name}, rated {severity}, with a stored risk "
            f"score of {score_text}. The response plan focuses on {focus} and the observed "
            f"{signal} in the event."
        ),
        "response_objective": (
            f"Determine whether “{title}” creates a verified business exposure for "
            f"{company_name or 'the company'} and choose proportionate next steps for {focus}."
        ),
        "immediate_checks": [
            f"Confirm the current status and evidence behind “{title}”.",
            f"Verify internal exposure connected to {focus}.",
            f"Check whether the {signal} is already affecting commitments, capacity, cost or timing.",
        ],
        "response_options": options,
        "information_required": required,
        "escalation_conditions": escalation,
        "responsible_areas": areas,
        "platform_recommendation": platform_recommendation,
        "notes": notes,
        "decision_support_only": True,
    }
