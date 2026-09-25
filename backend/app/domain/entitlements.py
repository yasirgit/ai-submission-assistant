"""Who may read a submission.

This module is the authorization rule. Prompts and model output do not
grant access. SQL repositories must apply the same split.
"""

from typing import Protocol

from app.domain.enums import Role


class Principal(Protocol):
    id: str
    role: Role
    team_id: str | None


class SubmissionScope(Protocol):
    assigned_underwriter_id: str
    team_id: str | None


def can_read_submission(principal: Principal, submission: SubmissionScope) -> bool:
    if principal.role == Role.ADMIN:
        return True
    if principal.role == Role.MANAGER:
        return principal.team_id is not None and submission.team_id == principal.team_id
    if principal.role == Role.UNDERWRITER:
        return submission.assigned_underwriter_id == principal.id
    return False


def can_review_submission(principal: Principal, submission: SubmissionScope) -> bool:
    """Review uses the same scope as read until a tighter rule is needed."""
    return can_read_submission(principal, submission)
