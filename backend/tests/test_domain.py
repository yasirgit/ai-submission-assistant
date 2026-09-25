"""Pure rules: no database and no HTTP."""

from types import SimpleNamespace

from app.domain.entitlements import can_read_submission, can_review_submission
from app.domain.enums import ReviewAction, Role, SubmissionStatus
from app.domain.errors import InvalidTransitionError
from app.domain.fingerprint import content_fingerprint
from app.domain.status import assert_analyzable, assert_reviewable, status_after_review

ALICE = SimpleNamespace(id="user-alice", role=Role.UNDERWRITER, team_id="team-north")
NOAH = SimpleNamespace(id="user-noah", role=Role.UNDERWRITER, team_id="team-north")
MIA = SimpleNamespace(id="user-mia", role=Role.MANAGER, team_id="team-north")
BOB = SimpleNamespace(id="user-bob", role=Role.UNDERWRITER, team_id="team-south")
ALEX = SimpleNamespace(id="user-alex", role=Role.ADMIN, team_id=None)


def _submission(assignee: str, team_id: str) -> SimpleNamespace:
    return SimpleNamespace(assigned_underwriter_id=assignee, team_id=team_id)


def test_underwriter_cannot_read_another_underwriters_submission() -> None:
    bobs = _submission("user-bob", "team-south")
    assert can_read_submission(ALICE, bobs) is False


def test_underwriter_cannot_read_a_teammates_submission() -> None:
    noahs = _submission("user-noah", "team-north")
    assert can_read_submission(ALICE, noahs) is False
    assert can_read_submission(NOAH, noahs) is True


def test_manager_reads_team_only() -> None:
    assert can_read_submission(MIA, _submission("user-alice", "team-north")) is True
    assert can_read_submission(MIA, _submission("user-bob", "team-south")) is False


def test_admin_reads_all() -> None:
    assert can_read_submission(ALEX, _submission("user-bob", "team-south")) is True


def test_review_follows_read_scope() -> None:
    bobs = _submission("user-bob", "team-south")
    assert can_review_submission(BOB, bobs) is True
    assert can_review_submission(ALICE, bobs) is False


def test_final_status_cannot_be_reanalyzed() -> None:
    for status in (SubmissionStatus.APPROVED, SubmissionStatus.REJECTED):
        try:
            assert_analyzable(status)
        except InvalidTransitionError:
            continue
        raise AssertionError(status)
    assert_analyzable(SubmissionStatus.NEW)


def test_only_ready_submissions_can_be_reviewed() -> None:
    try:
        assert_reviewable(SubmissionStatus.NEW)
    except InvalidTransitionError:
        pass
    else:
        raise AssertionError("new submissions are not reviewable")
    assert_reviewable(SubmissionStatus.READY_FOR_REVIEW)


def test_review_actions_set_the_human_decision() -> None:
    assert status_after_review(ReviewAction.ACCEPT) is SubmissionStatus.APPROVED
    assert status_after_review(ReviewAction.EDIT) is SubmissionStatus.APPROVED
    assert status_after_review(ReviewAction.REJECT) is SubmissionStatus.REJECTED


def test_fingerprint_ignores_repeated_whitespace() -> None:
    coverage = {"limit_eur": 1, "product": "Cyber Product X"}
    left = content_fingerprint("company-harbor", coverage, "same   text")
    right = content_fingerprint("company-harbor", coverage, "same text")
    assert left == right
