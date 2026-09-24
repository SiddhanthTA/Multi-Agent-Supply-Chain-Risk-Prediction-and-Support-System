from sqlalchemy.orm import Session

from app.ai.recommendation_engine import generate_recommendation
from app.crud.recommendation import create_recommendation
from app.schemas.recommendation import RecommendationCreate


def save_generated_recommendation(
    db: Session,
    prediction_id: int,
    category: str,
    severity: str,
):
    """
    Generate a recommendation using the AI recommendation engine
    and save it to the database.
    """

    from app.crud.recommendation import create_recommendation, get_recommendation_by_prediction
    
    existing = get_recommendation_by_prediction(db, prediction_id)

    recommendation = generate_recommendation(
        category=category,
        severity=severity,
    )
    
    if existing:
        existing.recommendation_title = recommendation["title"]
        existing.recommendation_text = recommendation["description"]
        existing.priority = recommendation["priority"]
        db.commit()
        db.refresh(existing)
        return existing

    recommendation_data = RecommendationCreate(
        prediction_id=prediction_id,
        recommendation_title=recommendation["title"],
        recommendation_text=recommendation["description"],
        priority=recommendation["priority"],
        status="Generated",
    )

    saved_recommendation = create_recommendation(
        db=db,
        recommendation=recommendation_data,
    )

    return saved_recommendation