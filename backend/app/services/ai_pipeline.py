from sqlalchemy.orm import Session

from app.ai.inference import predict_event

from app.models.event import Event
from app.models.risk import Risk
from app.models.prediction import Prediction

from app.services.recommendation_service import save_generated_recommendation
import time

NORMAL_WEATHER_KEYWORDS = [
    "clear", "sunny", "partly cloudy", "cloudy", "overcast"
]
SEVERE_WEATHER_KEYWORDS = [
    "storm", "thunderstorm", "heavy rain", "downpour",
    "flood", "flash flood", "hail", "snow", "rainstorm",
]
MODERATE_WEATHER_KEYWORDS = [
    "rain", "drizzle", "shower", "mist", "fog", "gust",
]
EXTREME_WEATHER_KEYWORDS = [
    "hurricane", "cyclone", "typhoon", "tornado", "earthquake",
    "flash flood", "blizzard", "extreme storm", "severe thunderstorm",
]


def _parse_weather_metrics(event_description: str):
    import re

    desc = (event_description or "").lower()
    temp_c = None
    humidity = None
    wind_kph = None
    precip_mm = None
    vis_km = None

    temp_match = re.search(r"temperature\s*:\s*(-?\d+(?:\.\d+)?)", desc, re.I)
    if temp_match:
        temp_c = float(temp_match.group(1))

    humidity_match = re.search(r"humidity\s*:\s*(\d+(?:\.\d+)?)", desc, re.I)
    if humidity_match:
        humidity = float(humidity_match.group(1))

    wind_match = re.search(r"wind\s*:\s*(\d+(?:\.\d+)?)\s*(?:kph|km/h|kmh)?", desc, re.I)
    if wind_match:
        wind_kph = float(wind_match.group(1))

    precip_match = re.search(r"precipitation\s*:\s*(\d+(?:\.\d+)?)\s*mm", desc, re.I)
    if precip_match:
        precip_mm = float(precip_match.group(1))

    vis_match = re.search(r"visibility\s*:\s*(\d+(?:\.\d+)?)\s*km", desc, re.I)
    if vis_match:
        vis_km = float(vis_match.group(1))

    return temp_c, humidity, wind_kph, precip_mm, vis_km


def classify_weather_conditions(title: str, description: str, temp_c=None, humidity=None, wind_kph=None, precip_mm=None, vis_km=None):
    condition_text = f"{(title or '').lower()} {(description or '').lower()}"

    if any(keyword in condition_text for keyword in EXTREME_WEATHER_KEYWORDS):
        return "Natural Disaster", "Critical", 1.0, True

    if any(keyword in condition_text for keyword in SEVERE_WEATHER_KEYWORDS) or (
        precip_mm is not None and precip_mm >= 15
    ) or (
        vis_km is not None and vis_km <= 3
    ):
        return "Severe Weather", "High", 0.85, True

    if (wind_kph is not None and wind_kph >= 45) or (
        temp_c is not None and temp_c >= 45
    ) or (
        humidity is not None and humidity >= 95 and temp_c is not None and temp_c >= 32
    ):
        return "Severe Weather", "High", 0.75, True

    if any(keyword in condition_text for keyword in NORMAL_WEATHER_KEYWORDS):
        has_hazard_signal = (
            any(keyword in condition_text for keyword in MODERATE_WEATHER_KEYWORDS)
            or (wind_kph is not None and wind_kph >= 25)
            or (humidity is not None and humidity >= 90 and temp_c is not None and temp_c >= 30)
            or (precip_mm is not None and precip_mm >= 2)
        )
        if not has_hazard_signal:
            return "Normal Conditions", "Low", 0.0, False

    if any(keyword in condition_text for keyword in MODERATE_WEATHER_KEYWORDS) or (
        wind_kph is not None and wind_kph >= 25
    ) or (
        humidity is not None and humidity >= 90 and temp_c is not None and temp_c >= 30
    ) or (
        precip_mm is not None and precip_mm >= 2
    ):
        return "Weather Delay", "Medium", 0.45, True

    return "Normal Conditions", "Low", 0.0, False


def cleanup_stale_normal_weather_risks(db: Session):
    """
    Safe one-time cleanup for stale weather records created by the earlier
    broken 80% / 0.8 normal-weather logic.
    """
    updated = 0
    weather_events = db.query(Event).filter(Event.event_type == "Weather").all()

    for event in weather_events:
        title = (event.title or "").lower()
        description = (event.description or "").lower()
        condition_text = f"{title} {description}"

        if not any(keyword in condition_text for keyword in NORMAL_WEATHER_KEYWORDS):
            continue

        risk = db.query(Risk).filter(Risk.event_id == event.id).first()
        if not risk:
            continue

        if risk.status != "Active" and risk.risk_score in (None, 0.0) and risk.probability in (None, 0.0):
            continue

        risk.risk_name = "Weather Delay"
        risk.risk_type = "Weather Delay"
        risk.risk_score = 0.0
        risk.severity = "Low"
        risk.probability = 0.0
        risk.status = "Inactive"

        prediction = db.query(Prediction).filter(Prediction.risk_id == risk.id).first()
        if prediction:
            prediction.predicted_risk = "Weather Delay"
            prediction.confidence_score = 0.0
            prediction.predicted_severity = "Low"
            prediction.prediction_status = "Low Confidence"

        updated += 1

    db.commit()
    return updated


def process_event(
    db: Session,
    event: Event,
):
    """
    Process an event using the AI pipeline.

    Flow:

    Event
        ↓
    DistilBERT
        ↓
    XGBoost
        ↓
    Risk
        ↓
    Prediction
        ↓
    Recommendation
    """

    try:
        pipeline_start = time.perf_counter()
        # -----------------------------------------
        # Validate Event
        # -----------------------------------------
        if not event.description or not event.description.strip():
            raise ValueError("Event description is empty.")

        inference_start = time.perf_counter()
        # -----------------------------------------
        # Run AI Prediction
        # -----------------------------------------
        ai_result = predict_event(
            event.description,
            event.location,
        )
        inference_time = time.perf_counter() - inference_start

        print(
            f"AI Inference Time: "
            f"{inference_time:.3f} seconds"
        )

        # -----------------------------------------
        # Create or Update Risk Object
        # -----------------------------------------
        risk = db.query(Risk).filter(Risk.event_id == event.id).first()
        if risk:
            risk.risk_name = ai_result["category"]
            risk.risk_type = ai_result["category"]
            risk.risk_score = ai_result["confidence"] * 100
            risk.severity = ai_result["severity"]
            risk.probability = ai_result["confidence"]
        else:
            risk = Risk(
                risk_name=ai_result["category"],
                risk_type=ai_result["category"],
                risk_score=ai_result["confidence"] * 100,
                severity=ai_result["severity"],
                probability=ai_result["confidence"],
                status="Active",
                event_id=event.id,
            )
            db.add(risk)

        # Generate risk.id before creating prediction
        db.flush()

        # -----------------------------------------
        # Determine Prediction Status
        # -----------------------------------------
        confidence = ai_result["confidence"]

        if confidence >= 0.80:
            prediction_status = "Generated"
        elif confidence >= 0.60:
            prediction_status = "Needs Review"
        else:
            prediction_status = "Low Confidence"

        print(
            f"AI Prediction -> "
            f"Category: {ai_result['category']}, "
            f"Severity: {ai_result['severity']}, "
            f"Confidence: {confidence:.2f}, "
            f"Status: {prediction_status}"
        )

        # -----------------------------------------
        # Create or Update Prediction Object
        # -----------------------------------------
        prediction = db.query(Prediction).filter(Prediction.risk_id == risk.id).first()
        if prediction:
            prediction.predicted_risk = ai_result["category"]
            prediction.confidence_score = confidence
            prediction.predicted_severity = ai_result["severity"]
            prediction.prediction_status = prediction_status
        else:
            prediction = Prediction(
                predicted_risk=ai_result["category"],
                confidence_score=confidence,
                predicted_severity=ai_result["severity"],
                prediction_model="DistilBERT + XGBoost",
                prediction_status=prediction_status,
                risk_id=risk.id,
            )
            db.add(prediction)

        # Commit Risk & Prediction
        db.commit()

        db.refresh(risk)
        db.refresh(prediction)

        # -----------------------------------------
        # Generate & Save Recommendation
        # -----------------------------------------
        recommendation = save_generated_recommendation(
            db=db,
            prediction_id=prediction.id,
            category=prediction.predicted_risk,
            severity=prediction.predicted_severity,
        )
        
        pipeline_time = time.perf_counter() - pipeline_start

        print(
            f"Pipeline Execution Time: "
            f"{pipeline_time:.3f} seconds"
        )

        return {
            "event": event,
            "risk": risk,
            "prediction": prediction,
            "recommendation": recommendation,
            "ai_result": ai_result,
        }

    except Exception as e:
        db.rollback()
        raise RuntimeError(f"AI Pipeline Failed: {str(e)}")

def process_weather_event(
    db: Session,
    event: Event,
):
    """
    Process a weather event using deterministic rule-based risk generation.
    Uses the actual WeatherAPI data available in the normalized event.
    """
    try:
        pipeline_start = time.perf_counter()

        title = event.title or ""
        desc = event.description or ""
        temp_c, humidity, wind_kph, precip_mm, vis_km = _parse_weather_metrics(desc)

        category, severity, confidence, is_active = classify_weather_conditions(
            title=title,
            description=desc,
            temp_c=temp_c,
            humidity=humidity,
            wind_kph=wind_kph,
            precip_mm=precip_mm,
            vis_km=vis_km,
        )

        print(
            f"Rule-Based Prediction -> "
            f"Category: {category}, "
            f"Severity: {severity}, "
            f"Confidence: {confidence:.2f}"
        )

        risk_status = "Active" if is_active else "Inactive"
        risk_score = confidence * 100 if is_active else 0.0

        risk = db.query(Risk).filter(Risk.event_id == event.id).first()
        if risk:
            risk.risk_name = category
            risk.risk_type = category
            risk.risk_score = risk_score
            risk.severity = severity
            risk.probability = confidence
            risk.status = risk_status
        else:
            risk = Risk(
                risk_name=category,
                risk_type=category,
                risk_score=risk_score,
                severity=severity,
                probability=confidence,
                status=risk_status,
                event_id=event.id,
            )
            db.add(risk)
        db.flush()

        prediction = db.query(Prediction).filter(Prediction.risk_id == risk.id).first()
        if prediction:
            prediction.predicted_risk = category
            prediction.confidence_score = confidence
            prediction.predicted_severity = severity
            prediction.prediction_status = "Generated" if is_active else "Low Confidence"
        else:
            prediction = Prediction(
                predicted_risk=category,
                confidence_score=confidence,
                predicted_severity=severity,
                prediction_model="Rule-Based Weather Logic",
                prediction_status="Generated" if is_active else "Low Confidence",
                risk_id=risk.id,
            )
            db.add(prediction)
        db.commit()

        db.refresh(risk)
        db.refresh(prediction)

        recommendation = save_generated_recommendation(
            db=db,
            prediction_id=prediction.id,
            category=prediction.predicted_risk,
            severity=prediction.predicted_severity,
        )

        pipeline_time = time.perf_counter() - pipeline_start
        print(f"Weather Pipeline Execution Time: {pipeline_time:.3f} seconds")

        return {
            "event": event,
            "risk": risk,
            "prediction": prediction,
            "recommendation": recommendation,
        }

    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Weather Pipeline Failed: {str(e)}")