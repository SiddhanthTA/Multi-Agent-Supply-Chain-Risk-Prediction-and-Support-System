from app.database.database import SessionLocal
from app.models.event import Event
from app.models.risk import Risk
from app.services.event_service import store_weather_event

db = SessionLocal()
print("Triggering weather...")
res = store_weather_event(db, "Dubai")
event = res["event"]
print(f"Returned event ID: {event.id}")

print(f"Querying risks for event {event.id}...")
risks = db.query(Risk).filter(Risk.event_id == event.id).all()
print(f"Found {len(risks)} risks.")
for r in risks:
    print(f"Risk ID: {r.id}, event_id: {r.event_id}")

db.close()
