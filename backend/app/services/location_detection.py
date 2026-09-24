import re
from typing import List, Dict, Any

# Broad local gazetteer for cities, countries, regions, and operational facilities.
# The detector is intentionally conservative: it keeps real geographies and rejects
# organizations, generic words, people, products, and company names.
LOCATIONS = {
    "toronto": "Toronto, Canada",
    "toronto canada": "Toronto, Canada",
    "pickering": "Pickering, Canada",
    "pickering nuclear generating station": "Pickering Nuclear Generating Station",
    "mumbai": "Mumbai, India",
    "bombay": "Mumbai, India",
    "chennai": "Chennai, India",
    "kochi": "Kochi, India",
    "kochi india": "Kochi, India",
    "delhi": "Delhi, India",
    "bangalore": "Bengaluru, India",
    "bengaluru": "Bengaluru, India",
    "hyderabad": "Hyderabad, India",
    "kolkata": "Kolkata, India",
    "pune": "Pune, India",
    "dubai": "Dubai, United Arab Emirates",
    "dubai united arab emirates": "Dubai, United Arab Emirates",
    "singapore": "Singapore",
    "rotterdam": "Rotterdam, Netherlands",
    "rotterdam port": "Rotterdam, Netherlands",
    "rotterdam netherlands": "Rotterdam, Netherlands",
    "london": "London, United Kingdom",
    "london united kingdom": "London, United Kingdom",
    "new york": "New York, United States",
    "new york city": "New York, United States",
    "california": "California",
    "san francisco": "San Francisco, United States",
    "los angeles": "Los Angeles, United States",
    "pine bluff": "Pine Bluff, United States",
    "pine bluff arsenal": "Pine Bluff Arsenal",
    "arkansas": "Arkansas, United States",
    "india": "India",
    "india and": "India",
    "united states": "United States",
    "united states of america": "United States",
    "usa": "United States",
    "us": "United States",
    "u s": "United States",
    "canada": "Canada",
    "united arab emirates": "United Arab Emirates",
    "uae": "United Arab Emirates",
    "germany": "Germany",
    "berlin": "Berlin, Germany",
    "frankfurt": "Frankfurt, Germany",
    "iran": "Iran",
    "europe": "Europe",
    "european": "Europe",
    "asia": "Asia",
    "asian": "Asia",
    "middle east": "Middle East",
    "middle-east": "Middle East",
    "jebel ali port": "Jebel Ali Port",
    "jebel ali": "Jebel Ali Port",
    "saudi arabia": "Saudi Arabia",
    "russia": "Russia",
    "russian": "Russia",
    "united kingdom": "United Kingdom",
    "uk": "United Kingdom",
    "european union": "European Union",
}

GENERIC_FALSE_POSITIVES = {
    "record", "stocks", "why", "oil", "market", "markets", "global", "shipping",
    "operations", "local", "company", "companies", "news", "business", "energy",
    "transport", "logistics", "supply", "chain", "demand", "trade", "investments",
    "the", "prnewswire", "globe", "newswire", "tsx", "new", "old", "monday",
    "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "sept",
    "oct", "nov", "dec", "jan", "feb", "mar", "apr", "jun", "jul", "aug",
    "ai", "gri", "ltl", "fla", "va", "edu", "idiq", "pba", "hdusa", "ev",
    "lfp", "wwii", "ic", "usaj", "gmp", "tampa", "arlington", "cranbury",
    "charter", "alliance", "group", "services", "products", "infrastructure",
    "capital", "fund", "funds", "board", "pipeline", "project", "projects",
    "technology", "innovation", "platform", "systems", "manufacturing"
}

ORG_LIKE_PATTERNS = (
    "inc", "corp", "llc", "ltd", "group", "holding", "holdings", "company",
    "companies", "industries", "services", "solutions", "partners", "bank",
    "defense", "energy", "oil", "air", "rail", "freight", "line", "lines",
    "logistics", "operations", "command", "university"
)


def _normalize_text(value: str) -> str:
    if not value:
        return ""
    text = value.lower().strip()
    text = text.replace("&", " and ")
    text = text.replace("-", " ")
    text = text.replace("/", " ")
    text = re.sub(r"(?<=\w)'s\b", "", text)
    text = re.sub(r"[^a-z0-9\s,]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_generic_false_positive(value: str) -> bool:
    if not value:
        return True
    normalized = _normalize_text(value)
    if not normalized:
        return True
    if normalized in GENERIC_FALSE_POSITIVES:
        return True
    tokens = normalized.split()
    if len(tokens) > 1 and any(token in GENERIC_FALSE_POSITIVES for token in tokens):
        return True
    if any(token in ORG_LIKE_PATTERNS for token in tokens):
        return True
    return False


def _phrase_found(text: str, phrase: str) -> bool:
    if not text or not phrase:
        return False
    normalized_text = _normalize_text(text)
    normalized_phrase = _normalize_text(phrase)
    if not normalized_phrase:
        return False
    pattern = re.escape(normalized_phrase).replace(r"\ ", r"\s+")
    return bool(re.search(rf"(?<![a-z0-9]){pattern}(?![a-z0-9])", normalized_text))


def _specificity_rank(value: str) -> int:
    v = (value or "").lower()
    if any(token in v for token in ["port", "station", "arsenal", "airport", "terminal", "harbor", "dock"]):
        return 40
    if any(token in v for token in ["city", "canada", "india", "united states", "germany", "united kingdom", "uae", "iran", "singapore"]):
        return 30
    if "," in value:
        return 25
    if " " in v:
        return 20
    return 10


def _candidate_aliases() -> List[tuple[str, str]]:
    items = []
    for alias, canonical in LOCATIONS.items():
        if not alias or not canonical:
            continue
        items.append((alias, canonical))
    return sorted(items, key=lambda item: (len(item[0]), len(item[1])), reverse=True)


def detect_locations(text: str) -> List[Dict[str, str]]:
    """Return geographic mentions discovered in a text string."""
    if not text:
        return []

    normalized_text = _normalize_text(text)
    if not normalized_text:
        return []

    matches: List[Dict[str, str]] = []
    seen = set()

    for alias, canonical in _candidate_aliases():
        normalized_alias = _normalize_text(alias)
        if not normalized_alias or _is_generic_false_positive(normalized_alias):
            continue
        if not _phrase_found(normalized_text, normalized_alias):
            continue

        # Hard guard: do not treat company or product names as locations.
        if canonical and _is_generic_false_positive(canonical):
            continue

        key = canonical.lower()
        if key in seen:
            continue
        seen.add(key)
        matches.append({
            "text": alias,
            "normalized": canonical,
        })

    # Keep only meaningful geographic entries in a deterministic order.
    matches.sort(key=lambda item: (-_specificity_rank(item["normalized"]), -len(item["normalized"]), item["normalized"]))
    return matches


def match_monitored_locations(detected_locations: List[Any], monitored_locations: List[Any]) -> List[str]:
    matches = []
    if not detected_locations or not monitored_locations:
        return matches

    monitored_names = []
    for loc in monitored_locations:
        name = getattr(loc, "name", None) or ''
        if name:
            monitored_names.append(name)

    for item in detected_locations:
        if isinstance(item, dict):
            normalized = item.get("normalized") or item.get("text") or ''
        else:
            normalized = str(item)

        for name in monitored_names:
            if not name:
                continue
            if name.lower() == normalized.lower():
                matches.append(name)
                continue
            city = name.split(',')[0].strip()
            if city.lower() == normalized.lower():
                matches.append(name)
                continue
            if normalized.lower() in {name.lower(), city.lower()}:
                matches.append(name)

    unique = []
    seen = set()
    for match in matches:
        if match not in seen:
            unique.append(match)
            seen.add(match)
    return unique


def resolve_event_location(text: str, monitored_locations: List[Any]) -> Dict[str, Any]:
    detected = detect_locations(text)
    if not detected:
        return {
            "detected_locations": [],
            "primary_location": "Unknown",
            "monitored_location": None,
            "normalized_locations": [],
        }

    normalized_locations = [item["normalized"] for item in detected]
    monitored_matches = match_monitored_locations(detected, monitored_locations)

    primary_location = normalized_locations[0]
    if monitored_matches:
        primary_location = monitored_matches[0]
    else:
        # Prefer specific city/facility over broad country or region.
        ordered = sorted(
            normalized_locations,
            key=lambda value: (-_specificity_rank(value), -len(value), value)
        )
        if ordered:
            primary_location = ordered[0]

    return {
        "detected_locations": [item["text"] for item in detected],
        "normalized_locations": normalized_locations,
        "primary_location": primary_location,
        "monitored_location": monitored_matches[0] if monitored_matches else None,
    }
