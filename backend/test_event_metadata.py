from datetime import datetime, timezone

from app.schemas.event import EventResponse
from app.services.event_service import normalize_news_event, normalize_weather_event


def test_news_metadata_population():
    article = {
        "title": "Singapore port congestion worsens amid shipping delays",
        "description": "Container traffic slowed after severe weather disrupted cargo operations.",
        "source": "Reuters",
        "published_at": "2026-09-22T14:30:00Z",
        "url": "https://example.com/article/1",
    }

    event = normalize_news_event(article)

    assert event.source == "Reuters"
    assert event.source_type == "news"
    assert event.category in {"Logistics", "Energy", "Geopolitical", "Financial", "Supply Chain", "Weather", "General"}
    assert event.published_at is not None
    assert event.received_at is not None
    assert event.event_time == event.published_at
    assert event.url == "https://example.com/article/1"


def test_weather_metadata_population():
    weather = {
        "location": "Singapore, Singapore",
        "temperature": 29.4,
        "humidity": 80,
        "wind_kph": 18,
        "precip_mm": 2.1,
        "vis_km": 8,
        "condition": "Heavy rain",
        "lat": 19.076,
        "lon": 72.8777,
        "last_updated": "2026-09-22 15:00",
    }

    event = normalize_weather_event(weather)

    assert event.source == "WeatherAPI"
    assert event.source_type == "weather"
    assert event.category == "Weather"
    assert event.published_at is None
    assert event.received_at is not None
    assert event.event_time is not None
    assert event.latitude == 19.076
    assert event.longitude == 72.8777


def test_event_response_includes_metadata_fields():
    dt = datetime(2026, 9, 22, 14, 30, tzinfo=timezone.utc)
    response = EventResponse(
        id=1,
        title="Test",
        description="Test description",
        event_type="News",
        location="Unknown",
        source="NewsAPI",
        source_type="news",
        category="Logistics",
        published_at=dt,
        received_at=dt,
        latitude=None,
        longitude=None,
        severity="Unknown",
        status="Active",
        event_time=dt,
        created_at=dt,
        updated_at=dt,
        url="https://example.com"
    )

    assert response.source_type == "news"
    assert response.category == "Logistics"
    assert response.published_at == dt
    assert response.received_at == dt
