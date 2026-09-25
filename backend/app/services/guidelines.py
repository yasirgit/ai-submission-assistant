"""Guideline search for the API. Ranking for the model arrives with retrieval."""

from sqlalchemy.orm import Session

from app.repositories.guidelines import GuidelineRepository


class GuidelineService:
    def __init__(self, session: Session) -> None:
        self._guidelines = GuidelineRepository(session)

    def search(self, query: str, limit: int):
        hits = []
        for chunk, document in self._guidelines.search(query, limit):
            hits.append(
                {
                    "document_id": document.id,
                    "document_title": document.title,
                    "chunk_id": chunk.id,
                    "excerpt": _excerpt(chunk.content),
                }
            )
        return hits


def _excerpt(content: str, limit: int = 180) -> str:
    collapsed = " ".join(content.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1] + "…"
