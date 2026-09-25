"""Load guideline chunks for ranking. Submission notes are not included."""

from sqlalchemy.orm import Session

from app.rag.types import RetrievedChunk
from app.repositories.guidelines import GuidelineRepository

_LOAD_LIMIT = 200


def load_guideline_chunks(session: Session) -> list[RetrievedChunk]:
    rows = GuidelineRepository(session).search("", _LOAD_LIMIT)
    return [
        RetrievedChunk(
            document_id=document.id,
            document_title=document.title,
            chunk_id=chunk.id,
            content=chunk.content,
            metadata=dict(chunk.chunk_metadata),
        )
        for chunk, document in rows
    ]
