from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.risk_investigation import RiskInvestigationAgent
from app.agents.tools import InvestigationAccessError, InvestigationNotFoundError
from app.ai.llm_provider import (
    AgentBusyError,
    AgentOutputError,
    AgentTimeoutError,
    AgentUnavailableError,
)
from app.api.deps import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.investigation import (
    InvestigationActor,
    InvestigationResponse,
)

router = APIRouter(prefix="/investigations", tags=["Risk Investigations"])


@router.post("/risk/{risk_id}", response_model=InvestigationResponse)
def investigate_risk(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    actor = InvestigationActor(user_id=current_user.id, role=current_user.role)
    try:
        return RiskInvestigationAgent().investigate(db, risk_id, actor=actor)
    except InvestigationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvestigationAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except AgentBusyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except AgentTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except AgentUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except AgentOutputError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
