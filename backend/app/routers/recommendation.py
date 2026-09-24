from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.crud.recommendation import (
    create_recommendation,
    get_recommendation,
    get_recommendations,
    update_recommendation,
    delete_recommendation,
)
from app.schemas.recommendation import (
    RecommendationCreate,
    RecommendationUpdate,
    RecommendationResponse,
)

from app.crud.recommendation import (
    create_recommendation,
    get_recommendation,
    get_recommendations,
    get_recommendation_by_prediction,
    update_recommendation,
    delete_recommendation,
)

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.post("/", response_model=RecommendationResponse)
def create_new_recommendation(
    recommendation: RecommendationCreate,
    db: Session = Depends(get_db),
):
    return create_recommendation(db, recommendation)


@router.get("/", response_model=list[RecommendationResponse])
def read_recommendations(db: Session = Depends(get_db)):
    return get_recommendations(db)

@router.get(
    "/prediction/{prediction_id}",
    response_model=RecommendationResponse,
)
def read_recommendation_by_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
):
    recommendation = get_recommendation_by_prediction(
        db,
        prediction_id,
    )

    if not recommendation:
        raise HTTPException(
            status_code=404,
            detail="Recommendation not found",
        )

    return recommendation

@router.get("/{recommendation_id}", response_model=RecommendationResponse)
def read_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
):
    recommendation = get_recommendation(db, recommendation_id)

    if not recommendation:
        raise HTTPException(
            status_code=404,
            detail="Recommendation not found"
        )

    return recommendation


@router.put("/{recommendation_id}", response_model=RecommendationResponse)
def update_existing_recommendation(
    recommendation_id: int,
    recommendation: RecommendationUpdate,
    db: Session = Depends(get_db),
):
    updated_recommendation = update_recommendation(
        db,
        recommendation_id,
        recommendation,
    )

    if not updated_recommendation:
        raise HTTPException(
            status_code=404,
            detail="Recommendation not found"
        )

    return updated_recommendation


@router.delete("/{recommendation_id}")
def delete_existing_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
):
    deleted_recommendation = delete_recommendation(
        db,
        recommendation_id,
    )

    if not deleted_recommendation:
        raise HTTPException(
            status_code=404,
            detail="Recommendation not found"
        )

    return {"message": "Recommendation deleted successfully"}