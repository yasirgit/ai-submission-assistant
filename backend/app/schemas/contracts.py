"""HTTP and review contracts. Database rows are mapped into these models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import (
    RecommendationStatus,
    ReviewAction,
    RiskFlagType,
    Severity,
    SubmissionStatus,
)

ASSISTANCE_DISCLAIMER = "AI-generated assistance — final decision remains with the underwriter."


class CoverageIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product: str = Field(min_length=1, max_length=120)
    limit_eur: int = Field(ge=0, le=100_000_000)


class PolicyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    carrier: str = Field(min_length=1, max_length=120)
    limit_eur: int = Field(ge=0, le=100_000_000)


class SubmissionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str = Field(min_length=1, max_length=64)
    requested_coverage: CoverageIn
    existing_policy: PolicyIn | None = None
    narrative: str = Field(min_length=1, max_length=20_000)
    assigned_underwriter_id: str | None = Field(default=None, max_length=64)


class ClaimRead(BaseModel):
    id: str
    year: int
    claim_type: str
    amount_eur: int
    description: str


class CompanyRead(BaseModel):
    id: str
    name: str
    industry: str
    annual_revenue_eur: int
    employee_count: int
    countries: list[str]


class SubmissionSummary(BaseModel):
    id: str
    company_id: str
    company_name: str
    status: SubmissionStatus
    assigned_underwriter_id: str
    team_id: str | None
    product: str
    created_at: datetime
    updated_at: datetime


class SubmissionList(BaseModel):
    submissions: list[SubmissionSummary]


class SubmissionDetail(BaseModel):
    id: str
    company: CompanyRead
    status: SubmissionStatus
    created_by: str
    assigned_underwriter_id: str
    team_id: str | None
    requested_coverage: CoverageIn
    existing_policy: PolicyIn | None
    narrative: str
    claims: list[ClaimRead]
    created_at: datetime
    updated_at: datetime


class RiskFlag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: RiskFlagType
    severity: Severity
    description: str = Field(min_length=1, max_length=500)


class SourceReference(BaseModel):
    document_id: str
    chunk_id: str
    title: str
    excerpt: str = ""


class EditedAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str | None = Field(default=None, max_length=4000)
    risk_flags: list[RiskFlag] | None = None
    missing_information: list[str] | None = None
    follow_up_questions: list[str] | None = None

    @model_validator(mode="after")
    def at_least_one_change(self) -> "EditedAnalysis":
        changed = (
            self.summary,
            self.risk_flags,
            self.missing_information,
            self.follow_up_questions,
        )
        if not any(value is not None for value in changed):
            raise ValueError("edited payload must change at least one field")
        return self


class ReviewCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: ReviewAction
    comment: str = Field(default="", max_length=2000)
    edited: EditedAnalysis | None = None

    @model_validator(mode="after")
    def action_matches_payload(self) -> "ReviewCreate":
        if self.action == ReviewAction.REJECT and not self.comment.strip():
            raise ValueError("A rejection needs a comment")
        if self.action == ReviewAction.EDIT and self.edited is None:
            raise ValueError("EDIT requires an edited payload")
        if self.action != ReviewAction.EDIT and self.edited is not None:
            raise ValueError("edited payload is only valid when action is EDIT")
        return self


class ReviewRead(BaseModel):
    id: str
    action: ReviewAction
    comment: str
    edited_payload: dict | None
    reviewer_id: str
    created_at: datetime
    disclaimer: str = ASSISTANCE_DISCLAIMER


class RecommendationRead(BaseModel):
    id: str
    submission_id: str
    summary: str
    extracted_data: dict
    risk_flags: list[RiskFlag]
    missing_information: list[str]
    follow_up_questions: list[str]
    confidence: float = Field(ge=0, le=1)
    source_references: list[SourceReference]
    model: str
    status: RecommendationStatus
    created_at: datetime
    human_review: ReviewRead | None
    disclaimer: str = ASSISTANCE_DISCLAIMER


class AuditEventRead(BaseModel):
    id: str
    user_id: str | None
    action: str
    resource_type: str
    resource_id: str
    timestamp: datetime
    metadata: dict
    request_id: str | None


class AuditList(BaseModel):
    events: list[AuditEventRead]


class GuidelineHit(BaseModel):
    document_id: str
    document_title: str
    chunk_id: str
    excerpt: str


class GuidelineSearchResult(BaseModel):
    results: list[GuidelineHit]


class AIRunRead(BaseModel):
    id: str
    request_id: str
    user_id: str
    submission_id: str | None
    model: str
    latency_ms: int | None
    retrieved_document_ids: list[str]
    tool_calls: list[str]
    success: bool
    outcome: str
    token_usage: dict | None
    created_at: datetime


class AIRunList(BaseModel):
    runs: list[AIRunRead]


class HealthRead(BaseModel):
    status: str
    database: str
