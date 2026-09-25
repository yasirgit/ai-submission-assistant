"""Liveness. Database failures stay generic."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.schemas.contracts import HealthRead

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthRead)
def health(session: Session = Depends(get_session)) -> HealthRead | JSONResponse:
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        session.rollback()
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": "unavailable"},
        )
    return HealthRead(status="ok", database="ok")
