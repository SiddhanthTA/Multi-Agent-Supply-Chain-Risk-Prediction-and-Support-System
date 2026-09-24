from app.database.database import SessionLocal
from app.services.event_service import store_weather_event
from app.models.event import Event
from app.models.risk import Risk
from app.models.prediction import Prediction

def count_records(db, location):
    events = db.query(Event).filter(Event.location == location).count()
    
    # We need to join Risk with Event to filter by location
    risks = db.query(Risk).join(Event).filter(Event.location == location).count()
    predictions = db.query(Prediction).join(Risk).join(Event).filter(Event.location == location).count()
    
    return events, risks, predictions

db = SessionLocal()
try:
    location = "Dubai"
    
    # Pre-test cleanup (optional, but let's just count)
    print("Initial counts for", location)
    e1, r1, p1 = count_records(db, location)
    print(f"Events: {e1}, Risks: {r1}, Predictions: {p1}")
    
    # Click 1
    print("\n--- FIRST CLICK ---")
    res = store_weather_event(db, location=location)
    e2, r2, p2 = count_records(db, location)
    print(f"Events: {e2}, Risks: {r2}, Predictions: {p2}")
    event_loc = res["event"].location
    print(f"Stored location: '{event_loc}'")
    
    # Click 2
    print("\n--- SECOND CLICK ---")
    res2 = store_weather_event(db, location=location)
    e3, r3, p3 = count_records(db, location)
    print(f"Events: {e3}, Risks: {r3}, Predictions: {p3}")
    
    # Assertions
    assert e2 == e3, "Duplicate Event created!"
    assert r2 == r3, "Duplicate Risk created!"
    assert p2 == p3, "Duplicate Prediction created!"
    assert event_loc == location, "Location string modified!"
    print("\nSUCCESS: No duplicates created. Location consistent.")

except Exception as e:
    print(f"ERROR: {e}")
finally:
    db.close()
