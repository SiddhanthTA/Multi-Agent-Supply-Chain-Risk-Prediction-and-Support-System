from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.crud.system_log import (
    create_system_log,
    get_system_log,
    get_system_logs,
    update_system_log,
    delete_system_log,
)
from app.schemas.system_log import (
    SystemLogCreate,
    SystemLogUpdate,
    SystemLogResponse,
)

router = APIRouter(
    prefix="/system-logs",
    tags=["System Logs"]
)


@router.post("/", response_model=SystemLogResponse)
def create_new_system_log(
    system_log: SystemLogCreate,
    db: Session = Depends(get_db),
):
    return create_system_log(db, system_log)


@router.get("/", response_model=list[SystemLogResponse])
def read_system_logs(db: Session = Depends(get_db)):
    return get_system_logs(db)


@router.get("/{system_log_id}", response_model=SystemLogResponse)
def read_system_log(
    system_log_id: int,
    db: Session = Depends(get_db),
):
    system_log = get_system_log(db, system_log_id)

    if not system_log:
        raise HTTPException(
            status_code=404,
            detail="System Log not found"
        )

    return system_log


@router.put("/{system_log_id}", response_model=SystemLogResponse)
def update_existing_system_log(
    system_log_id: int,
    system_log: SystemLogUpdate,
    db: Session = Depends(get_db),
):
    updated_system_log = update_system_log(
        db,
        system_log_id,
        system_log,
    )

    if not updated_system_log:
        raise HTTPException(
            status_code=404,
            detail="System Log not found"
        )

    return updated_system_log


@router.delete("/{system_log_id}")
def delete_existing_system_log(
    system_log_id: int,
    db: Session = Depends(get_db),
):
    deleted_system_log = delete_system_log(
        db,
        system_log_id,
    )

    if not deleted_system_log:
        raise HTTPException(
            status_code=404,
            detail="System Log not found"
        )

    return {"message": "System Log deleted successfully"}