from sqlalchemy.orm import Session

from app.models.ai_log import AILog
from app.schemas.ai_log import AILogCreate, AILogUpdate


def create_ai_log(db: Session, ai_log: AILogCreate):
    db_ai_log = AILog(**ai_log.model_dump())
    db.add(db_ai_log)
    db.commit()
    db.refresh(db_ai_log)
    return db_ai_log


def get_ai_log(db: Session, ai_log_id: int):
    return db.query(AILog).filter(AILog.id == ai_log_id).first()


def get_ai_logs(db: Session):
    return db.query(AILog).all()


def update_ai_log(db: Session, ai_log_id: int, ai_log: AILogUpdate):
    db_ai_log = get_ai_log(db, ai_log_id)

    if not db_ai_log:
        return None

    update_data = ai_log.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_ai_log, key, value)

    db.commit()
    db.refresh(db_ai_log)

    return db_ai_log


def delete_ai_log(db: Session, ai_log_id: int):
    db_ai_log = get_ai_log(db, ai_log_id)

    if not db_ai_log:
        return None

    db.delete(db_ai_log)
    db.commit()

    return db_ai_log