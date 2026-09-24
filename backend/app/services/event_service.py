from app.services.ai_pipeline import process_event, process_weather_event
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.schemas.event import EventCreate, EventResponse
from app.database.database import SessionLocal
from app.integrations.news_api import fetch_supply_chain_news
from app.integrations.currents_api import fetch_currents_news
from app.integrations.weather_api import fetch_weather_data
from app.crud.event import get_event_by_url, save_normalized_event
from app.services.ingestion_metrics import (
    base_stats,
    emit_summary,
    finish_stats,
    new_collection_id,
    start_timer,
)
from app.utils.logger import logger
from app.models.risk import Risk
from app.models.location import MonitoredLocation
from app.services.location_detection import resolve_event_location


def primary_intelligence_locations(monitored_locations):
    configured_countries = {
        item.strip()
        for item in settings.PRIMARY_INTELLIGENCE_COUNTRIES.split(",")
        if item.strip()
    }
    return [
        location
        for location in monitored_locations
        if str(getattr(location, "name", "") or "").strip() in configured_countries
    ]


def _normalize_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace('Z', '+00:00'))
        except ValueError:
            try:
                return datetime.strptime(text, '%Y-%m-%d %H:%M')
            except ValueError:
                return None
    return None


def _detect_event_category(title: str, description: str = "") -> str:
    text = f"{title or ''} {description or ''}".lower()
    if not text:
        return "General"

    if any(keyword in text for keyword in ["weather", "storm", "typhoon", "flood", "heat", "wind", "rain", "temperature", "hurricane"]):
        return "Weather"
    if any(keyword in text for keyword in ["oil", "gas", "pipeline", "energy", "power", "fuel", "refinery"]):
        return "Energy"
    if any(keyword in text for keyword in ["war", "sanction", "conflict", "geopolitical", "tariff", "trade restriction", "diplomatic", "iran", "ukraine", "china"]):
        return "Geopolitical"
    if any(keyword in text for keyword in ["inflation", "market", "price", "financial", "demand", "currency", "trade financing", "bank", "commodity"]):
        return "Financial"
    if any(keyword in text for keyword in ["port", "shipping", "logistics", "freight", "warehouse", "cargo", "container", "supply chain", "transport", "supply-chain"]):
        return "Logistics"
    if any(keyword in text for keyword in ["supplier", "procurement", "inventory", "manufacturing", "distribution", "shipment"]):
        return "Supply Chain"
    return "General"


# --------------------------------------------------
# NEWS NORMALIZATION
# --------------------------------------------------
def normalize_news_event(article: dict, location: str = "Unknown") -> EventCreate:
    published_at = _normalize_datetime(article.get("published_at"))
    received_at = datetime.now(timezone.utc)
    return EventCreate(
        title=article.get("title"),
        description=article.get("description"),
        event_type="News",
        location=location,
        source=article.get("source") or "NewsAPI",
        source_type="news",
        category=_detect_event_category(article.get("title") or "", article.get("description") or ""),
        published_at=published_at,
        received_at=received_at,
        url=article.get("url"),
        severity=settings.DEFAULT_EVENT_SEVERITY,
        status=settings.DEFAULT_EVENT_STATUS,
        event_time=published_at,
    )


# --------------------------------------------------
# WEATHER NORMALIZATION
# --------------------------------------------------
def normalize_weather_event(weather: dict) -> EventCreate:
    description_parts = [
        f"Temperature: {weather.get('temperature')}°C",
        f"Humidity: {weather.get('humidity')}%",
        f"Wind: {weather.get('wind_kph')} kph",
    ]
    if weather.get("precip_mm") is not None:
        description_parts.append(f"Precipitation: {weather.get('precip_mm')} mm")
    if weather.get("vis_km") is not None:
        description_parts.append(f"Visibility: {weather.get('vis_km')} km")

    event_time = _normalize_datetime(weather.get("last_updated"))
    received_at = datetime.now(timezone.utc)

    return EventCreate(
        title=weather.get("condition"),
        description=" | ".join(description_parts),
        event_type="Weather",
        location=weather.get("location"),
        source="WeatherAPI",
        source_type="weather",
        category="Weather",
        published_at=None,
        received_at=received_at,
        latitude=weather.get("lat"),
        longitude=weather.get("lon"),
        severity=settings.DEFAULT_EVENT_SEVERITY,
        status=settings.DEFAULT_EVENT_STATUS,
        event_time=event_time,
    )


# --------------------------------------------------
# STORE NEWS EVENTS
# --------------------------------------------------
def store_news_events(db: Session, collection_id: str | None = None):
    collection_id = collection_id or new_collection_id()
    started = start_timer()
    logger.info("Fetching latest news events...")

    news_api_articles = fetch_supply_chain_news(collection_id=collection_id)
    currents_articles = fetch_currents_news(collection_id=collection_id)

    persistence_stats = {}
    for provider, fetcher in (
        ("NewsAPI", fetch_supply_chain_news),
        ("Currents API", fetch_currents_news),
    ):
        provider_stats = getattr(fetcher, "last_stats", None)
        if isinstance(provider_stats, dict):
            persistence_stats[provider] = dict(provider_stats)
            persistence_stats[provider]["errors"] = list(provider_stats.get("errors", []))
        else:
            persistence_stats[provider] = base_stats(collection_id, provider, "ALL")

    articles = []
    source_errors = []

    if isinstance(news_api_articles, dict) and news_api_articles.get("status") == "error":
        source_errors.append(news_api_articles.get("message") or "NewsAPI request failed.")
    else:
        articles.extend(news_api_articles)

    if isinstance(currents_articles, dict) and currents_articles.get("status") == "error":
        source_errors.append(currents_articles.get("message") or "Currents API request failed.")
    else:
        articles.extend(currents_articles)

    if source_errors:
        logger.warning("One or more news sources failed during collection.")
    if not articles and source_errors:
        return {"status": "error", "message": "All news sources failed during collection."}

    logger.info(f"{len(articles)} news articles fetched.")

    # Load all monitored locations to use for text-based location inference
    all_monitored_locations = db.query(MonitoredLocation).all()
    monitored_locations = primary_intelligence_locations(all_monitored_locations)

    saved_events = []

    for article in articles:
        provider = "Currents API" if article.get("source") == "Currents API" else "NewsAPI"
        stats = persistence_stats[provider]
        # Build article text to search for location mentions
        article_text = (
            f"{article.get('title', '')} "
            f"{article.get('description', '')}"
        )

        location_result = resolve_event_location(article_text, monitored_locations)
        location = location_result.get("primary_location") or "Unknown"
        if location == "Unknown":
            stats["unknown_location"] += 1
        else:
            stats["location_detected"] += 1

        event = normalize_news_event(article, location=location)

        # Save Event (returns existing event if URL already seen)
        existing_event = get_event_by_url(db, event.url) if event.url else None
        saved_event = save_normalized_event(
            db,
            event.model_dump(),
        )

        if existing_event:
            stats["duplicate_existing_event"] += 1
            stats["events_skipped"] += 1
        else:
            stats["events_created"] += 1

        collection_query = article.get("collection_query")
        for query_stats in stats.get("query_metrics", []):
            if query_stats.get("query") == collection_query:
                if existing_event:
                    query_stats["events_skipped"] += 1
                else:
                    query_stats["events_created"] += 1
                break

        # Only run the AI pipeline if this event has not been processed yet.
        # This prevents the scheduler from creating duplicate Risk/Prediction
        # records when it re-encounters the same news article.
        existing_risk = db.query(Risk).filter(Risk.event_id == saved_event.id).first()
        if existing_risk is None:
            process_event(
                db=db,
                event=saved_event,
            )

        saved_events.append(saved_event)

    logger.info(f"{len(saved_events)} news events processed.")

    cycle_stats = base_stats(collection_id, "News ingestion", "ALL")
    cycle_stats["events_created"] = sum(item["events_created"] for item in persistence_stats.values())
    cycle_stats["events_skipped"] = sum(item["events_skipped"] for item in persistence_stats.values())
    cycle_stats["duplicate_existing_event"] = sum(item["duplicate_existing_event"] for item in persistence_stats.values())
    cycle_stats["location_detected"] = sum(item["location_detected"] for item in persistence_stats.values())
    cycle_stats["unknown_location"] = sum(item["unknown_location"] for item in persistence_stats.values())

    for stats in persistence_stats.values():
        emit_summary(logger, finish_stats(stats, started))
    emit_summary(logger, finish_stats(cycle_stats, started))

    return {
        "message": f"{len(saved_events)} news events processed successfully.",
        "events": saved_events,
    }

# --------------------------------------------------
# STORE WEATHER EVENT
# --------------------------------------------------
def store_weather_event(db: Session, location: str = None):
    logger.info(f"Fetching latest weather event for {location or 'default'}...")

    weather = fetch_weather_data(city=location)

    if isinstance(weather, dict) and weather.get("status") == "error":
        logger.error(f"Weather API Error: {weather.get('message')}")
        return weather

    event = normalize_weather_event(weather)

    # Save Event
    saved_event = save_normalized_event(
        db,
        event.model_dump(),
    )

    # Automatically run Weather Rule-Based Pipeline
    pipeline_result = process_weather_event(
        db=db,
        event=saved_event,
    )

    logger.info("Weather event processed successfully.")

    risk_obj = pipeline_result.get("risk") if isinstance(pipeline_result, dict) else None
    pred_obj = pipeline_result.get("prediction") if isinstance(pipeline_result, dict) else None

    return {
        "message": "Weather event processed successfully.",
        "event": EventResponse.model_validate(saved_event).model_dump(mode="json"),
        "risk": {
            "id": risk_obj.id,
            "risk_name": risk_obj.risk_name,
            "risk_score": risk_obj.risk_score,
            "severity": risk_obj.severity,
            "status": risk_obj.status,
        } if risk_obj else None,
        "prediction": {
            "predicted_risk": pred_obj.predicted_risk,
            "confidence_score": pred_obj.confidence_score,
            "predicted_severity": pred_obj.predicted_severity,
        } if pred_obj else None,
    }

# --------------------------------------------------
# SCHEDULER FUNCTION
# --------------------------------------------------
def collect_news_events():
    collection_id = new_collection_id()
    started = start_timer()
    logger.info("Scheduler triggered.")

    db = SessionLocal()

    try:
        store_news_events(db, collection_id=collection_id)
        logger.info("Scheduler completed successfully.")

    except Exception as e:
        logger.exception(f"Scheduler failed: {str(e)}")

    finally:
        cycle_stats = base_stats(collection_id, "News ingestion", "SCHEDULER")
        cycle_stats["errors"] = []
        emit_summary(logger, finish_stats(cycle_stats, started))
        db.close()