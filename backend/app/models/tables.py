"""Persistence tables. These objects are not API responses."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SaEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import (
    DocumentType,
    RecommendationStatus,
    Role,
    SubmissionStatus,
)
from app.models.base import Base

_STR_ENUM = {"native_enum": False, "length": 32}


def _enum(enum_type: type) -> SaEnum:
    return SaEnum(enum_type, **_STR_ENUM)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[Role] = mapped_column(_enum(Role), nullable=False)
    team_id: Mapped[str | None] = mapped_column(String(64))


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str] = mapped_column(String(80), nullable=False)
    annual_revenue_eur: Mapped[int] = mapped_column(Integer, nullable=False)
    employee_count: Mapped[int] = mapped_column(Integer, nullable=False)
    countries: Mapped[list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(80), nullable=False)
    amount_eur: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint("content_fingerprint", name="uq_submission_fingerprint"),
        Index("ix_submission_assignee", "assigned_underwriter_id"),
        Index("ix_submission_team", "team_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    status: Mapped[SubmissionStatus] = mapped_column(
        _enum(SubmissionStatus), nullable=False, default=SubmissionStatus.NEW
    )
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_underwriter_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_id: Mapped[str | None] = mapped_column(String(64))
    requested_coverage: Mapped[dict] = mapped_column(JSON, nullable=False)
    existing_policy: Mapped[dict | None] = mapped_column(JSON)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    content_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Document(Base):
    """Guideline and submission text. Body text is always untrusted data."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    doc_type: Mapped[DocumentType] = mapped_column(_enum(DocumentType), nullable=False)
    owner_company_id: Mapped[str | None] = mapped_column(ForeignKey("companies.id"))
    trust_level: Mapped[str] = mapped_column(String(16), nullable=False, default="UNTRUSTED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_metadata: Mapped[dict] = mapped_column("metadata", JSON, nullable=False)


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    risk_flags: Mapped[list] = mapped_column(JSON, nullable=False)
    missing_information: Mapped[list] = mapped_column(JSON, nullable=False)
    follow_up_questions: Mapped[list] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source_references: Mapped[list] = mapped_column(JSON, nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[RecommendationStatus] = mapped_column(_enum(RecommendationStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), nullable=False, index=True)
    recommendation_id: Mapped[str] = mapped_column(ForeignKey("ai_recommendations.id"), nullable=False)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    edited_payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(40), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column("timestamp", DateTime(timezone=True), nullable=False)
    details: Mapped[dict] = mapped_column("metadata", JSON, nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(64))


class AIRun(Base):
    """Observability row. Prompts and document bodies are not stored here."""

    __tablename__ = "ai_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    submission_id: Mapped[str | None] = mapped_column(ForeignKey("submissions.id"), index=True)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    retrieved_document_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    tool_calls: Mapped[list] = mapped_column(JSON, nullable=False)
    success: Mapped[bool] = mapped_column(nullable=False)
    token_usage: Mapped[dict | None] = mapped_column(JSON)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
