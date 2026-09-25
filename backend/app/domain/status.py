"""Legal status changes. The model is not a caller of these functions."""

from app.domain.enums import ReviewAction, SubmissionStatus
from app.domain.errors import InvalidTransitionError

_FINAL = {SubmissionStatus.APPROVED, SubmissionStatus.REJECTED}


def assert_analyzable(status: SubmissionStatus) -> None:
    if status in _FINAL:
        raise InvalidTransitionError("A final underwriting decision cannot be re-analyzed")
    if status == SubmissionStatus.PROCESSING:
        raise InvalidTransitionError("Analysis is already in progress")


def assert_reviewable(status: SubmissionStatus) -> None:
    if status != SubmissionStatus.READY_FOR_REVIEW:
        raise InvalidTransitionError("Only a submission ready for review can be decided")


def status_after_review(action: ReviewAction) -> SubmissionStatus:
    if action == ReviewAction.REJECT:
        return SubmissionStatus.REJECTED
    return SubmissionStatus.APPROVED
