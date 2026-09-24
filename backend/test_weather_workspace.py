from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.integrations.weather_api import fetch_weather_data
from app.models.event import Event
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.risk import Risk
from app.services.event_service import (
    primary_intelligence_locations,
    store_weather_event,
)


def weather_payload(
    location="Mumbai, India",
    country="India",
    lat=19.076,
    lon=72.8777,
    temperature=29.4,
):
    return {
        "location": location,
        "country": country,
        "lat": lat,
        "lon": lon,
        "temperature": temperature,
        "condition": "Heavy rain",
        "wind_kph": 22,
        "humidity": 90,
        "precip_mm": 18,
        "vis_km": 2,
        "last_updated": "2026-09-24T10:00:00Z",
    }


def test_weather_city_lookup_passes_city_name_to_weatherapi():
    response = MagicMock(status_code=200)
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "location": {
            "name": "Mumbai",
            "country": "India",
            "lat": 19.076,
            "lon": 72.8777,
        },
        "current": {
            "temp_c": 29.4,
            "condition": {"text": "Heavy rain"},
            "wind_kph": 22,
            "humidity": 90,
            "precip_mm": 18,
            "vis_km": 2,
            "last_updated": "2026-09-24 10:00",
        },
    }

    with patch("app.integrations.weather_api.requests.get", return_value=response) as request:
        weather = fetch_weather_data("Mumbai")

    assert request.call_args.kwargs["params"]["q"] == "Mumbai"
    assert weather["location"] == "Mumbai, India"
    assert weather["lat"] == 19.076


def test_news_location_monitoring_excludes_weather_cities():
    locations = [
        SimpleNamespace(name="India"),
        SimpleNamespace(name="United States"),
        SimpleNamespace(name="Mumbai"),
        SimpleNamespace(name="Chicago"),
        SimpleNamespace(name="Singapore"),
    ]

    assert primary_intelligence_locations(locations) == locations[:2]


def test_sequential_same_city_weather_refresh_is_idempotent_and_keeps_cities_separate():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    with patch(
        "app.services.event_service.fetch_weather_data",
        side_effect=[
            weather_payload(),
            weather_payload(temperature=30.0),
            weather_payload("Delhi, India", "India", 28.6139, 77.2090),
        ],
    ):
        first = store_weather_event(db, "Mumbai")
        refreshed = store_weather_event(db, "Mumbai")
        delhi = store_weather_event(db, "Delhi")

    assert first["event"]["id"] == refreshed["event"]["id"]
    assert first["risk"]["id"] == refreshed["risk"]["id"]
    assert "Temperature: 30.0°C" in refreshed["event"]["description"]
    assert db.query(Event).count() == 2
    assert db.query(Risk).count() == 2
    assert db.query(Prediction).count() == 2
    assert db.query(Recommendation).count() == 2
    assert delhi["event"]["id"] != refreshed["event"]["id"]
    assert {event.location for event in db.query(Event).all()} == {
        "Mumbai, India",
        "Delhi, India",
    }
    assert all(
        event.latitude is not None and event.longitude is not None
        for event in db.query(Event).all()
    )
    db.close()


def test_weather_city_failure_does_not_prevent_later_city_processing():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    with patch(
        "app.services.event_service.fetch_weather_data",
        side_effect=[
            {"status": "error", "message": "Weather unavailable"},
            weather_payload("Chicago, United States", "United States", 41.8781, -87.6298),
        ],
    ):
        failed = store_weather_event(db, "Mumbai")
        successful = store_weather_event(db, "Chicago")

    assert failed["status"] == "error"
    assert successful["event"]["location"] == "Chicago, United States"
    assert db.query(Event).count() == 1
    db.close()