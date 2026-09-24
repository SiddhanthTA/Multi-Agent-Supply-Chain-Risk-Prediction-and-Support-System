from sqlalchemy.orm import Session

from app.models.system_log import SystemLog
from app.schemas.system_log import SystemLogCreate, SystemLogUpdate


def create_system_log(db: Session, system_log: SystemLogCreate):
    db_system_log = SystemLog(**system_log.model_dump())
    db.add(db_system_log)
    db.commit()
    db.refresh(db_system_log)
    return db_system_log


def get_system_log(db: Session, system_log_id: int):
    return db.query(SystemLog).filter(SystemLog.id == system_log_id).first()


def get_system_logs(db: Session):
    return db.query(SystemLog).all()


def update_system_log(
    db: Session,
    system_log_id: int,
    system_log: SystemLogUpdate,
):
    db_system_log = get_system_log(db, system_log_id)

    if not db_system_log:
        return None

    update_data = system_log.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_system_log, key, value)

    db.commit()
    db.refresh(db_system_log)

    return db_system_log


def delete_system_log(db: Session, system_log_id: int):
    db_system_log = get_system_log(db, system_log_id)

    if not db_system_log:
        return None

    db.delete(db_system_log)
    db.commit()

    return db_system_log