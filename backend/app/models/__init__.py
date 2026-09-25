"""SQLAlchemy tables. Persistence shape only; not returned from the API."""

from app.models.base import Base
from app.models.tables import (
    AIRecommendation,
    AIRun,
    AuditEvent,
    Claim,
    Company,
    Document,
    DocumentChunk,
    Review,
    Submission,
    User,
)

__all__ = [
    "AIRecommendation",
    "AIRun",
    "AuditEvent",
    "Base",
    "Claim",
    "Company",
    "Document",
    "DocumentChunk",
    "Review",
    "Submission",
    "User",
]
