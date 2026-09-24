from app.services.location_detection import detect_locations, resolve_event_location, match_monitored_locations


class DummyLocation:
    def __init__(self, name, country=None):
        self.name = name
        self.country = country


def test_detect_dubai():
    text = "Dubai port operations were disrupted."
    detected = detect_locations(text)
    assert any(item["normalized"] == "Dubai, United Arab Emirates" for item in detected)


def test_detect_jebel_ali_port():
    text = "Jebel Ali Port faces shipping delays."
    detected = detect_locations(text)
    assert any(item["normalized"] == "Jebel Ali Port" for item in detected)


def test_detect_rotterdam():
    text = "Rotterdam Port reports congestion."
    detected = detect_locations(text)
    assert any(item["normalized"] == "Rotterdam, Netherlands" for item in detected)


def test_detect_singapore():
    text = "Singapore port congestion worsens."
    detected = detect_locations(text)
    assert any(item["normalized"] == "Singapore" for item in detected)


def test_detect_uae_country():
    text = "UAE introduces new shipping regulations."
    detected = detect_locations(text)
    assert any(item["normalized"] == "United Arab Emirates" for item in detected)


def test_detect_multiple_locations():
    text = "Dubai operations were affected by new UAE regulations."
    detected = detect_locations(text)
    labels = {item["normalized"] for item in detected}
    assert "Dubai, United Arab Emirates" in labels
    assert "United Arab Emirates" in labels


def test_detect_global_semiconductor_no_location():
    text = "Global semiconductor demand rises."
    detected = detect_locations(text)
    assert detected == []


def test_detect_california():
    text = "Apple expands operations in California."
    detected = detect_locations(text)
    assert any(item["normalized"] == "California" for item in detected)


def test_detect_europe_and_asia_regions():
    assert any(item["normalized"] == "Europe" for item in detect_locations("European ports experience congestion."))
    assert any(item["normalized"] == "Asia" for item in detect_locations("Shipping activity increases across Asia."))


def test_monitored_match_dubai():
    monitored = [DummyLocation("Dubai, United Arab Emirates", "United Arab Emirates")]
    result = resolve_event_location("Dubai port operations were disrupted.", monitored)
    assert result["primary_location"] == "Dubai, United Arab Emirates"
    assert result["monitored_location"] == "Dubai, United Arab Emirates"


def test_monitored_no_match_for_rotterdam():
    monitored = [DummyLocation("Dubai, United Arab Emirates", "United Arab Emirates")]
    result = resolve_event_location("Rotterdam Port reports congestion.", monitored)
    assert result["primary_location"] == "Rotterdam, Netherlands"
    assert result["monitored_location"] is None


def test_monitored_singapore_match_multi_location():
    monitored = [
        DummyLocation("Dubai, United Arab Emirates", "United Arab Emirates"),
        DummyLocation("Singapore", "Singapore"),
    ]
    result = resolve_event_location("Singapore port congestion worsens.", monitored)
    assert result["primary_location"] == "Singapore"
    assert result["monitored_location"] == "Singapore"


def test_monitored_global_no_match():
    monitored = [DummyLocation("Dubai, United Arab Emirates", "United Arab Emirates")]
    result = resolve_event_location("Global semiconductor demand rises.", monitored)
    assert result["primary_location"] == "Unknown"
    assert result["monitored_location"] is None


def test_monitored_multi_detected_locations():
    monitored = [
        DummyLocation("Dubai, United Arab Emirates", "United Arab Emirates"),
        DummyLocation("Singapore", "Singapore"),
    ]
    result = resolve_event_location("Dubai and Singapore ports report delays.", monitored)
    assert result["primary_location"] in {"Dubai, United Arab Emirates", "Singapore"}
    assert set(match_monitored_locations(result["detected_locations"], monitored)) == {"Dubai, United Arab Emirates", "Singapore"}


def test_detect_toronto_real_article():
    text = "Aecon announces new contracts in Toronto."
    detected = detect_locations(text)
    labels = {item["normalized"] for item in detected}
    assert "Toronto, Canada" in labels or "Toronto" in labels
    assert "Aecon" not in labels


def test_detect_kochi_real_article():
    text = "Indian Oil expands its Kochi operations in the southern Indian corridor."
    detected = detect_locations(text)
    labels = {item["normalized"] for item in detected}
    assert "Kochi, India" in labels or "Kochi" in labels
    assert "Indian Oil" not in labels


def test_detect_us_and_iran():
    text = "US-Iran tensions affect oil markets across the region."
    detected = detect_locations(text)
    labels = {item["normalized"] for item in detected}
    assert any(label in {"United States", "US"} for label in labels)
    assert "Iran" in labels
    assert "Oil" not in labels


def test_detect_pine_bluff_and_arkansas():
    text = "Hanwha Defense USA to locate a manufacturing campus at Pine Bluff Arsenal."
    detected = detect_locations(text)
    labels = {item["normalized"] for item in detected}
    assert "Pine Bluff Arsenal" in labels or "Pine Bluff" in labels or "Arkansas" in labels
    assert "Hanwha Defense USA" not in labels


def test_no_generic_record_as_location():
    text = "Record diesel prices raise fears of US fuel shortages."
    detected = detect_locations(text)
    labels = {item["normalized"] for item in detected}
    assert "Record" not in labels
    assert any(label in {"United States", "US"} for label in labels)


def test_detect_toronto_port_congestion():
    result = resolve_event_location("Toronto port congestion disrupts suppliers.", [])
    assert result["primary_location"] in {"Toronto", "Toronto, Canada"}
    assert result["monitored_location"] is None


def test_no_location_for_business_activity():
    result = detect_locations("Business activity increases across sectors.")
    assert result == []


def test_no_location_for_customers_shipping_costs():
    result = detect_locations("Customers face higher shipping costs.")
    assert result == []


def test_no_location_for_industry_demand():
    result = detect_locations("Industry demand remains strong.")
    assert result == []


def test_detect_us_officials():
    result = resolve_event_location("US officials announce new restrictions.", [])
    assert result["primary_location"] in {"United States", "US"}


def test_detect_us_sanctions():
    result = resolve_event_location("U.S. sanctions affect oil exports.", [])
    assert result["primary_location"] in {"United States", "US"}


def test_detect_united_states_imports():
    result = resolve_event_location("United States imports increase.", [])
    assert result["primary_location"] in {"United States", "US"}


def test_detect_russian_exports():
    result = resolve_event_location("Russian exports decline.", [])
    assert result["primary_location"] in {"Russia", "Russian"}


def test_detect_european_customers_delays():
    result = resolve_event_location("European customers face delays.", [])
    assert result["primary_location"] in {"Europe", "European"}
