"""Append-only audit events."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tables import AuditEvent


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, event: AuditEvent) -> AuditEvent:
        self._session.add(event)
        self._session.flush()
        return event

    def list_for_submission(self, submission_id: str) -> list[AuditEvent]:
        stmt = (
            select(AuditEvent)
            .where(
                AuditEvent.resource_type == "submission",
                AuditEvent.resource_id == submission_id,
            )
            .order_by(AuditEvent.occurred_at.asc())
        )
        return list(self._session.scalars(stmt).all())
