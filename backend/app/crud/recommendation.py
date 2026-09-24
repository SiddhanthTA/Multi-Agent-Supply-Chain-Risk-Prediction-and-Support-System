from sqlalchemy.orm import Session

from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationCreate, RecommendationUpdate


def create_recommendation(db: Session, recommendation: RecommendationCreate):
    db_recommendation = Recommendation(**recommendation.model_dump())
    db.add(db_recommendation)
    db.commit()
    db.refresh(db_recommendation)
    return db_recommendation


def get_recommendation(db: Session, recommendation_id: int):
    return (
        db.query(Recommendation)
        .filter(Recommendation.id == recommendation_id)
        .first()
    )

def get_recommendation_by_prediction(
    db: Session,
    prediction_id: int,
    ):
    return (
        db.query(Recommendation)
        .filter(Recommendation.prediction_id == prediction_id)
        .first()
    )

def get_recommendations(db: Session):
    return db.query(Recommendation).all()


def update_recommendation(
    db: Session,
    recommendation_id: int,
    recommendation: RecommendationUpdate,
):
    db_recommendation = get_recommendation(db, recommendation_id)

    if not db_recommendation:
        return None

    update_data = recommendation.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_recommendation, key, value)

    db.commit()
    db.refresh(db_recommendation)

    return db_recommendation


def delete_recommendation(db: Session, recommendation_id: int):
    db_recommendation = get_recommendation(db, recommendation_id)

    if not db_recommendation:
        return None

    db.delete(db_recommendation)
    db.commit()

    return db_recommendation