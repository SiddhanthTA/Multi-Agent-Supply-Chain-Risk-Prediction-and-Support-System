from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.review_content import presentation_risks, presentation_location

from app.crud.event import (
    create_event,
    get_event,
    get_events,
    update_event,
    delete_event,
)

from app.schemas.event import (
    EventCreate,
    EventUpdate,
    EventResponse,
)

from app.services.event_service import (
    store_news_events,
    store_weather_event,
)

router = APIRouter(
    prefix="/events",
    tags=["Events"]
)


# --------------------------------------------------
# CRUD ENDPOINTS
# --------------------------------------------------

@router.post("/", response_model=EventResponse)
def create_new_event(
    event: EventCreate,
    db: Session = Depends(get_db)
):
    return create_event(db, event)


@router.get("/", response_model=list[EventResponse])
def read_events(
    days: int | None = None,
    db: Session = Depends(get_db)
):
    return get_events(db, days=days)


@router.get("/review-set", response_model=list[EventResponse])
def read_review_events(
    location: str | None = None,
    db: Session = Depends(get_db),
):
    """Events belonging to the curated presentation review set."""
    selected = (location or "all").strip()

    def matches(value: str | None) -> bool:
        value = str(value or "").strip()
        if selected in ("", "all", "All Locations"):
            return True
        if selected == "Global":
            return value == "" or value.lower() == "unknown" or value not in {"India", "United States"}
        if selected == "India":
            return value == "India" or value.endswith(", India") or value.endswith(",India")
        if selected == "United States":
            return value == "United States" or value.endswith(", United States") or value.endswith(",United States")
        return value == selected

    events = []
    seen = set()
    for risk in presentation_risks(db):
        event = risk.event if risk else None
        location = presentation_location(risk)
        if event and event.id not in seen and matches(location):
            payload = EventResponse.model_validate(event).model_dump()
            payload['location'] = location
            events.append(EventResponse.model_validate(payload))
            seen.add(event.id)
    return events


# --------------------------------------------------
# LIVE DATA COLLECTION
# --------------------------------------------------

@router.post("/news/store")
def collect_news(
    db: Session = Depends(get_db)
):
    """
    Fetch, normalize and store live NewsAPI events.
    """
    return store_news_events(db)


@router.post("/weather/store")
def collect_weather(
    location: str = None,
    db: Session = Depends(get_db)
):
    """
    Fetch, normalize and store live WeatherAPI event.
    """
    result = store_weather_event(db, location=location)
    if isinstance(result, dict) and result.get("status") == "error":
        raise HTTPException(
            status_code=502,
            detail=result.get("message") or "Unable to fetch weather right now."
        )
    return result

@router.get("/{event_id}", response_model=EventResponse)
def read_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    event = get_event(db, event_id)

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    return event


@router.put("/{event_id}", response_model=EventResponse)
def update_existing_event(
    event_id: int,
    event: EventUpdate,
    db: Session = Depends(get_db),
):
    updated_event = update_event(db, event_id, event)

    if not updated_event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    return updated_event


@router.delete("/{event_id}")
def delete_existing_event(
    event_id: int,
    db: Session = Depends(get_db),
):
    deleted_event = delete_event(db, event_id)

    if not deleted_event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    return {
        "message": "Event deleted successfully"
    }


# --------------------------------------------------
