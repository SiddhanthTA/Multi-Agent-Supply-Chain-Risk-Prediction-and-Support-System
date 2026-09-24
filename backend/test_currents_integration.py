from unittest.mock import MagicMock, patch

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.crud.event import save_normalized_event
from app.integrations.currents_api import fetch_currents_news
from app.models.event import Event
from app.schemas.event import EventCreate
from app.services.event_service import normalize_news_event, store_news_events


def currents_response(payload, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_currents_success_normalizes_articles_and_uses_bounded_queries():
    payload = {
        "news": [{
            "id": "article-1",
            "title": "Port shipping disruption affects supply chain",
            "description": "Freight delays are reported.",
            "url": "https://example.com/currents-1",
            "published": "2026-09-23T08:00:00Z",
        }]
    }

    with patch("app.integrations.currents_api.settings.CURRENTS_API_KEY", "configured"), \
         patch("app.integrations.currents_api.relevance_filter.evaluate", return_value={"accepted": True}), \
         patch("app.integrations.currents_api.requests.get", side_effect=[currents_response(payload)] * 4) as request:
        articles = fetch_currents_news()

    assert len(articles) == 1
    assert articles[0] == {
        "title": "Port shipping disruption affects supply chain",
        "description": "Freight delays are reported.",
        "source": "Currents API",
        "published_at": "2026-09-23T08:00:00Z",
        "url": "https://example.com/currents-1",
    }
    assert request.call_count == 4
    assert request.call_args.kwargs["headers"] == {"Authorization": "configured"}
    assert request.call_args.kwargs["params"]["language"] == "en"


def test_currents_optional_fields_are_safe():
    payload = {"news": [{"title": "Shipping update", "description": None}]}

    with patch("app.integrations.currents_api.settings.CURRENTS_API_KEY", "configured"), \
         patch("app.integrations.currents_api.relevance_filter.evaluate", return_value={"accepted": True}), \
         patch("app.integrations.currents_api.requests.get", return_value=currents_response(payload)):
        articles = fetch_currents_news()

    assert articles == []


def test_currents_failure_returns_safe_error_without_secret():
    with patch("app.integrations.currents_api.settings.CURRENTS_API_KEY", "configured"), \
            patch("app.integrations.currents_api.requests.get", side_effect=requests.exceptions.Timeout("network unavailable")):
        result = fetch_currents_news()

    assert result["status"] == "error"
    assert "network unavailable" not in result["message"]
    assert "configured" not in result["message"]


def test_duplicate_url_returns_existing_event():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    event_data = EventCreate(
        title="Port disruption",
        description="Freight delays affect a terminal.",
        event_type="News",
        location="Unknown",
        source="Currents API",
        source_type="news",
        category="Logistics",
        url="https://example.com/shared-story",
    ).model_dump()

    first = save_normalized_event(session, event_data)
    second = save_normalized_event(session, {**event_data, "title": "Same story from NewsAPI", "source": "NewsAPI"})

    assert first.id == second.id
    assert session.query(Event).count() == 1
    session.close()


def test_currents_article_enters_existing_event_pipeline():
    article = {
        "title": "Dubai port shipping disruption",
        "description": "Freight operations are delayed.",
        "source": "Currents API",
        "published_at": "2026-09-23T08:00:00Z",
        "url": "https://example.com/pipeline-story",
    }
    saved_event = MagicMock(id=42)
    db = MagicMock()
    db.query.return_value.all.return_value = []
    db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.services.event_service.fetch_supply_chain_news", return_value=[]), \
         patch("app.services.event_service.fetch_currents_news", return_value=[article]), \
         patch("app.services.event_service.resolve_event_location", return_value={"primary_location": "Dubai"}), \
         patch("app.services.event_service.save_normalized_event", return_value=saved_event) as save_event, \
         patch("app.services.event_service.process_event") as process_event:
        result = store_news_events(db)

    assert result["events"] == [saved_event]
    save_event.assert_called_once()
    process_event.assert_called_once_with(db=db, event=saved_event)


def test_existing_news_normalization_remains_compatible():
    event = normalize_news_event({
        "title": "Singapore shipping delay",
        "description": "A freight delay affects a port.",
        "source": "NewsAPI",
        "published_at": "2026-09-23T08:00:00Z",
        "url": "https://example.com/newsapi-story",
    }, location="Singapore")

    assert event.source == "NewsAPI"
    assert event.location == "Singapore"
    assert event.source_type == "news"
