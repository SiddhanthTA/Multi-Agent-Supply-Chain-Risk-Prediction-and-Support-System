from sqlalchemy.orm import Session

from app.models.prediction import Prediction
from app.schemas.prediction import PredictionCreate, PredictionUpdate


def create_prediction(db: Session, prediction: PredictionCreate):
    db_prediction = Prediction(**prediction.model_dump())
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    return db_prediction


def get_prediction(db: Session, prediction_id: int):
    return db.query(Prediction).filter(Prediction.id == prediction_id).first()


def get_predictions(db: Session):
    return db.query(Prediction).all()


def update_prediction(db: Session, prediction_id: int, prediction: PredictionUpdate):
    db_prediction = get_prediction(db, prediction_id)

    if not db_prediction:
        return None

    update_data = prediction.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_prediction, key, value)

    db.commit()
    db.refresh(db_prediction)

    return db_prediction


def delete_prediction(db: Session, prediction_id: int):
    db_prediction = get_prediction(db, prediction_id)

    if not db_prediction:
        return None

    db.delete(db_prediction)
    db.commit()

    return db_prediction