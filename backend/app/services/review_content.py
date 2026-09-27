"""Presentation-specific selection of real stored risks for the dashboard."""

from datetime import datetime, timezone

from app.models.risk import Risk

# These sets are populated by presentation_risks() from the current stored data.
CURATED_US_RISK_IDS = set()
CURATED_INDIA_RISK_IDS = set()
CURATED_GLOBAL_RISK_IDS = set()
CURATED_REVIEW_RISK_IDS = set()

# ---------------------------------------------------------------------------
# Dynamic presentation curation
# ---------------------------------------------------------------------------
# The presentation workspace is selected from real stored Event/Risk rows.
# Nothing is inserted into the database merely to reach the presentation
# targets. The selector deliberately prefers supply-chain signals, but has a
# second, lower-threshold pass so a sparse score bucket does not collapse to
# only a handful of risks.

DYNAMIC_REVIEW_RISK_IDS = set()
_REVIEW_COUNTS = {"United States": 13, "India": 15, "Global": 22}

_REVIEW_DEPENDENCIES = {
    "Semiconductors": ("semiconductor", "semiconductors", "chip", "chips", "wafer", "foundry", "memory"),
    "Batteries": ("battery", "batteries", "cell", "cells", "cathode", "anode"),
    "Lithium": ("lithium",),
    "Diesel": ("diesel", "fuel", "refinery", "refined products"),
    "Electricity": ("electricity", "power grid", "grid", "power generation", "utility"),
    "Coal": ("coal",),
    "Ports": ("port", "ports", "shipping", "vessel", "container", "freight", "maritime"),
    "Road": ("road", "truck", "trucking", "highway"),
    "Rail": ("rail", "railway"),
    "Cloud Services": ("cloud", "data center", "data centre"),
    "Telecom": ("telecom", "network outage", "communications"),
    "North America": ("united states", "u.s.", "usa", "north america", "canada"),
}

_REVIEW_SUPPLY_TERMS = (
    "supply chain", "supplier", "sourcing", "shortage", "bottleneck", "capacity",
    "production", "manufacturing", "factory", "plant", "shipment", "shipping",
    "freight", "port", "rail", "truck", "logistics", "export", "import", "tariff",
    "sanction", "trade", "refinery", "fuel", "diesel", "oil", "crude", "gas",
    "electricity", "power", "coal", "semiconductor", "chip", "battery", "lithium",
    "nickel", "cobalt", "rare earth", "mineral", "weather", "flood", "storm",
    "hurricane", "earthquake", "drought", "cyberattack", "cyber", "outage",
    "congestion", "rerouting", "blockade", "embargo", "energy",
)

_REVIEW_NOISE_TERMS = (
    "cricket", "football", "soccer", "cycling", "marathon", "olympic", "asian games",
    "festival", "concert", "celebrity", "movie", "music", "garbage truck",
    "air defense", "missile interception", "sports", "tournament", "match",
    "fashion", "entertainment", "lottery", "horoscope",
)

# Location strings in the event stream are not guaranteed to use one format.
# These aliases keep common city/state forms from being incorrectly pushed
# into Global merely because the country was omitted.
_INDIA_LOCATION_ALIASES = {
    "india", "new delhi", "delhi", "mumbai", "bombay", "bengaluru", "bangalore",
    "chennai", "madras", "hyderabad", "pune", "ahmedabad", "kolkata", "calcutta",
    "kochi", "cochin", "coimbatore", "noida", "gurugram", "gurgaon", "jaipur",
    "lucknow", "kanpur", "surat", "nagpur", "indore", "bhubaneswar",
    "visakhapatnam", "thiruvananthapuram", "trivandrum", "vadodara", "mysuru",
    "mysore", "chandigarh", "goa",
}
_US_STATE_ALIASES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine",
    "maryland", "massachusetts", "michigan", "minnesota", "mississippi",
    "missouri", "montana", "nebraska", "nevada", "new hampshire", "new jersey",
    "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina",
    "south dakota", "tennessee", "texas", "utah", "vermont", "virginia",
    "washington", "west virginia", "wisconsin", "wyoming", "district of columbia",
}
_US_STATE_CODES = {
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi", "id",
    "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma", "mi", "mn", "ms",
    "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc", "nd", "oh", "ok",
    "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv",
    "wi", "wy", "dc",
}
_US_CITY_ALIASES = {
    "new york", "los angeles", "chicago", "houston", "phoenix", "philadelphia",
    "san antonio", "san diego", "dallas", "san jose", "austin", "jacksonville",
    "fort worth", "columbus", "charlotte", "san francisco", "indianapolis",
    "seattle", "denver", "washington", "boston", "nashville", "detroit",
    "portland", "las vegas", "memphis", "louisville", "baltimore", "milwaukee",
    "albuquerque", "tucson", "fresno", "sacramento", "atlanta", "kansas city",
    "miami", "raleigh", "omaha", "minneapolis", "cleveland", "tulsa",
    "new orleans", "tampa", "honolulu", "arlington", "pittsburgh", "st louis",
    "st. louis", "cincinnati", "orlando", "irvine", "silicon valley",
}

def _review_text(risk):
    event = risk.event
    return " ".join(
        str(getattr(event, field, "") or "")
        for field in ("title", "description", "category")
    ).casefold()

def _normalize_location_text(value):
    text = str(value or "").strip().casefold()
    for char in (",", "|", ";", "(", ")", "[", "]"):
        text = text.replace(char, " ")
    return " ".join(text.split())

def _review_location(risk):
    value = _normalize_location_text(risk.event.location if risk.event else "")
    if not value or value in {"unknown", "global", "world", "worldwide", "international"}:
        return "Global"

    tokens = set(value.replace("-", " ").split())
    if (
        "india" in tokens
        or value.endswith(" india")
        or any(alias == value or f"{alias} india" in value for alias in _INDIA_LOCATION_ALIASES)
    ):
        return "India"

    if (
        "united states" in value
        or value in {"us", "u.s.", "usa"}
        or "usa" in tokens
        or "u.s." in value
        or value.endswith(" us")
        or any(alias == value or f"{alias} " in value for alias in _US_STATE_ALIASES)
        or any(f" {code}" in f" {value} " for code in _US_STATE_CODES)
        or any(alias == value or alias in value for alias in _US_CITY_ALIASES)
    ):
        return "United States"

    return "Global"

def _review_dependency_matches(risk):
    text = _review_text(risk)
    matches = []
    for dependency, terms in _REVIEW_DEPENDENCIES.items():
        if any(term in text for term in terms):
            matches.append(dependency)
    return matches

def _review_candidate_score(risk):
    text = _review_text(risk)
    if not risk.event or not risk.event.title:
        return -10_000
    if risk.event.event_type == "Weather":
        return -10_000
    if any(term in text for term in _REVIEW_NOISE_TERMS):
        return -10_000

    score = 0
    dependencies = _review_dependency_matches(risk)
    score += min(len(dependencies), 4) * 22
    score += min(sum(text.count(term) for term in _REVIEW_SUPPLY_TERMS), 8) * 4

    severity = str(risk.severity or "").casefold()
    score += {"critical": 24, "high": 18, "medium": 10, "low": 4}.get(severity, 0)

    category = str(risk.event.category or "").casefold()
    if any(term in category for term in ("supply", "logistics", "energy", "technology", "trade")):
        score += 8

    created = risk.event.published_at or risk.event.event_time or risk.event.created_at
    if created:
        age_days = max(0, (datetime.now(timezone.utc) - (
            created.replace(tzinfo=timezone.utc) if created.tzinfo is None else created
        )).total_seconds() / 86400)
        if age_days <= 7:
            score += 12
        elif age_days <= 14:
            score += 6
        elif age_days > 45:
            score -= 12

    return score

def _dedupe_review_candidates(rows):
    seen = set()
    result = []
    for risk in rows:
        title = " ".join((risk.event.title or "").casefold().split())
        if title in seen:
            continue
        seen.add(title)
        result.append(risk)
    return result

def presentation_risks(db):
    """Return the balanced presentation set from real stored Risk/Event rows.

    Selection is exact up to the requested regional targets whenever enough
    eligible stored rows exist. The first pass prefers strong supply-chain
    signals; the second pass fills any regional shortfall from the remaining
    non-noise rows. This avoids the previous 5/4-result problem caused by an
    overly strict score threshold.
    """
    global DYNAMIC_REVIEW_RISK_IDS, CURATED_REVIEW_RISK_IDS
    all_rows = (
        db.query(Risk)
        .join(Risk.event)
        .filter(Risk.status != "Resolved")
        .order_by(Risk.created_at.desc())
        .limit(5000)
        .all()
    )

    buckets = {"United States": [], "India": [], "Global": []}
    for risk in _dedupe_review_candidates(all_rows):
        if not risk.event or not risk.event.title:
            continue
        if risk.event.event_type == "Weather":
            continue
        score = _review_candidate_score(risk)
        if score <= -10_000:
            continue
        buckets[_review_location(risk)].append((score, risk))

    selected = []
    selected_ids = set()

    for location, target in _REVIEW_COUNTS.items():
        ranked = sorted(
            buckets[location],
            key=lambda item: (
                item[0],
                float(item[1].risk_score or 0),
                item[1].created_at or datetime.min,
            ),
            reverse=True,
        )
        # Strong pass: only signals that meet the normal quality bar.
        chosen = [risk for score, risk in ranked if score >= 18][:target]
        # Fill pass: if the bucket is sparse, use the strongest remaining
        # non-noise stored signals in that same location instead of stealing
        # rows from another location.
        if len(chosen) < target:
            chosen_ids = {risk.id for risk in chosen}
            chosen.extend(
                risk for _, risk in ranked
                if risk.id not in chosen_ids
            )
            chosen = chosen[:target]

        selected.extend(chosen)
        selected_ids.update(risk.id for risk in chosen)

    DYNAMIC_REVIEW_RISK_IDS = selected_ids
    CURATED_REVIEW_RISK_IDS = set(selected_ids)
    CURATED_US_RISK_IDS = {
        risk.id for risk in selected if _review_location(risk) == "United States"
    }
    CURATED_INDIA_RISK_IDS = {
        risk.id for risk in selected if _review_location(risk) == "India"
    }
    CURATED_GLOBAL_RISK_IDS = {
        risk.id for risk in selected if _review_location(risk) == "Global"
    }
    return selected

def presentation_location(risk):
    if risk.id in DYNAMIC_REVIEW_RISK_IDS:
        return _review_location(risk)
    return risk.event.location if risk.event else None

def is_review_risk(risk_id: int) -> bool:
    return int(risk_id) in DYNAMIC_REVIEW_RISK_IDS

def curated_review_risk_ids():
    return DYNAMIC_REVIEW_RISK_IDS

def _generic_review_subject(risk, event):
    deps = _review_dependency_matches(risk)
    if deps:
        return ", ".join(deps[:3])
    if event.category:
        return str(event.category)
    return str(risk.risk_type or risk.risk_name or "the monitored supply-chain signal")

def _generic_review_sections(risk, event, company_name, industry):
    subject = _generic_review_subject(risk, event)
    deps = _review_dependency_matches(risk)
    dep_text = ", ".join(deps) if deps else subject
    title = event.title or "Stored event signal"
    summary = (
        f"{title} is a {risk.severity or 'unrated'} {risk.risk_type or risk.risk_name or 'supply-chain'} "
        f"signal in {presentation_location(risk) or event.location or 'the monitored network'}. "
        f"The strongest configured company-relevant areas are {dep_text}. "
        f"The stored event does not by itself establish a loss or disruption at {company_name}."
    )
    why = (
        f"For {company_name}, the relevant review question is whether the external signal changes "
        f"availability, cost, lead time, routing, supplier capacity or demand for {dep_text}. "
        f"SupplySentry does not store supplier contracts, purchase volumes, inventory cover, shipment "
        f"volumes or customer commitments, so exposure must be verified internally."
    )
    next_steps = [
        f"Map current {dep_text} suppliers, routes or operating dependencies against the event.",
        f"Check open orders, inventory cover and committed production or delivery dates exposed to {dep_text}.",
        "Track the source event for persistence, escalation or reversal before changing supply-chain plans.",
    ]
    sections = {
        "investigation_summary": [_statement(summary, "E1", title, "fact")],
        "why_this_matters": [
            _statement(why, "E1", title),
            _statement(
                f"{company_name}'s quantitative exposure remains unknown because internal contracts, volumes and inventory data are not stored.",
                "E3",
                f"{company_name} / {industry}",
            ),
        ],
        "supporting_evidence": [
            _statement(
                f"Stored assessment: {risk.severity or 'Unrated'} severity, {risk.risk_type or risk.risk_name or 'Unspecified'} risk type, risk score {float(risk.risk_score or 0):.2f}.",
                "E2",
                f"{risk.severity} / {risk.risk_type or risk.risk_name}",
            ),
            _statement(
                f"Stored event location: {event.location or 'not specified'}; source: {event.source or 'not specified'}.",
                "E1",
                title,
            ),
        ],
        "related_intelligence": [],
        "what_to_investigate_next": [_statement(item, "E1", title) for item in next_steps],
    }
    return sections, deps, subject




