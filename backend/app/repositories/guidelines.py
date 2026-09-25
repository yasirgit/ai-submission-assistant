"""Published guideline chunks. Submission narratives are never included."""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.domain.enums import DocumentType
from app.models.tables import Document, DocumentChunk


class GuidelineRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def search(self, query: str, limit: int) -> list[tuple[DocumentChunk, Document]]:
        stmt = (
            select(DocumentChunk, Document)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.doc_type == DocumentType.GUIDELINE)
        )
        cleaned = query.strip()
        if cleaned:
            pattern = f"%{_escape_like(cleaned)}%"
            stmt = stmt.where(
                or_(
                    DocumentChunk.content.ilike(pattern, escape="\\"),
                    Document.title.ilike(pattern, escape="\\"),
                )
            )
        stmt = stmt.order_by(Document.id, DocumentChunk.chunk_index).limit(limit)
        return list(self._session.execute(stmt).all())


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
