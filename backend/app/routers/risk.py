from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.crud.risk import (
    create_risk,
    get_risk,
    get_risks,
    update_risk,
    delete_risk,
)
from app.schemas.risk import (
    RiskCreate,
    RiskUpdate,
    RiskResponse,
)

router = APIRouter(
    prefix="/risks",
    tags=["Risks"]
)


@router.post("/", response_model=RiskResponse)
def create_new_risk(risk: RiskCreate, db: Session = Depends(get_db)):
    return create_risk(db, risk)


@router.get("/", response_model=list[RiskResponse])
def read_risks(db: Session = Depends(get_db)):
    return get_risks(db)


@router.get("/{risk_id}", response_model=RiskResponse)
def read_risk(risk_id: int, db: Session = Depends(get_db)):
    risk = get_risk(db, risk_id)

    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    return risk


@router.put("/{risk_id}", response_model=RiskResponse)
def update_existing_risk(
    risk_id: int,
    risk: RiskUpdate,
    db: Session = Depends(get_db),
):
    updated_risk = update_risk(db, risk_id, risk)

    if not updated_risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    return updated_risk


@router.delete("/{risk_id}")
def delete_existing_risk(
    risk_id: int,
    db: Session = Depends(get_db),
):
    deleted_risk = delete_risk(db, risk_id)

    if not deleted_risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    return {"message": "Risk deleted successfully"}