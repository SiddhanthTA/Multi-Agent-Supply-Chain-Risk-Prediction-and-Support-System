import re


COUNTRY_ALIASES = {
    "united arab emirates": ["uae"],
    "republic of singapore": ["singapore"],
    "singapore": ["singapore"],
}


def normalize_location_text(value: str) -> str:
    if not value:
        return ""

    text = value.lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"(?<=\w)'s\b", "", text)
    text = re.sub(r"[^a-z0-9\s,]", " ", text)
    text = text.replace(",", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _contains_phrase(text: str, phrase: str) -> bool:
    if not phrase:
        return False
    compact_phrase = normalize_location_text(phrase)
    if not compact_phrase:
        return False
    return re.search(rf"(?<![a-z0-9]){re.escape(compact_phrase)}(?![a-z0-9])", text) is not None


def _build_aliases(name: str, city: str, country: str):
    aliases = []
    seen = set()

    def add(value):
        if value and value.strip():
            norm = normalize_location_text(value)
            if norm and norm not in seen:
                seen.add(norm)
                aliases.append(value)

    add(name)
    add(city)
    add(country)

    if city and country and city.lower() != country.lower():
        add(f"{city}, {country}")
        add(f"{city} {country}")
        add(f"{city} in {country}")
        add(f"{country}'s {city}")
        add(f"{country} {city}")
        add(f"{city} in the {country}")
        add(f"{city} and {country}")

    if country:
        for alias in COUNTRY_ALIASES.get(country.lower(), []) + COUNTRY_ALIASES.get(city.lower(), []):
            if alias and alias.lower() != country.lower():
                add(alias)
                if city and city.lower() != country.lower():
                    add(f"{city} {alias}")
                    add(f"{city}, {alias}")
                    add(f"{city} in {alias}")

    return aliases


def infer_location_from_text(text: str, monitored_locations: list) -> str:
    """Determine the safest monitored location match for the article text."""
    if not text or not monitored_locations:
        return "Unknown"

    normalized_text = normalize_location_text(text)
    if not normalized_text:
        return "Unknown"

    scored_matches = []

    for location in monitored_locations:
        name = str(getattr(location, "name", "") or "").strip()
        if not name:
            continue

        city = name.split(",")[0].strip() if "," in name else name
        country = str(getattr(location, "country", "") or "").strip()

        best_score = 0
        best_label = None

        for alias in _build_aliases(name, city, country):
            normalized_alias = normalize_location_text(alias)
            if not normalized_alias:
                continue
            if not _contains_phrase(normalized_text, normalized_alias):
                continue

            if normalized_alias == normalize_location_text(name):
                score = 100
            elif normalized_alias == normalize_location_text(city):
                score = 90
            elif (
                normalized_alias == normalize_location_text(f"{city} {country}")
                or normalized_alias == normalize_location_text(f"{city}, {country}")
                or normalized_alias == normalize_location_text(f"{city} in {country}")
                or normalized_alias == normalize_location_text(f"{country}'s {city}")
                or normalized_alias == normalize_location_text(f"{country} {city}")
            ):
                score = 96
            elif normalized_alias == normalize_location_text(country):
                score = 0
            elif normalized_alias in {normalize_location_text(v) for v in COUNTRY_ALIASES.get(country.lower(), [])}:
                score = 0
            else:
                score = 75

            if score > best_score:
                best_score = score
                best_label = name

        if best_score > 0:
            scored_matches.append((best_score, len(name), name, best_label))

    if not scored_matches:
        return "Unknown"

    scored_matches.sort(key=lambda item: (-item[0], -item[1], item[2]))
    top_score, _, top_name, _ = scored_matches[0]

    if len(scored_matches) > 1:
        second_score = scored_matches[1][0]
        if top_score >= 90 and second_score >= 90:
            return "Unknown"

    if top_score < 75:
        return "Unknown"

    return top_name
