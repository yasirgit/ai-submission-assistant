"""AI run records visible to the caller."""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.domain.entitlements import Principal
from app.domain.enums import Role
from app.models.tables import AIRun, Submission


class AIRunRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_visible(self, principal: Principal, limit: int) -> list[AIRun]:
        stmt = select(AIRun).order_by(AIRun.created_at.desc()).limit(limit)
        if principal.role == Role.ADMIN:
            return list(self._session.scalars(stmt).all())
        if principal.role == Role.MANAGER and principal.team_id is not None:
            stmt = (
                select(AIRun)
                .outerjoin(Submission, AIRun.submission_id == Submission.id)
                .where(or_(AIRun.user_id == principal.id, Submission.team_id == principal.team_id))
                .order_by(AIRun.created_at.desc())
                .limit(limit)
            )
            return list(self._session.scalars(stmt).all())
        scoped = select(AIRun).where(AIRun.user_id == principal.id).order_by(AIRun.created_at.desc())
        return list(self._session.scalars(scoped.limit(limit)).all())

    def add(self, run: AIRun) -> AIRun:
        self._session.add(run)
        self._session.flush()
        return run
