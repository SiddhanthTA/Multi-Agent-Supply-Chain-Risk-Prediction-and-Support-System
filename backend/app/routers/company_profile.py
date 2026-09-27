from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.company_profile import (
    CompanyProfileSaveError,
    company_profile_response,
    company_relevance_for_event,
    company_relevance_summary,
    get_company_profile,
    save_company_profile,
)
from app.database.database import get_db
from app.models.user import User
from app.schemas.company_profile import (
    CompanyProfileRequest,
    CompanyProfileResponse,
    CompanyRelevanceEvent,
    CompanyRelevanceSummary,
)

router = APIRouter(
    prefix="/company-profile",
    tags=["Company Profile"],
)


@router.get("", response_model=CompanyProfileResponse)
def read_company_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = get_company_profile(db, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found.",
        )
    return company_profile_response(profile)


@router.put("", response_model=CompanyProfileResponse)
def upsert_company_profile(
    payload: CompanyProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        profile = save_company_profile(db, current_user.id, payload)
    except CompanyProfileSaveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return company_profile_response(profile)


@router.get("/relevance", response_model=CompanyRelevanceSummary)
def read_company_relevance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_events: bool = True,
):
    """Company relevance for current intelligence, computed from the saved profile."""
    return company_relevance_summary(
        db,
        current_user.id,
        include_events=include_events,
    )


@router.get("/relevance/events/{event_id}", response_model=CompanyRelevanceEvent)
def read_event_company_relevance(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = company_relevance_for_event(db, current_user.id, event_id)
    if result is None:
        profile = get_company_profile(db, current_user.id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found.",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found.",
        )
    return result
