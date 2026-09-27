"""Deterministic Agent 2 response-plan templates (DEMO / MOCK).

No model inference. Selects a prepared template using the real risk, event,
company profile and company relevance data already stored in SupplySentry so the
intended second-stage workflow can be demonstrated. Read-only; no DB writes.

Content describes options for human review only. It never ranks options and
never invents suppliers, contracts, volumes, inventory, fleet size or losses.
"""

from __future__ import annotations

import re

FUEL_TERMS = (
    "diesel", "petrol", "gasoline", "fuel", "crude", "oil price", "oil prices",
    "refinery", "petroleum", "barrel", "brent", "wti",
)
MATERIALS_TERMS = (
    "semiconductor", "semiconductors", "chip", "chips", "wafer", "wafers",
    "battery", "batteries", "lithium", "copper", "steel", "aluminum", "aluminium",
    "foundry", "rare earth", "resin", "plastic",
)
LOGISTICS_TERMS = (
    "port", "ports", "shipping", "shipment", "vessel", "container", "freight",
    "rail", "railway", "truck", "trucking", "warehouse", "customs", "strike",
    "congestion", "blockade", "rerouting", "sanction", "embargo",
)

DEMO_NOTE = (
    "Prepared response options based on the investigated risk and available company "
    "context. This is a deterministic demonstration template, not a model-generated "
    "conclusion, and it ranks no option above another."
)
NO_EXPOSURE_NOTE = (
    "SupplySentry holds configured dependencies, not quantitative business exposure. "
    "Supplier names, purchase terms, shipment volumes, inventory levels, fleet size, "
    "customer exposure and financial losses are not available and are not assumed "
    "anywhere in this plan."
)


def _has(text: str, terms) -> bool:
    """Word-boundary match so e.g. 'imports' does not match the term 'port'."""
    return any(re.search(rf"\b{re.escape(term)}\b", text) for term in terms)


def select_scenario(event: dict, risk: dict) -> str:
    """Pick a demo scenario from real stored data only."""
    text = " ".join(
        str(event.get(field) or "") for field in ("title", "description", "category")
    ).casefold()
    risk_text = f"{risk.get('risk_type') or ''} {risk.get('risk_name') or ''}".casefold()

    if _has(text, FUEL_TERMS):
        return "fuel_and_energy"
    if _has(text, MATERIALS_TERMS):
        return "materials_and_supply"
    if _has(text, LOGISTICS_TERMS):
        return "logistics_and_transport"
    if re.search(r"price|cost|tariff|inflation|market|financial|revenue", f"{text} {risk_text}"):
        return "financial_market"
    return "general"


def _company_clause(company: dict | None, relevance: dict | None, dependencies: list[str]) -> str:
    if not company:
        return (
            "Company-specific context is not configured for this account, so the options below "
            "focus on verification and monitoring rather than assuming company exposure."
        )
    name = company.get("company_name") or "this organization"
    if (relevance or {}).get("relevance") in {"direct", "indirect"} and dependencies:
        listed = ", ".join(dependencies)
        plural = "y" if len(dependencies) == 1 else "ies"
        return (
            f"For {name}, the configured {listed} dependenc{plural} make this signal relevant "
            f"for review. SupplySentry does not hold actual exposure values for these "
            f"dependencies, so the options below describe checks and options for human review "
            f"rather than quantified business impact."
        )
    return (
        f"No configured company dependency for {name} currently matches this event. The response "
        f"options below therefore focus on verification and monitoring rather than assuming "
        f"direct company exposure."
    )


# Standard option set reused by every scenario. The per-scenario text only
# supplies the subject wording; option names and structure are fixed so the demo
# always offers Monitor / Reduce / Escalate for human review.
OPTION_TEMPLATES = (
    {
        "name": "Option 1: Monitor and Verify",
        "what_to_check": [
            "Review the current status of {subject} in scope.",
            "Check which internal activities are exposed to this signal.",
        ],
        "why": (
            "Confirms whether the signal is actually relevant before committing analyst "
            "time or changing plans."
        ),
        "information_required": [
            "Current internal exposure related to {subject}",
            "Current status of the underlying event",
        ],
    },
    {
        "name": "Option 2: Reduce Near-Term Exposure",
        "what_to_check": [
            "Review near-term plans and commitments that are sensitive to {subject}.",
            "Assess whether timing, sourcing, routing, or pricing adjustments are feasible.",
        ],
        "why": (
            "May reduce exposure to a developing signal if the adjustments are "
            "operationally feasible."
        ),
        "information_required": [
            "Quantified internal exposure and timing",
            "Available options and their constraints",
        ],
    },
    {
        "name": "Option 3: Escalate for Review",
        "what_to_check": [
            "Review the escalation conditions listed in this plan.",
            "Consolidate verified internal data before escalating.",
        ],
        "why": (
            "Escalation is appropriate when verified internal data shows the signal "
            "affects a critical activity and options are constrained."
        ),
        "information_required": [
            "Verified internal impact data",
            "Documented constraints on available options",
        ],
    },
)

SCENARIO_CONTENT = {
    "fuel_and_energy": {
        "subject": "the affected fuel or energy conditions",
        "objective": (
            "Assess whether this fuel or energy-related development creates a material "
            "near-term impact on transportation costs, fuel availability, or delivery "
            "continuity."
        ),
        "immediate_checks": [
            "Review current fuel-dependent transportation activity in scope.",
            "Check current fuel procurement, pricing, and availability arrangements.",
            "Review upcoming activities that depend on the affected fuel type.",
            "Check whether alternative routing, carriers, or timing are available.",
        ],
        "information_required": [
            "Actual fuel consumption or usage",
            "Transportation or fleet exposure",
            "Carrier and fuel contract terms",
            "Upcoming shipment volume and timing",
            "Alternative transport availability",
            "Current fuel-cost exposure",
        ],
        "escalation_conditions": [
            "Internal data shows significant dependence on the affected fuel type.",
            "A supply constraint or restriction is confirmed by an authoritative source.",
            "The signal persists or intensifies across consecutive monitoring cycles.",
        ],
        "responsible_areas": ["Procurement", "Logistics", "Operations", "Finance"],
    },
    "materials_and_supply": {
        "subject": "the affected material or supply conditions",
        "objective": (
            "Assess whether this material or supply development creates a material "
            "near-term impact on sourcing continuity, production, or delivery schedules."
        ),
        "immediate_checks": [
            "Review current supply conditions for the affected material.",
            "Check which products or activities depend on the affected material.",
            "Review current inventory and replenishment position where available.",
            "Check whether alternative sourcing or substitutes are feasible.",
        ],
        "information_required": [
            "Material usage and criticality by product",
            "Supplier concentration and sourcing arrangements",
            "Contracted volumes and lead times",
            "Inventory levels and replenishment status",
            "Substitute or alternative material qualification",
        ],
        "escalation_conditions": [
            "The affected material is a confirmed critical input with limited alternatives.",
            "Supply interruption is confirmed by an authoritative source.",
            "Inventory or replenishment data shows insufficient cover for near-term plans.",
        ],
        "responsible_areas": ["Procurement", "Operations", "Risk / Compliance"],
    },



    "logistics_and_transport": {
        "subject": "the affected transport or routing conditions",
        "objective": (
            "Assess whether this logistics or transport development creates a material "
            "near-term impact on routing, capacity, or delivery continuity."
        ),
        "immediate_checks": [
            "Review current routing and capacity conditions on affected lanes.",
            "Check whether near-term movements are exposed to the disruption.",
            "Review alternative routes, modes, or carriers where feasible.",
            "Check current customs or border requirements where relevant.",
        ],
        "information_required": [
            "Lane-level shipment volume and timing",
            "Carrier and routing arrangements",
            "Available alternative capacity",
            "Customs or border processing requirements",
        ],
        "escalation_conditions": [
            "Affected lanes are confirmed business-critical and alternatives are limited.",
            "A closure, blockade, or capacity constraint is confirmed by an authoritative source.",
            "The disruption persists beyond the expected resolution window.",
        ],
        "responsible_areas": ["Logistics", "Operations", "Procurement"],
    },
    "financial_market": {
        "subject": "the market or cost movement",
        "objective": (
            "Assess whether this market or cost development creates a material near-term "
            "impact on cost, pricing, or financial planning."
        ),
        "immediate_checks": [
            "Review the current signal and its direction.",
            "Check which activities are financially sensitive to the movement.",
            "Review current committed spend or pricing arrangements where available.",
            "Check whether planning assumptions require review.",
        ],
        "information_required": [
            "Quantified cost or price exposure by activity",
            "Contracted volumes and prices",
            "Budget and planning assumptions",
            "Margin and cash-flow sensitivity",
        ],
        "escalation_conditions": [
            "Verified data shows material impact on committed spend or plan.",
            "The movement exceeds internal planning tolerances.",
            "The signal persists across consecutive monitoring cycles.",
        ],
        "responsible_areas": ["Finance", "Procurement", "Risk / Compliance"],
    },
    "general": {
        "subject": "this event",
        "objective": (
            "Establish whether this event is relevant to the organization and clarify its "
            "operational or commercial significance before deciding on further action."
        ),
        "immediate_checks": [
            "Review the current status of the event and the associated risk.",
            "Check which internal activities could be related to this signal.",
            "Confirm whether any configured company dependency is affected.",
        ],
        "information_required": [
            "Internal activity data related to the signal",
            "Current status of the underlying event",
            "Any dependency exposure data held internally",
        ],
        "escalation_conditions": [
            "Verified internal data shows the signal affects a critical activity.",
            "The event is confirmed by an authoritative source and is material to operations.",
            "The signal persists or intensifies across consecutive monitoring cycles.",
        ],
        "responsible_areas": ["Operations", "Risk / Compliance"],
    },
}



def build_response_plan(
    *,
    risk: dict,
    event: dict,
    company: dict | None,
    company_relevance: dict | None,
    platform_recommendation: dict | None,
) -> dict:
    """Build a deterministic demo response plan from real stored context."""
    scenario = select_scenario(event, risk)
    content = SCENARIO_CONTENT[scenario]
    # A value can legitimately be configured under more than one category (for
    # example Semiconductors under Materials and Technology). Keep the distinct
    # values for display, preserving first-seen order.
    dependencies = []
    for match in ((company_relevance or {}).get("matched_dependencies") or []):
        value = match.get("value")
        if value and value not in dependencies:
            dependencies.append(value)
    clause = _company_clause(company, company_relevance, dependencies)

    notes = [DEMO_NOTE, NO_EXPOSURE_NOTE, clause]
    if not company:
        notes.append(
            "No company profile is configured for this account, so this plan is intentionally "
            "generic and verification-oriented."
        )
    elif not dependencies:
        notes.append(
            "No configured company dependency matches this event, so no company-specific "
            "exposure is assumed in any option above."
        )

    options = [
        {
            "name": template["name"],
            "what_to_check": [
                item.format(subject=content["subject"])
                for item in template["what_to_check"]
            ],
            "why": template["why"],
            "information_required": [
                item.format(subject=content["subject"])
                for item in template["information_required"]
            ],
        }
        for template in OPTION_TEMPLATES
    ]

    return {
        "risk_id": risk.get("id"),
        "event_id": event.get("id"),
        "scenario": scenario,
        "generated_by": "deterministic-response-plan",
        "is_demo_template": True,
        "company_context_available": bool(company),
        "company_name": (company or {}).get("company_name"),
        "company_industry": (company or {}).get("industry"),
        "company_relevance": (company_relevance or {}).get("relevance"),
        "matched_dependencies": dependencies,
        "risk_summary": (
            f"{risk.get('risk_name') or 'Risk'} ({risk.get('risk_type') or 'Unclassified'}) "
            f"rated {risk.get('severity') or 'Unknown'} with a score of "
            f"{risk.get('risk_score')}, linked to event “{event.get('title') or 'an event'}” "
            f"in {event.get('location') or 'Unknown'}."
        ),
        "response_objective": content["objective"],
        "immediate_checks": list(content["immediate_checks"]),
        "response_options": options,
        "information_required": list(content["information_required"]),
        "escalation_conditions": list(content["escalation_conditions"]),
        "responsible_areas": list(content["responsible_areas"]),
        "platform_recommendation": platform_recommendation,
        "notes": notes,
        "decision_support_only": True,
    }
