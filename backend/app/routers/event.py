from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db

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
    db: Session = Depends(get_db)
):
    return get_events(db)


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