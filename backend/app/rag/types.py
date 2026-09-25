"""Retrieval port. Callers depend on this, not on a vector database."""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class RetrievalQuery:
    text: str
    industry: str | None
    countries: tuple[str, ...]
    product: str | None
    k: int = 5


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: str
    document_title: str
    chunk_id: str
    content: str
    metadata: dict = field(default_factory=dict)
    score: float = 0.0


class DocumentRetriever(Protocol):
    def retrieve(self, query: RetrievalQuery) -> list[RetrievedChunk]:
        """Return at most query.k chunks. Never the whole corpus."""
