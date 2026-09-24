from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database.database import get_db
from app.models.location import MonitoredLocation
from app.routers.auth import get_current_user
from app.models.user import User
from app.integrations.weather_api import search_locations

router = APIRouter(
    prefix="/locations",
    tags=["Locations"]
)

class LocationCreate(BaseModel):
    name: str
    country: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

class LocationResponse(BaseModel):
    id: int
    name: str
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    user_id: int

    class Config:
        orm_mode = True

class LocationSearchResult(BaseModel):
    name: str
    region: str
    country: str
    lat: float
    lon: float
    display: str


@router.get("/search", response_model=List[LocationSearchResult])
def location_search(
    q: str,
    current_user: User = Depends(get_current_user)
):
    """
    Search for locations using WeatherAPI autocomplete.
    Returns resolved city name, country, and coordinates.
    Frontend uses this to let the user pick a canonical location.
    """
    results = search_locations(q)
    return results


@router.post("/", response_model=LocationResponse)
def create_location(
    location: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if already exists by name for this user
    existing = db.query(MonitoredLocation).filter(
        MonitoredLocation.name == location.name,
        MonitoredLocation.user_id == current_user.id
    ).first()
    
    if existing:
        return existing
        
    db_location = MonitoredLocation(
        name=location.name,
        country=location.country,
        latitude=location.lat,
        longitude=location.lon,
        user_id=current_user.id
    )
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

@router.get("/", response_model=List[LocationResponse])
def get_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    locations = db.query(MonitoredLocation).filter(
        MonitoredLocation.user_id == current_user.id
    ).all()
    return locations

@router.delete("/{location_id}")
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    location = db.query(MonitoredLocation).filter(
        MonitoredLocation.id == location_id,
        MonitoredLocation.user_id == current_user.id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
        
    db.delete(location)
    db.commit()
    return {"message": "Location deleted"}
