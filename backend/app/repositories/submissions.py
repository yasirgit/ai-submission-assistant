"""Submission persistence. Reads are scoped to a principal."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entitlements import Principal
from app.models.tables import Company, Submission
from app.repositories.scope import scope_submissions


class SubmissionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_visible(self, principal: Principal, submission_id: str) -> Submission | None:
        stmt = scope_submissions(select(Submission).where(Submission.id == submission_id), principal)
        return self._session.scalars(stmt).one_or_none()

    def list_visible(self, principal: Principal, limit: int) -> list[tuple[Submission, Company]]:
        stmt = scope_submissions(
            select(Submission, Company).join(Company, Submission.company_id == Company.id),
            principal,
        )
        stmt = stmt.order_by(Submission.created_at.desc()).limit(limit)
        return list(self._session.execute(stmt).all())

    def by_fingerprint(self, fingerprint: str) -> Submission | None:
        stmt = select(Submission).where(Submission.content_fingerprint == fingerprint)
        return self._session.scalars(stmt).one_or_none()

    def add(self, submission: Submission) -> Submission:
        self._session.add(submission)
        self._session.flush()
        return submission
