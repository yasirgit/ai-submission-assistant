"""Roles, submission lifecycle, and the vocabulary of a draft analysis."""

from enum import StrEnum


class Role(StrEnum):
    UNDERWRITER = "UNDERWRITER"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"


class SubmissionStatus(StrEnum):
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RecommendationStatus(StrEnum):
    DRAFT = "DRAFT"
    ACCEPTED = "ACCEPTED"
    EDITED = "EDITED"
    REJECTED = "REJECTED"


class ReviewAction(StrEnum):
    ACCEPT = "ACCEPT"
    EDIT = "EDIT"
    REJECT = "REJECT"


class DocumentType(StrEnum):
    GUIDELINE = "GUIDELINE"
    SUBMISSION = "SUBMISSION"
    CLAIM = "CLAIM"


class RiskFlagType(StrEnum):
    REVENUE = "REVENUE"
    INDUSTRY = "INDUSTRY"
    GEOGRAPHY = "GEOGRAPHY"
    EMPLOYEES = "EMPLOYEES"
    CLAIMS = "CLAIMS"
    COVERAGE = "COVERAGE"
    CONFLICTING_GUIDANCE = "CONFLICTING_GUIDANCE"
    OTHER = "OTHER"


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
