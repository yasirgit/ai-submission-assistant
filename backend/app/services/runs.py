"""Read AI run records inside the caller's scope."""

from sqlalchemy.orm import Session

from app.domain.entitlements import Principal
from app.repositories.runs import AIRunRepository


class AIRunService:
    def __init__(self, session: Session) -> None:
        self._runs = AIRunRepository(session)

    def list_runs(self, principal: Principal, limit: int):
        return self._runs.list_visible(principal, limit)
