"""Map persistence rows to response models at the HTTP boundary."""

from app.models.tables import (
    AIRecommendation,
    AIRun,
    AuditEvent,
    Claim,
    Company,
    Review,
    Submission,
)
from app.schemas.contracts import (
    AIRunRead,
    AuditEventRead,
    ClaimRead,
    CompanyRead,
    RecommendationRead,
    ReviewRead,
    SubmissionDetail,
    SubmissionSummary,
)


def company_read(company: Company) -> CompanyRead:
    return CompanyRead(
        id=company.id,
        name=company.name,
        industry=company.industry,
        annual_revenue_eur=company.annual_revenue_eur,
        employee_count=company.employee_count,
        countries=list(company.countries),
    )


def claim_read(claim: Claim) -> ClaimRead:
    return ClaimRead(
        id=claim.id,
        year=claim.year,
        claim_type=claim.claim_type,
        amount_eur=claim.amount_eur,
        description=claim.description,
    )


def submission_summary(submission: Submission, company: Company) -> SubmissionSummary:
    return SubmissionSummary(
        id=submission.id,
        company_id=submission.company_id,
        company_name=company.name,
        status=submission.status,
        assigned_underwriter_id=submission.assigned_underwriter_id,
        team_id=submission.team_id,
        product=submission.requested_coverage["product"],
        created_at=submission.created_at,
        updated_at=submission.updated_at,
    )


def submission_detail(submission: Submission, company: Company, claims: list[Claim]) -> SubmissionDetail:
    return SubmissionDetail(
        id=submission.id,
        company=company_read(company),
        status=submission.status,
        created_by=submission.created_by,
        assigned_underwriter_id=submission.assigned_underwriter_id,
        team_id=submission.team_id,
        requested_coverage=submission.requested_coverage,
        existing_policy=submission.existing_policy,
        narrative=submission.narrative,
        claims=[claim_read(claim) for claim in claims],
        created_at=submission.created_at,
        updated_at=submission.updated_at,
    )


def review_read(review: Review) -> ReviewRead:
    return ReviewRead(
        id=review.id,
        action=review.action,
        comment=review.comment,
        edited_payload=review.edited_payload,
        reviewer_id=review.reviewer_id,
        created_at=review.created_at,
    )


def recommendation_read(recommendation: AIRecommendation, review: Review | None) -> RecommendationRead:
    return RecommendationRead(
        id=recommendation.id,
        submission_id=recommendation.submission_id,
        summary=recommendation.summary,
        extracted_data=recommendation.extracted_data,
        risk_flags=recommendation.risk_flags,
        missing_information=list(recommendation.missing_information),
        follow_up_questions=list(recommendation.follow_up_questions),
        confidence=recommendation.confidence,
        source_references=list(recommendation.source_references),
        model=recommendation.model,
        status=recommendation.status,
        created_at=recommendation.created_at,
        human_review=review_read(review) if review else None,
    )


def audit_event_read(event: AuditEvent) -> AuditEventRead:
    return AuditEventRead(
        id=event.id,
        user_id=event.user_id,
        action=event.action,
        resource_type=event.resource_type,
        resource_id=event.resource_id,
        timestamp=event.occurred_at,
        metadata=event.details,
        request_id=event.request_id,
    )


def ai_run_read(run: AIRun) -> AIRunRead:
    return AIRunRead(
        id=run.id,
        request_id=run.request_id,
        user_id=run.user_id,
        submission_id=run.submission_id,
        model=run.model,
        latency_ms=run.latency_ms,
        retrieved_document_ids=list(run.retrieved_document_ids),
        tool_calls=list(run.tool_calls),
        success=run.success,
        outcome=run.outcome,
        token_usage=run.token_usage,
        created_at=run.created_at,
    )
