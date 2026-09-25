"""SQL form of the submission entitlement rule.

Keep this aligned with app.domain.entitlements.can_read_submission.
The filter belongs in the query so other tenants' rows are not loaded.
"""

from sqlalchemy import false, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.domain.entitlements import Principal
from app.domain.enums import Role
from app.models.tables import Company, Submission


def scope_submissions(stmt: Select, principal: Principal) -> Select:
    if principal.role == Role.ADMIN:
        return stmt
    if principal.role == Role.MANAGER:
        if principal.team_id is None:
            return stmt.where(false())
        return stmt.where(Submission.team_id == principal.team_id)
    if principal.role == Role.UNDERWRITER:
        return stmt.where(Submission.assigned_underwriter_id == principal.id)
    return stmt.where(false())


def has_visible_submission(session: Session, principal: Principal, company_id: str) -> bool:
    if principal.role == Role.ADMIN:
        return session.get(Company, company_id) is not None
    stmt = scope_submissions(
        select(Submission.id).where(Submission.company_id == company_id),
        principal,
    ).limit(1)
    return session.scalar(stmt) is not None
