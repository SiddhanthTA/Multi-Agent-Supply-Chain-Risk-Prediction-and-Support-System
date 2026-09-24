from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.services.correlation_engine import correlate_risks


router = APIRouter(
    prefix="/correlation",
    tags=["Correlation Engine"],
)


@router.get("/summary")
def correlation_summary(
    db: Session = Depends(get_db),
):
    """
    Generate an overall supply chain
    correlation summary.
    """

    result = correlate_risks(db)

    return {
        "message": "Correlation analysis completed successfully.",
        "results": result,
    }