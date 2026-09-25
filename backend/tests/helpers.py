"""Shared headers and rows the model phase will create later."""

from datetime import UTC, datetime

from app.domain.enums import RecommendationStatus, SubmissionStatus
from app.models.tables import AIRecommendation, AIRun, Submission

ALICE = {"X-User-Id": "user-alice"}
NOAH = {"X-User-Id": "user-noah"}
BOB = {"X-User-Id": "user-bob"}
MIA = {"X-User-Id": "user-mia"}
ALEX = {"X-User-Id": "user-alex"}

ALICE_SUBMISSION = "sub-alice-harbor-cyber"
BOB_SUBMISSION = "sub-bob-brightgrid-cyber"
NOAH_SUBMISSION = "sub-noah-nordic-cyber"


def add_draft(api, submission_id: str, recommendation_id: str = "rec-draft") -> None:
    factory = api.app.state.session_factory
    with factory() as session:
        submission = session.get(Submission, submission_id)
        assert submission is not None
        submission.status = SubmissionStatus.READY_FOR_REVIEW
        session.add(
            AIRecommendation(
                id=recommendation_id,
                submission_id=submission_id,
                summary="Draft summary for human review.",
                extracted_data={"company_name": "Synthetic"},
                risk_flags=[
                    {
                        "type": "REVENUE",
                        "severity": "MEDIUM",
                        "description": "Revenue sits in a conflicting band.",
                    }
                ],
                missing_information=["Latest audited revenue"],
                follow_up_questions=["Please confirm audited revenue."],
                confidence=0.62,
                source_references=[],
                model="mock",
                status=RecommendationStatus.DRAFT,
                created_at=datetime.now(UTC),
            )
        )
        session.commit()


def add_run(api, run: AIRun) -> None:
    factory = api.app.state.session_factory
    with factory() as session:
        session.add(run)
        session.commit()
