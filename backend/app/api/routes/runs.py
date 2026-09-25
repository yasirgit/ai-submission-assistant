"""Recent AI runs for the caller."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_principal, get_session
from app.domain.entitlements import Principal
from app.schemas.contracts import AIRunList
from app.schemas.mapping import ai_run_read
from app.services.runs import AIRunService

router = APIRouter(prefix="/ai-runs", tags=["ai-runs"])


@router.get("", response_model=AIRunList)
def list_runs(
    limit: int = Query(default=20, ge=1, le=100),
    principal: Principal = Depends(get_principal),
    session: Session = Depends(get_session),
) -> AIRunList:
    runs = AIRunService(session).list_runs(principal, limit)
    return AIRunList(runs=[ai_run_read(run) for run in runs])
