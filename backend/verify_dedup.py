from app.database.database import SessionLocal
from app.models.event import Event
from app.models.risk import Risk
from app.models.prediction import Prediction
from app.services.event_service import store_weather_event
import json

db = SessionLocal()

print("Triggering weather 1...")
store_weather_event(db, "Dubai")
print("Triggering weather 2...")
store_weather_event(db, "Dubai")

print("Checking Events for Dubai...")
events = db.query(Event).filter(Event.location == "Dubai").all()
for e in events:
    print(f"Event ID: {e.id}, Type: {e.event_type}, Date: {e.event_time}")
    
    risks = db.query(Risk).filter(Risk.event_id == e.id).all()
    for r in risks:
        print(f"  Risk ID: {r.id}, Name: {r.risk_name}")
        preds = db.query(Prediction).filter(Prediction.risk_id == r.id).all()
        for p in preds:
            print(f"    Prediction ID: {p.id}, Status: {p.prediction_status}")

db.close()
