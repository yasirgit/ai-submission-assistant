"""Guideline search. Results are published guideline chunks only."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_principal, get_session
from app.schemas.contracts import GuidelineHit, GuidelineSearchResult
from app.services.guidelines import GuidelineService

router = APIRouter(prefix="/guidelines", tags=["guidelines"])


@router.get("/search", response_model=GuidelineSearchResult)
def search_guidelines(
    q: str = Query(default="", max_length=200),
    limit: int = Query(default=10, ge=1, le=20),
    _principal=Depends(get_principal),
    session: Session = Depends(get_session),
) -> GuidelineSearchResult:
    hits = GuidelineService(session).search(q, limit)
    return GuidelineSearchResult(results=[GuidelineHit.model_validate(hit) for hit in hits])
