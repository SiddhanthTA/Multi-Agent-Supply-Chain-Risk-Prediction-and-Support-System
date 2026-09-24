import re

STRONG_EVENT_TERMS = (
    "disruption", "disruptions", "disrupted", "delay", "delays", "delayed",
    "congestion", "closure", "closed", "shutdown", "outage", "outages",
    "shortage", "shortages", "strike", "strikes", "blockade", "rerouting",
    "reroute", "attack", "attacks", "damaged", "destroyed", "fire", "flood",
    "cyclone", "earthquake", "storm", "sanction", "sanctions", "embargo",
    "restriction", "restrictions", "halt", "halted", "suspended", "suspension",
    "collision", "grounding", "blackout", "incident", "blockage", "stoppage",
)

DOMAIN_CONTEXT_TERMS = (
    "supply chain", "logistics", "shipping", "ship", "freight", "cargo", "vessel",
    "container", "port", "harbor", "terminal", "railway", "rail", "trucking",
    "truck", "road", "transport", "transportation", "factory", "manufacturing",
    "plant", "infrastructure", "pipeline", "refinery", "oil", "gas", "energy",
    "power", "supplier", "procurement", "semiconductor", "customs", "border",
    "trade", "export", "import", "shipment", "production", "shortage",
)

EXPLICIT_HIGH_SIGNAL_PHRASES = (
    "supply chain disruption",
    "port closure",
    "port congestion",
    "pipeline outage",
    "refinery outage",
    "energy infrastructure attack",
    "oil supply disruption",
    "gas supply disruption",
    "fuel supply disruption",
    "fuel supply problems",
    "energy supply emergency",
    "supply shock",
    "supply shocks",
    "supply squeeze",
    "trade route disruption",
    "factory shutdown",
    "customs closure",
    "border closure",
    "export restrictions",
    "import restrictions",
    "vessel attack",
    "vessel incident",
    "port attack",
    "missing shipments",
    "delayed shipments",
    "blocked shipments",
    "restricted shipments",
    "trade embargo",
)

ENERGY_CONTEXT_TERMS = ("energy", "oil", "gas", "pipeline", "refinery", "power")
TRADE_EVENT_TERMS = ("sanction", "sanctions", "embargo", "tariff", "restriction", "restrictions")
TRADE_CONTEXT_TERMS = (
    "trade", "export", "exports", "import", "imports", "shipment", "shipments",
    "supply", "route", "routes", "cargo", "energy", "oil", "gas",
    # Sanctioned sectors: aviation, fuel, shipping and technology.
    "aviation", "airline", "airlines", "aircraft", "airspace", "fuel", "diesel",
    "petrol", "gasoline", "shipping", "freight", "vessel", "tanker", "port",
    "commodity", "commodities", "technology", "semiconductor", "semiconductors",
)
WEATHER_CONTEXT_TERMS = ("weather", "flood", "cyclone", "earthquake", "storm", "hurricane")
OPERATIONAL_DOMAIN_TERMS = (
    "port", "harbor", "terminal", "vessel", "container", "pipeline", "refinery",
    "factory", "plant", "railway", "rail", "trucking", "truck", "customs", "border",
)

# --------------------------------------------------
# ADDITIONAL CONTEXT FAMILIES (shadow revision)
# Context alone never passes; every rule below still requires a signal term.
# --------------------------------------------------

AVIATION_CONTEXT_TERMS = (
    "aviation", "airline", "airlines", "airliner", "aircraft", "airport", "airports",
    "airspace", "air cargo", "air freight", "air traffic", "flight", "flights",
    "runway", "jet fuel", "aviation fuel",
)

FUEL_CONTEXT_TERMS = (
    "fuel", "fuels", "diesel", "petrol", "gasoline", "kerosene", "crude", "crude oil",
    "lng", "lpg", "opec", "oilfield", "oilfields", "barrel", "barrels",
    "refined products", "oil products", "energy security", "oil prices",
    "fuel prices", "energy prices",
)

LABOR_TRANSIT_CONTEXT_TERMS = (
    "labor", "labour", "worker", "workers", "workforce", "trade union",
    "trade unions", "labor union", "labour union", "union workers", "union members",
    "dockworkers", "dock workers", "longshoremen", "stevedores", "port workers",
    "rail workers", "transit workers", "truck drivers", "delivery drivers",
    "collective bargaining", "picket line", "walkout", "work stoppage",
    "transit", "commuter", "subway",
)

SEMICONDUCTOR_CONTEXT_TERMS = (
    "semiconductor", "semiconductors", "chip", "chips", "microchip", "microchips",
    "chipmaker", "chipmakers", "chipmaking", "chip making", "chip maker",
    "wafer", "wafers", "fab", "fabs", "foundry", "foundries", "lithography",
    "dram", "nand", "gddr", "gpu", "hbm", "high bandwidth memory",
    "memory chip", "memory chips", "silicon wafer",
)

# --------------------------------------------------
# SOFT SIGNALS
# These are weaker than STRONG_EVENT_TERMS and only pass when paired with a
# specific context family (never with a bare domain term).
# --------------------------------------------------

AVIATION_SIGNAL_TERMS = (
    "advisory", "advisories", "travel advisory", "travel advisories",
    "cancellation", "cancellations", "canceled", "cancelled", "closures",
    "no fly", "ground stop", "warning", "alert", "divert", "diverted",
)

ENERGY_SOFT_SIGNAL_TERMS = (
    "energy security", "fuel security", "oil security", "supply security",
    "energy crisis", "fuel crisis", "oil crisis", "diesel crisis",
    "market stability", "price stability", "supply stability", "record high",
    "supply shortfall", "fuel shortfall", "energy shortfall",
    "price spike", "price spikes", "price surge", "price surges",
    "supply squeeze", "supply tightness", "supply uncertainty",
    "shortfall", "shortfalls", "rationing", "rationed", "curtailment", "curtailed",
    "spike", "spikes", "surge", "surges", "volatility", "tightness",
    "squeeze", "bottleneck", "bottlenecks",
)

FUEL_FLOW_TERMS = (
    "import", "imports", "export", "exports", "shipment", "shipments",
    "supply", "supplies", "volume", "volumes", "flow", "flows",
    "stockpile", "stockpiles", "inventory", "inventories", "reserve", "reserves",
)

FLOW_CHANGE_TERMS = (
    "fall", "falls", "fell", "drop", "drops", "dropped", "decline", "declines",
    "declined", "decrease", "decreases", "rise", "rises", "rose", "increase",
    "increases", "jump", "jumps", "slump", "slumps", "cut", "cuts", "reduce",
    "reduced", "shortage", "shortages",
)

SEMICONDUCTOR_SIGNAL_TERMS = (
    "capacity", "outpace", "outpacing", "shortage", "shortages", "bottleneck",
    "bottlenecks", "tight", "tightness", "constraint", "constraints", "crunch",
    "undersupply", "supply", "supplies", "demand", "ramp", "expansion",
    "allocation", "lead time", "lead times",
)

# Generic business markers. Used only to suppress a soft-signal pass; they never
# grant a pass and never override a genuine strong event.
GENERIC_BUSINESS_MARKERS = (
    "announces", "announced", "announcement", "unveils", "unveiled", "launches",
    "launched", "named", "appoints", "appointed", "award", "awards", "awarded",
    "new product", "product line", "new order", "receives order", "named a leader",
    "investment", "invests", "invested", "dividend", "earnings", "revenue",
    "profit", "profits", "stock", "stocks", "shares", "shareholder",
    "buy rating", "price target", "insider", "partnership", "partners with",
    "signs deal", "contract award", "ipo", "quarterly", "ceo", "cfo",
    "vice president",
)

EXTENDED_CONTEXT_TERMS = (
    DOMAIN_CONTEXT_TERMS
    + AVIATION_CONTEXT_TERMS
    + FUEL_CONTEXT_TERMS
    + LABOR_TRANSIT_CONTEXT_TERMS
    + SEMICONDUCTOR_CONTEXT_TERMS
)


def _normalize_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _contains_term(text: str, term: str) -> bool:
    normalized_term = _normalize_text(term)
    if not normalized_term:
        return False
    return f" {normalized_term} " in f" {text} "


def _matches(text: str, terms: tuple[str, ...]) -> list[str]:
    return [term for term in terms if _contains_term(text, term)]


def _soft_signal_pass(text: str, energy_matches: list[str], aviation_matches: list[str]) -> dict | None:
    """Return the qualifying soft-signal decision, or ``None``.

    Soft signals are weaker evidence than ``STRONG_EVENT_TERMS``, so they only
    pass together with a specific context family and never with a bare domain term.
    """

    if energy_matches:
        energy_signals = _matches(text, ENERGY_SOFT_SIGNAL_TERMS)
        if energy_signals:
            return {
                "reason": "preserved_energy_signal",
                "matched_terms": energy_matches + energy_signals,
            }

        fuel_flow = _matches(text, FUEL_FLOW_TERMS)
        flow_change = _matches(text, FLOW_CHANGE_TERMS)
        if fuel_flow and flow_change:
            return {
                "reason": "preserved_fuel_flow",
                "matched_terms": energy_matches + fuel_flow + flow_change,
            }

    if aviation_matches:
        aviation_signals = _matches(text, AVIATION_SIGNAL_TERMS)
        if aviation_signals:
            return {
                "reason": "preserved_aviation_signal",
                "matched_terms": aviation_matches + aviation_signals,
            }

    chip_matches = _matches(text, SEMICONDUCTOR_CONTEXT_TERMS)
    if chip_matches:
        chip_signals = _matches(text, SEMICONDUCTOR_SIGNAL_TERMS)
        if chip_signals:
            return {
                "reason": "preserved_semiconductor_signal",
                "matched_terms": chip_matches + chip_signals,
            }

    return None


def classify_candidate(article: dict) -> dict:
    """Evaluate a normalized article without changing the production gate."""
    title = article.get("title", "") if isinstance(article, dict) else ""
    description = article.get("description", "") if isinstance(article, dict) else ""
    text = _normalize_text(f"{title} {description}")
    if not text:
        return {"passed": False, "reason": "no_relevant_terms", "matched_terms": []}

    event_matches = _matches(text, STRONG_EVENT_TERMS)
    domain_matches = _matches(text, EXTENDED_CONTEXT_TERMS)
    phrase_matches = _matches(text, EXPLICIT_HIGH_SIGNAL_PHRASES)

    if phrase_matches:
        return {"passed": True, "reason": "explicit_phrase", "matched_terms": phrase_matches}

    energy_matches = _matches(text, ENERGY_CONTEXT_TERMS + FUEL_CONTEXT_TERMS)
    if energy_matches and event_matches:
        return {
            "passed": True,
            "reason": "preserved_energy_event",
            "matched_terms": energy_matches + event_matches,
        }

    trade_events = [term for term in TRADE_EVENT_TERMS if _contains_term(text, term)]
    trade_context = [term for term in TRADE_CONTEXT_TERMS if _contains_term(text, term)]
    if trade_events and trade_context:
        return {
            "passed": True,
            "reason": "preserved_trade_event",
            "matched_terms": trade_events + trade_context,
        }

    weather_matches = _matches(text, WEATHER_CONTEXT_TERMS)
    if weather_matches and event_matches:
        return {
            "passed": True,
            "reason": "preserved_weather_event",
            "matched_terms": weather_matches + event_matches,
        }

    aviation_matches = _matches(text, AVIATION_CONTEXT_TERMS)
    if aviation_matches and event_matches:
        return {
            "passed": True,
            "reason": "preserved_aviation_event",
            "matched_terms": aviation_matches + event_matches,
        }

    labor_matches = _matches(text, LABOR_TRANSIT_CONTEXT_TERMS)
    if labor_matches and event_matches:
        return {
            "passed": True,
            "reason": "preserved_labor_disruption",
            "matched_terms": labor_matches + event_matches,
        }

    soft_signal = _soft_signal_pass(text, energy_matches, aviation_matches)
    if soft_signal is not None:
        business_markers = _matches(text, GENERIC_BUSINESS_MARKERS)
        if business_markers and not event_matches:
            # Soft evidence plus generic corporate wording is not a risk signal.
            return {
                "passed": False,
                "reason": "generic_business_announcement",
                "matched_terms": business_markers + soft_signal["matched_terms"],
            }
        return {
            "passed": True,
            "reason": soft_signal["reason"],
            "matched_terms": soft_signal["matched_terms"],
        }

    if domain_matches and event_matches and any(
        term in OPERATIONAL_DOMAIN_TERMS for term in domain_matches
    ):
        return {
            "passed": True,
            "reason": "domain_event",
            "matched_terms": domain_matches + event_matches,
        }

    if event_matches and domain_matches:
        return {
            "passed": True,
            "reason": "strong_event_context",
            "matched_terms": event_matches + domain_matches,
        }

    if domain_matches:
        return {"passed": False, "reason": "generic_domain_only", "matched_terms": domain_matches}
    if event_matches:
        return {"passed": False, "reason": "no_event_context", "matched_terms": event_matches}
    return {"passed": False, "reason": "no_relevant_terms", "matched_terms": []}
