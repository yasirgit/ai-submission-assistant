"""Create, read, review, and analyze submissions.

Review is the only path that writes APPROVED or REJECTED.
Analysis stores a draft and moves the submission to READY_FOR_REVIEW.
"""

import json
import logging
import time
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.agents.loop import run_agent
from app.domain.entitlements import Principal, can_review_submission
from app.domain.enums import RecommendationStatus, ReviewAction, Role, SubmissionStatus
from app.domain.errors import (
    CompanyNotFoundError,
    DuplicateSubmissionError,
    ForbiddenError,
    InvalidTransitionError,
    NotFoundError,
)
from app.domain.fingerprint import content_fingerprint
from app.domain.status import assert_analyzable, assert_reviewable, status_after_review
from app.llm.types import LLMClient
from app.models.tables import AIRecommendation, AIRun, Claim, Company, Review, Submission
from app.repositories.audit import AuditRepository
from app.repositories.companies import CompanyRepository, UserRepository
from app.repositories.recommendations import RecommendationRepository, ReviewRepository
from app.repositories.runs import AIRunRepository
from app.repositories.submissions import SubmissionRepository
from app.schemas.contracts import ReviewCreate, SubmissionCreate
from app.services.analysis import AnalysisProduct
from app.services.audit import record
from app.services.clock import new_id, utc_now
from app.tools.gateway import ToolGateway

logger = logging.getLogger("finlex.analysis")


@dataclass
class SubmissionDetailData:
    submission: Submission
    company: Company
    claims: list[Claim]


@dataclass
class RecommendationData:
    recommendation: AIRecommendation
    review: Review | None


class SubmissionService:
    def __init__(
        self,
        session: Session,
        *,
        llm: LLMClient | None = None,
        build_retriever=None,
        retrieval_k: int = 5,
        tool_timeout_seconds: float = 2.0,
    ) -> None:
        self._session = session
        self._llm = llm
        self._build_retriever = build_retriever
        self._retrieval_k = retrieval_k
        self._tool_timeout_seconds = tool_timeout_seconds
        self._submissions = SubmissionRepository(session)
        self._companies = CompanyRepository(session)
        self._users = UserRepository(session)
        self._recommendations = RecommendationRepository(session)
        self._reviews = ReviewRepository(session)
        self._audit = AuditRepository(session)
        self._runs = AIRunRepository(session)

    def list_submissions(self, principal: Principal, limit: int) -> list[tuple[Submission, Company]]:
        return self._submissions.list_visible(principal, limit)

    def get_submission(self, principal: Principal, submission_id: str) -> SubmissionDetailData:
        submission = self._visible(principal, submission_id)
        company = self._companies.get(submission.company_id)
        if company is None:
            raise NotFoundError()
        claims = self._companies.list_claims(submission.company_id)
        return SubmissionDetailData(submission=submission, company=company, claims=claims)

    def create(
        self, principal: Principal, body: SubmissionCreate, request_id: str | None
    ) -> SubmissionDetailData:
        company = self._companies.get(body.company_id)
        if company is None:
            raise CompanyNotFoundError()
        assignee_id, team_id = self._assignment(principal, body.assigned_underwriter_id)
        coverage = body.requested_coverage.model_dump()
        fingerprint = content_fingerprint(body.company_id, coverage, body.narrative)
        existing = self._submissions.by_fingerprint(fingerprint)
        if existing is not None:
            raise DuplicateSubmissionError(existing.id)

        now = utc_now()
        submission = Submission(
            id=new_id(),
            company_id=body.company_id,
            status=SubmissionStatus.NEW,
            created_by=principal.id,
            assigned_underwriter_id=assignee_id,
            team_id=team_id,
            requested_coverage=coverage,
            existing_policy=body.existing_policy.model_dump() if body.existing_policy else None,
            narrative=body.narrative,
            content_fingerprint=fingerprint,
            created_at=now,
            updated_at=now,
        )
        try:
            self._submissions.add(submission)
        except IntegrityError:
            self._session.rollback()
            raced = self._submissions.by_fingerprint(fingerprint)
            raise DuplicateSubmissionError(raced.id if raced else "") from None

        record(
            self._audit,
            user_id=principal.id,
            action="submission.created",
            resource_type="submission",
            resource_id=submission.id,
            request_id=request_id,
            details={
                "company_id": submission.company_id,
                "assigned_underwriter_id": submission.assigned_underwriter_id,
                "status": submission.status.value,
            },
        )
        claims = self._companies.list_claims(company.id)
        return SubmissionDetailData(submission=submission, company=company, claims=claims)

    def get_recommendation(self, principal: Principal, submission_id: str) -> RecommendationData:
        self._visible(principal, submission_id)
        recommendation = self._recommendations.latest(submission_id)
        if recommendation is None:
            raise NotFoundError()
        review = self._reviews.for_recommendation(recommendation.id)
        return RecommendationData(recommendation=recommendation, review=review)

    def review(
        self,
        principal: Principal,
        submission_id: str,
        body: ReviewCreate,
        request_id: str | None,
    ) -> RecommendationData:
        submission = self._visible(principal, submission_id)
        if not can_review_submission(principal, submission):
            raise NotFoundError()
        assert_reviewable(submission.status)
        recommendation = self._recommendations.latest(submission_id)
        if recommendation is None or recommendation.status != RecommendationStatus.DRAFT:
            raise InvalidTransitionError("There is no draft recommendation to review")

        now = utc_now()
        edited = body.edited.model_dump(exclude_none=True) if body.edited else None
        review = self._reviews.add(
            Review(
                id=new_id(),
                submission_id=submission.id,
                recommendation_id=recommendation.id,
                reviewer_id=principal.id,
                action=body.action.value,
                comment=body.comment.strip(),
                edited_payload=edited,
                created_at=now,
            )
        )
        recommendation.status = _recommendation_status(body.action)
        submission.status = status_after_review(body.action)
        submission.updated_at = now
        record(
            self._audit,
            user_id=principal.id,
            action="submission.reviewed",
            resource_type="submission",
            resource_id=submission.id,
            request_id=request_id,
            details={
                "review_action": body.action.value,
                "recommendation_id": recommendation.id,
                "status": submission.status.value,
            },
        )
        return RecommendationData(recommendation=recommendation, review=review)

    def analyze(self, principal: Principal, submission_id: str, request_id: str | None) -> RecommendationData:
        submission = self._visible(principal, submission_id)
        assert_analyzable(submission.status)
        if self._llm is None or self._build_retriever is None:
            raise RuntimeError("Analysis requires a model client and a retriever")
        gateway = ToolGateway(
            self._session,
            principal,
            self._audit,
            self._build_retriever(self._session),
            submission_id=submission.id,
            request_id=request_id,
            retrieval_k=self._retrieval_k,
            tool_timeout_seconds=self._tool_timeout_seconds,
        )
        started = time.perf_counter()
        product = run_agent(self._llm, gateway, submission.id)
        latency_ms = int((time.perf_counter() - started) * 1000)
        if product.error is not None:
            self._record_analysis(principal, submission, request_id, product, latency_ms, success=False)
            raise product.error

        now = utc_now()
        recommendation = self._recommendations.add(
            AIRecommendation(
                id=new_id(),
                submission_id=submission.id,
                summary=product.summary,
                extracted_data=product.extracted_data,
                risk_flags=product.risk_flags,
                missing_information=product.missing_information,
                follow_up_questions=product.follow_up_questions,
                confidence=product.confidence,
                source_references=product.sources,
                model=product.model,
                status=RecommendationStatus.DRAFT,
                created_at=now,
            )
        )
        submission.status = SubmissionStatus.READY_FOR_REVIEW
        submission.updated_at = now
        self._record_analysis(principal, submission, request_id, product, latency_ms, success=True)
        return RecommendationData(recommendation=recommendation, review=None)

    def _record_analysis(
        self,
        principal: Principal,
        submission: Submission,
        request_id: str | None,
        product: AnalysisProduct,
        latency_ms: int,
        *,
        success: bool,
    ) -> None:
        self._runs.add(
            AIRun(
                id=new_id(),
                request_id=request_id or "",
                user_id=principal.id,
                submission_id=submission.id,
                model=product.model,
                latency_ms=latency_ms,
                retrieved_document_ids=product.retrieved_document_ids,
                tool_calls=list(product.tool_calls),
                success=success,
                token_usage=product.token_usage or None,
                outcome=product.outcome,
                created_at=utc_now(),
            )
        )
        record(
            self._audit,
            user_id=principal.id,
            action="analysis.completed" if success else "analysis.failed",
            resource_type="submission",
            resource_id=submission.id,
            request_id=request_id,
            details={
                "outcome": product.outcome,
                "model": product.model,
                "retrieved_document_ids": product.retrieved_document_ids,
                "dropped_source_ids": product.dropped_source_ids,
                "status": submission.status.value,
            },
        )
        logger.info(
            json.dumps(
                {
                    "event": "analysis",
                    "request_id": request_id,
                    "user_id": principal.id,
                    "submission_id": submission.id,
                    "model": product.model,
                    "latency_ms": latency_ms,
                    "retrieved_document_ids": product.retrieved_document_ids,
                    "outcome": product.outcome,
                    "success": success,
                    "tool_calls": product.tool_calls,
                    "prompt_tokens": (product.token_usage or {}).get("prompt_tokens"),
                }
            )
        )

    def list_audit(self, principal: Principal, submission_id: str):
        self._visible(principal, submission_id)
        return self._audit.list_for_submission(submission_id)

    def _visible(self, principal: Principal, submission_id: str) -> Submission:
        submission = self._submissions.get_visible(principal, submission_id)
        if submission is None:
            raise NotFoundError()
        return submission

    def _assignment(self, principal: Principal, requested_assignee: str | None) -> tuple[str, str | None]:
        if principal.role == Role.UNDERWRITER:
            if requested_assignee and requested_assignee != principal.id:
                raise ForbiddenError("Underwriters can only assign submissions to themselves")
            return principal.id, principal.team_id

        if not requested_assignee:
            raise ForbiddenError("An underwriter must be assigned")
        assignee = self._users.get(requested_assignee)
        if assignee is None or assignee.role != Role.UNDERWRITER:
            raise ForbiddenError("Assignee must be an underwriter")
        if principal.role == Role.MANAGER and assignee.team_id != principal.team_id:
            raise ForbiddenError("Assignee must be an underwriter on your team")
        if principal.role == Role.ADMIN:
            return assignee.id, assignee.team_id
        if principal.role == Role.MANAGER:
            return assignee.id, principal.team_id
        raise ForbiddenError("Assignee must be an underwriter")


def _recommendation_status(action: ReviewAction) -> RecommendationStatus:
    if action == ReviewAction.ACCEPT:
        return RecommendationStatus.ACCEPTED
    if action == ReviewAction.EDIT:
        return RecommendationStatus.EDITED
    return RecommendationStatus.REJECTED
