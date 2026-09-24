from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.crud.ai_log import (
    create_ai_log,
    get_ai_log,
    get_ai_logs,
    update_ai_log,
    delete_ai_log,
)
from app.schemas.ai_log import (
    AILogCreate,
    AILogUpdate,
    AILogResponse,
)

router = APIRouter(
    prefix="/ai-logs",
    tags=["AI Logs"]
)


@router.post("/", response_model=AILogResponse)
def create_new_ai_log(
    ai_log: AILogCreate,
    db: Session = Depends(get_db),
):
    return create_ai_log(db, ai_log)


@router.get("/", response_model=list[AILogResponse])
def read_ai_logs(db: Session = Depends(get_db)):
    return get_ai_logs(db)


@router.get("/{ai_log_id}", response_model=AILogResponse)
def read_ai_log(
    ai_log_id: int,
    db: Session = Depends(get_db),
):
    ai_log = get_ai_log(db, ai_log_id)

    if not ai_log:
        raise HTTPException(
            status_code=404,
            detail="AI Log not found"
        )

    return ai_log


@router.put("/{ai_log_id}", response_model=AILogResponse)
def update_existing_ai_log(
    ai_log_id: int,
    ai_log: AILogUpdate,
    db: Session = Depends(get_db),
):
    updated_ai_log = update_ai_log(
        db,
        ai_log_id,
        ai_log,
    )

    if not updated_ai_log:
        raise HTTPException(
            status_code=404,
            detail="AI Log not found"
        )

    return updated_ai_log


@router.delete("/{ai_log_id}")
def delete_existing_ai_log(
    ai_log_id: int,
    db: Session = Depends(get_db),
):
    deleted_ai_log = delete_ai_log(
        db,
        ai_log_id,
    )

    if not deleted_ai_log:
        raise HTTPException(
            status_code=404,
            detail="AI Log not found"
        )

    return {"message": "AI Log deleted successfully"}