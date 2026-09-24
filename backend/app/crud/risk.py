from sqlalchemy.orm import Session

from app.models.risk import Risk
from app.schemas.risk import RiskCreate, RiskUpdate


def create_risk(db: Session, risk: RiskCreate):
    db_risk = Risk(**risk.model_dump())
    db.add(db_risk)
    db.commit()
    db.refresh(db_risk)
    return db_risk


def get_risk(db: Session, risk_id: int):
    return db.query(Risk).filter(Risk.id == risk_id).first()


def get_risks(db: Session):
    return db.query(Risk).all()

def get_risk_by_event(db: Session, event_id: int):
    return (
        db.query(Risk)
        .filter(Risk.event_id == event_id)
        .first()
    )

def update_risk(db: Session, risk_id: int, risk: RiskUpdate):
    db_risk = get_risk(db, risk_id)

    if not db_risk:
        return None

    update_data = risk.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_risk, key, value)

    db.commit()
    db.refresh(db_risk)

    return db_risk


def delete_risk(db: Session, risk_id: int):
    db_risk = get_risk(db, risk_id)

    if not db_risk:
        return None

    db.delete(db_risk)
    db.commit()

    return db_risk